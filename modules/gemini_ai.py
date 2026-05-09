# ==============================================================
# modules/gemini_ai.py — Project Friday | Gemini AI v4.0
# Versi : 4.0.0 — Support Gemini 2.5 Flash + dual SDK fallback
# ==============================================================

from modules.tampilan import tampilkan_status, tampilkan_memproses

MODEL_UTAMA   = "gemini-2.5-flash"
MODEL_FALLBACK = "gemini-1.5-flash"
MAX_TOKENS    = 500

# Deteksi SDK yang tersedia: google-generativeai (lama) atau google-genai (baru)
_SDK_MODE = None
genai     = None

try:
    import google.generativeai as genai
    _SDK_MODE = "generativeai"
except ImportError:
    try:
        from google import genai as _g
        genai = _g
        _SDK_MODE = "genai"
    except ImportError:
        pass


class GeminiAI:
    def __init__(self, api_key: str, system_prompt: str, memori=None):
        self._terhubung    = False
        self.model         = None
        self.chat          = None
        self.system_prompt = system_prompt
        self.memori        = memori
        self._api_key      = api_key

        if _SDK_MODE is None:
            tampilkan_status(
                "google-generativeai tidak terinstall!\n"
                "Jalankan: pip install google-generativeai",
                "error"
            )
            return

        if _SDK_MODE == "generativeai":
            self._init_generativeai(api_key, system_prompt)
        else:
            self._init_genai(api_key, system_prompt)

    def _init_generativeai(self, api_key: str, system_prompt: str):
        """Inisialisasi dengan SDK google-generativeai (legacy)."""
        try:
            genai.configure(api_key=api_key)
            full_system = self._bangun_system_prompt(system_prompt)

            # Coba model utama (Gemini 2.5 Flash)
            self.model = self._buat_model_generativeai(full_system, MODEL_UTAMA)
            if self.model is None:
                tampilkan_status(
                    f"Gagal load {MODEL_UTAMA}, mencoba {MODEL_FALLBACK}...", "peringatan"
                )
                self.model = self._buat_model_generativeai(full_system, MODEL_FALLBACK)
            # Simpan nama model yang aktif untuk keperluan recovery
            self._active_model_name = MODEL_UTAMA if self.model else MODEL_FALLBACK

            if self.model:
                self.chat       = self.model.start_chat(history=[])
                self._terhubung = True
                tampilkan_status(
                    f"Gemini AI siap (SDK: generativeai).", "sukses"
                )
            else:
                tampilkan_status("Gagal inisialisasi Gemini AI.", "error")

        except Exception as e:
            tampilkan_status(f"Gagal init Gemini AI: {e}", "error")

    def _buat_model_generativeai(self, system_prompt: str, model_name: str):
        """Buat GenerativeModel — kompatibel semua versi google-generativeai."""
        # Konfigurasi dasar tanpa thinking_config agar kompatibel semua versi
        gen_config = {
            "max_output_tokens": MAX_TOKENS,
            "temperature"      : 0.75,
            "top_p"            : 0.95,
        }
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config=gen_config,
            )
            model.start_chat(history=[])
            tampilkan_status(f"Model {model_name} dimuat.", "sukses")
            return model
        except Exception as e:
            tampilkan_status(f"Gagal load {model_name}: {e}", "peringatan")
            return None

    def _init_genai(self, api_key: str, system_prompt: str):
        """Inisialisasi dengan SDK google-genai (baru)."""
        try:
            self._client    = genai.Client(api_key=api_key)
            self._model_name = MODEL_UTAMA
            full_system     = self._bangun_system_prompt(system_prompt)
            self._system    = full_system
            self._history   = []
            self._terhubung = True
            tampilkan_status("Gemini AI siap (SDK: google-genai).", "sukses")
        except Exception as e:
            tampilkan_status(f"Gagal init Gemini (genai SDK): {e}", "error")

    def _bangun_system_prompt(self, base: str) -> str:
        """Gabungkan system prompt dengan konteks memori."""
        if not self.memori:
            return base
        konteks = self._bangun_konteks_memori()
        return base + ("\n\n" + konteks if konteks else "")

    def _bangun_konteks_memori(self) -> str:
        if not self.memori:
            return ""
        bagian = []
        try:
            cur = self.memori.koneksi.cursor()
            cur.execute("SELECT kunci, nilai FROM preferensi LIMIT 10")
            prefs = cur.fetchall()
            if prefs:
                bagian.append("[YANG SAYA INGAT TENTANG PENGGUNA]")
                for k, v in prefs:
                    bagian.append(f"- {k}: {v}")
        except Exception:
            pass

        riwayat = self.memori.ambil_percakapan_terakhir(5)
        if riwayat:
            bagian.append("\n[PERCAKAPAN TERAKHIR — UNTUK KONTEKS]")
            for user, friday in riwayat:
                bagian.append(f"User  : {user}")
                bagian.append(f"Friday: {friday}")

        return "\n".join(bagian) if bagian else ""

    @property
    def terhubung(self) -> bool:
        return self._terhubung

    def _bersihkan(self, teks: str) -> str:
        teks = teks.replace("**", "").replace("*", "")
        teks = teks.replace("##", "").replace("#", "").replace("`", "")
        return teks.strip()

    def tanya(self, perintah: str) -> str:
        if not self._terhubung:
            return "Maaf, koneksi ke AI sedang bermasalah."
        tampilkan_memproses()
        try:
            if _SDK_MODE == "generativeai":
                response = self.chat.send_message(perintah)
                return self._bersihkan(response.text)
            else:
                from google.genai import types
                contents = self._history + [{"role": "user", "parts": [perintah]}]
                resp = self._client.models.generate_content(
                    model=self._model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=self._system,
                        max_output_tokens=MAX_TOKENS,
                        temperature=0.75,
                    ),
                )
                jawaban = self._bersihkan(resp.text)
                self._history.append({"role": "user",  "parts": [perintah]})
                self._history.append({"role": "model", "parts": [jawaban]})
                if len(self._history) > 20:
                    self._history = self._history[-20:]
                return jawaban
        except Exception as e:
            err = str(e)
            if "API_KEY" in err.upper() or "api key" in err.lower():
                return "API key Gemini tidak valid. Periksa config.py."
            if "quota" in err.lower() or "429" in err:
                return "Kuota Gemini habis. Coba lagi nanti."
            if "thinking" in err.lower():
                # Versi lama tidak support thinking — reinit model tanpa config tersebut
                tampilkan_status("Reinisialisasi model (thinking not supported)...", "peringatan")
                model_name = getattr(self, '_active_model_name', MODEL_UTAMA)
                full_system = self._bangun_system_prompt(self.system_prompt)
                self.model = self._buat_model_generativeai(full_system, model_name)
                if self.model:
                    self.chat = self.model.start_chat(history=[])
                    try:
                        response = self.chat.send_message(perintah)
                        return self._bersihkan(response.text)
                    except Exception:
                        pass
            tampilkan_status(f"Error Gemini: {err}", "error")
            return "Maaf, saya sedang mengalami gangguan."

    def tanya_dengan_web(self, pertanyaan: str, konteks_web: str) -> str:
        if not self._terhubung:
            return "Maaf, koneksi ke AI bermasalah."
        return self.tanya(konteks_web)

    def reset_sesi(self) -> None:
        if _SDK_MODE == "generativeai" and self.model:
            self.chat = self.model.start_chat(history=[])
        elif _SDK_MODE == "genai":
            self._history = []
        tampilkan_status("Sesi percakapan direset.", "info")

    def bangun_konteks(self, suara_user, waktu, cuaca, berita):
        berita_str = " | ".join(berita) if berita else "tidak tersedia"
        return (
            f"[KONTEKS REAL-TIME]\n"
            f"Waktu  : {waktu}\n"
            f"Cuaca  : {cuaca}\n"
            f"Berita : {berita_str}\n\n"
            f"[PERINTAH PENGGUNA]\n{suara_user}"
        )
