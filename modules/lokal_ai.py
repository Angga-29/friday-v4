# ==============================================================
# modules/lokal_ai.py — Project Friday | Ollama Local AI
# Versi : 1.0.0 — Fallback offline via Ollama REST API
# ==============================================================
"""
Dipakai saat Claude tidak bisa diakses (offline / quota habis).
Menghubungi Ollama server lokal di port 11434.

Model yang direkomendasikan untuk desktop dengan GPU (mis. RTX 5050, ~8GB VRAM):
  qwen2.5:7b    — ~4.7 GB (Q4), bahasa Indonesia bagus, seimbang (default)
  llama3.1:8b   — ~4.9 GB (Q4), alternatif kuat, konteks panjang
  mistral:7b    — ~4.1 GB (Q4), cepat, cocok untuk VRAM lebih terbatas

Install Ollama di Windows:
  Download installer dari https://ollama.com/download/windows
  ollama serve             ← jalankan server (biasanya auto-start sebagai service)
  ollama pull qwen2.5:7b   ← download model (~4.7 GB)

Setelah itu Friday otomatis pakai Ollama saat offline.
"""

import json
import socket
import requests
from modules.tampilan import tampilkan_status

TIMEOUT_CONNECT  = 3    # detik — cek apakah Ollama jalan
TIMEOUT_GENERATE = 180  # detik — tunggu response (model lokal lambat)


