# ==============================================================
# modules/gemini_ai.py — Project Friday | Gemini AI v3.0
# Versi : 3.0.0 — Integrasi dengan memori permanen
# ==============================================================

import google.generativeai as genai
from modules.tampilan import tampilkan_status, tampilkan_memproses

MODEL_NAME = "gemini-2.5-flash"
MAX_TOKENS = 500


class GeminiAI:
    def __init__(self, api_key: str, system_prompt: str, memori=None):
        self._terhubung    = False
        self.model         = None
        self.chat          = None
        self.system_prompt = system_prompt
        self.memori        = memori   # Optional: MemoriFriday instance

        try:
            genai.configure(api_key=api_key)
            # Inject memori ke system prompt jika tersedia
            full_system = system_prompt
            if memori:
                konteks_memori = self._bangun_konteks_memori()
                if konteks_memori:
                    full_system = system_prompt + "\n\n" + konteks_memori

            self.model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                system_instruction=full_system,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=MAX_TOKENS,
                    temperature=0.75,
                    top_p=0.95,
                )
            )
            self.chat = self.model.start_chat(history=[])
            self._terhubung = True
            tampilkan_status(f"Gemini AI ({MODEL_NAME}) berhasil dimuat.", "sukses")

        except Exception as e:
            tampilkan_status(f"Gagal init Gemini AI: {e}", "error")

    def _bangun_konteks_memori(self) -> str:
        """Bangun konteks dari memori untuk diberikan ke Gemini."""
        if not self.memori:
            return ""

        bagian = []

        # Preferensi pengguna
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

        # Percakapan terakhir (5 terakhir)
        riwayat = self.memori.ambil_percakapan_terakhir(5)
        if riwayat:
            bagian.append("\n[PERCAKAPAN TERAKHIR — UNTUK KONTEKS]")
            for user, friday in riwayat:
                bagian.append(f"User : {user}")
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
            response = self.chat.send_message(perintah)
            return self._bersihkan(response.text)
        except Exception as e:
            tampilkan_status(f"Error Gemini: {e}", "error")
            return "Maaf, saya sedang mengalami gangguan."

    def tanya_dengan_web(self, pertanyaan: str, konteks_web: str) -> str:
        if not self._terhubung:
            return "Maaf, koneksi ke AI bermasalah."
        tampilkan_memproses()
        try:
            response = self.chat.send_message(konteks_web)
            return self._bersihkan(response.text)
        except Exception as e:
            tampilkan_status(f"Error Gemini (web): {e}", "error")
            return "Maaf, gagal memproses hasil pencarian."

    def reset_sesi(self) -> None:
        if self.model:
            self.chat = self.model.start_chat(history=[])
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
