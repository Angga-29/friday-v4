# modules/pendengar.py — Project Friday | Modul Pengenalan Suara
# Versi 2.3 — Fix echo: deteksi otomatis + buffer + threshold tinggi
# ==============================================================

import time
import speech_recognition as sr
from modules.tampilan import (
    tampilkan_status,
    tampilkan_mendengarkan,
    tampilkan_user_bicara,
)

# --- Konfigurasi ---
TIMEOUT_TUNGGU        = 7     # Detik menunggu suara mulai
BATAS_DURASI          = 12    # Durasi maksimal bicara (detik)
JEDA_KALIMAT          = 2.0   # Jeda sebelum dianggap selesai bicara
BAHASA                = "id-ID"
BUFFER_SETELAH_TTS    = 3.0   # Jeda setelah Friday selesai bicara (3s)
MAX_RETRY             = 2     # Coba dengar ulang jika gagal
TIMEOUT_TUNGGU_BICARA = 15    # Maks tunggu Friday selesai bicara
ECHO_THRESHOLD        = 0.5   # 50% kata sama = dianggap echo


def _hitung_kemiripan(a: str, b: str) -> float:
    """
    Hitung rasio kata yang sama antara dua teks.
    Return 0.0-1.0 (0 = beda total, 1 = identik).
    """
    if not a or not b:
        return 0.0
    kata_a = set(a.lower().split())
    kata_b = set(b.lower().split())
    if not kata_a or not kata_b:
        return 0.0
    sama = kata_a & kata_b
    # Bandingkan dengan teks yang lebih pendek (capture biasanya lebih pendek dari TTS)
    return len(sama) / min(len(kata_a), len(kata_b))


def _adalah_echo(teks_user: str) -> bool:
    """
    Cek apakah teks dari mikrofon adalah echo dari suara Friday sendiri.
    Bandingkan dengan teks terakhir yang Friday ucapkan.
    """
    try:
        from modules.suara import teks_terakhir_diucapkan
        teks_friday = teks_terakhir_diucapkan()
        if not teks_friday:
            return False
        kemiripan = _hitung_kemiripan(teks_user, teks_friday)
        return kemiripan >= ECHO_THRESHOLD
    except ImportError:
        return False


def dengarkan(setelah_tts: bool = True) -> str | None:
    """
    Mendengarkan input suara dari mikrofon dan mengubahnya ke teks.
    Otomatis abaikan echo dari suara Friday sendiri.
    """
    # ── Anti-echo lapis 1: tunggu flag sedang_bicara clear ──────
    try:
        from modules.suara import sedang_bicara
        if sedang_bicara():
            tampilkan_status("Menunggu Friday selesai bicara...", "info")
            batas = time.time() + TIMEOUT_TUNGGU_BICARA
            while sedang_bicara() and time.time() < batas:
                time.sleep(0.1)
    except ImportError:
        pass

    # ── Anti-echo lapis 2: buffer untuk gema ruangan hilang ─────
    if setelah_tts:
        time.sleep(BUFFER_SETELAH_TTS)

    recognizer = sr.Recognizer()

    for percobaan in range(1, MAX_RETRY + 1):
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                recognizer.pause_threshold          = JEDA_KALIMAT
                recognizer.dynamic_energy_threshold = True

                tampilkan_mendengarkan()

                try:
                    audio = recognizer.listen(
                        source,
                        timeout=TIMEOUT_TUNGGU,
                        phrase_time_limit=BATAS_DURASI
                    )
                except sr.WaitTimeoutError:
                    if percobaan < MAX_RETRY:
                        tampilkan_status(
                            f"Tidak ada suara. Percobaan {percobaan}/{MAX_RETRY}...",
                            "peringatan"
                        )
                        continue
                    tampilkan_status("Tidak ada suara terdeteksi.", "peringatan")
                    return None

        except OSError:
            tampilkan_status(
                "Mikrofon tidak tersedia. Pastikan izin mikrofon Termux aktif.",
                "error"
            )
            return None

        # Transkripsi audio ke teks
        try:
            tampilkan_status("Memproses suara...", "info")
            teks = recognizer.recognize_google(audio, language=BAHASA)

            # ── Anti-echo lapis 3: deteksi kemiripan dengan teks Friday ──
            if _adalah_echo(teks):
                tampilkan_status(
                    f"Mendengar suara sendiri (echo): '{teks}' — diabaikan.",
                    "peringatan"
                )
                if percobaan < MAX_RETRY:
                    time.sleep(0.5)
                    continue
                return None

            tampilkan_user_bicara(teks)
            return teks

        except sr.UnknownValueError:
            if percobaan < MAX_RETRY:
                tampilkan_status(
                    f"Suara kurang jelas. Percobaan {percobaan}/{MAX_RETRY}...",
                    "peringatan"
                )
                time.sleep(0.5)
                continue
            tampilkan_status(
                "Suara tidak dapat dikenali. Coba bicara lebih dekat & jelas.",
                "peringatan"
            )
            return None

        except sr.RequestError as e:
            tampilkan_status(
                f"Gagal menghubungi Google Speech API: {e}", "error"
            )
            return None

        except Exception as e:
            tampilkan_status(f"Error pengenalan suara: {e}", "error")
            return None

    return None