class LokalAI:
    """
    Wrapper Ollama dengan interface sama seperti ClaudeAI:
      - tanya(perintah)        → str
      - tanya_stream(perintah) → generator[str]
      - bangun_konteks(...)    → str
      - reset_sesi()
      - terhubung              → bool
    """

    def __init__(self, host: str, model: str, system_prompt: str):
        self.host          = host.rstrip("/")
        self.model         = model
        self.system_prompt = system_prompt
        self._history      = []   # [{role, content}, ...]
        self._terhubung    = False
        self._cek_dan_init()

    # ----------------------------------------------------------
    # INIT & CEK
    # ----------------------------------------------------------
    def _cek_dan_init(self):
        """Cek apakah Ollama server jalan dan model tersedia."""
        if not self._ping_server():
            tampilkan_status(
                f"Ollama tidak terdeteksi di {self.host} — mode offline tidak aktif.",
                "peringatan"
            )
            return

        # Cek apakah model sudah di-pull
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=TIMEOUT_CONNECT)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if any(self.model.split(":")[0] in m for m in models):
                    self._terhubung = True
                    tampilkan_status(
                        f"Ollama siap: model {self.model} tersedia.", "sukses"
                    )
                else:
                    tampilkan_status(
                        f"Ollama jalan tapi model '{self.model}' belum di-pull.\n"
                        f"Jalankan: ollama pull {self.model}",
                        "peringatan"
                    )
        except Exception as e:
            tampilkan_status(f"Ollama cek model gagal: {e}", "peringatan")

    def _ping_server(self) -> bool:
        """Cek port Ollama dengan socket (cepat, tanpa HTTP overhead)."""
        try:
            host = self.host.replace("http://", "").replace("https://", "")
            ip, port = host.split(":") if ":" in host else (host, "11434")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT_CONNECT)
            hasil = sock.connect_ex((ip, int(port)))
            sock.close()
            return hasil == 0
        except Exception:
            return False

    @property
    def terhubung(self) -> bool:
        return self._terhubung

    # ----------------------------------------------------------
    # HELPER INTERNAL
    # ----------------------------------------------------------
    def _buat_messages(self, perintah: str) -> list:
        """Bangun daftar messages untuk Ollama /api/chat."""
        msgs = [{"role": "system", "content": self.system_prompt}]
        msgs.extend(self._history[-10:])   # maks 5 pasang terakhir
        msgs.append({"role": "user", "content": perintah})
        return msgs

    def _bersihkan(self, teks: str) -> str:
        teks = teks.replace("**", "").replace("*", "")
        teks = teks.replace("##", "").replace("#", "").replace("`", "")
        return teks.strip()

    def _simpan_history(self, perintah: str, jawaban: str):
        self._history.append({"role": "user",      "content": perintah})
        self._history.append({"role": "assistant", "content": jawaban})
        if len(self._history) > 20:
            self._history = self._history[-20:]

    # ----------------------------------------------------------
    # TANYA — blocking, return string
    # ----------------------------------------------------------
    def tanya(self, perintah: str) -> str:
        if not self._terhubung:
            return "Mode offline tidak tersedia — Ollama belum terpasang."
        try:
            payload = {
                "model"   : self.model,
                "messages": self._buat_messages(perintah),
                "stream"  : False,
                "options" : {
                    "temperature": 0.75,
                    "num_predict": 300,   # maks token output
                },
            }
            r = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=TIMEOUT_GENERATE,
            )
            r.raise_for_status()
            jawaban = self._bersihkan(
                r.json().get("message", {}).get("content", "")
            )
            self._simpan_history(perintah, jawaban)
            return jawaban or "Maaf, tidak ada jawaban dari model lokal."
        except requests.exceptions.Timeout:
            return "Model lokal timeout — mungkin masih loading, coba lagi."
        except Exception as e:
            tampilkan_status(f"Ollama error: {e}", "error")
            return "Maaf, model lokal mengalami gangguan."

    # ----------------------------------------------------------
    # TANYA STREAM — generator, yield per-chunk
    # ----------------------------------------------------------
    def tanya_stream(self, perintah: str):
        """
        Generator: yield potongan teks saat Ollama streaming.
        Kompatibel dengan mulai_bubble_stream() / stream_chunk() di tampilan.py.
        """
        if not self._terhubung:
            yield "Mode offline tidak tersedia — Ollama belum terpasang."
            return

        teks_total = []
        try:
            payload = {
                "model"   : self.model,
                "messages": self._buat_messages(perintah),
                "stream"  : True,
                "options" : {
                    "temperature": 0.75,
                    "num_predict": 300,
                },
            }
            with requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=TIMEOUT_GENERATE,
                stream=True,
            ) as r:
                r.raise_for_status()
                for baris in r.iter_lines():
                    if not baris:
                        continue
                    try:
                        data   = json.loads(baris)
                        bagian = data.get("message", {}).get("content", "")
                        if bagian:
                            bagian = self._bersihkan(bagian)
                            teks_total.append(bagian)
                            yield bagian
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.Timeout:
            yield " [timeout — model masih loading]"
        except Exception as e:
            tampilkan_status(f"Ollama stream error: {e}", "error")
            yield "Maaf, model lokal mengalami gangguan."
        finally:
            teks_penuh = "".join(teks_total).strip()
            if teks_penuh:
                self._simpan_history(perintah, teks_penuh)

    # ----------------------------------------------------------
    # BANGUN KONTEKS — sama dengan ClaudeAI
    # ----------------------------------------------------------
    def bangun_konteks(self, suara_user: str, waktu: str,
                       cuaca: str, berita: list) -> str:
        if berita:
            judul_list = []
            for b in berita:
                if isinstance(b, dict):
                    sumber = b.get("sumber", "").strip()
                    judul  = b.get("judul", "").strip()
                    judul_list.append(f"{sumber}: {judul}" if sumber else judul)
                else:
                    judul_list.append(str(b))
            berita_str = " | ".join(judul_list[:3])   # batasi 3 untuk hemat token
        else:
            berita_str = "tidak tersedia"

        return (
            f"[KONTEKS]\n"
            f"Waktu  : {waktu}\n"
            f"Cuaca  : {cuaca}\n"
            f"Berita : {berita_str}\n\n"
            f"[PERTANYAAN]\n{suara_user}"
        )

    # ----------------------------------------------------------
    # RESET SESI
    # ----------------------------------------------------------
    def reset_sesi(self):
        self._history = []
        tampilkan_status("Sesi Ollama direset.", "info")

    # ----------------------------------------------------------
    # CEK ULANG (dipanggil periodik jika awalnya offline)
    # ----------------------------------------------------------
    def cek_ulang(self):
        """Coba koneksi ulang ke Ollama — berguna setelah Ollama baru distart."""
        if not self._terhubung:
            self._cek_dan_init()
        return self._terhubung
