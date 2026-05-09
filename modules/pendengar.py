# modules/pendengar.py — Project Friday | Modul Pengenalan Suara
# Versi 2.2 — Fix echo: tunggu flag sedang_bicara sebelum rekam
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
BUFFER_SETELAH_TTS    = 2.5   # Jeda setelah Friday selesai bicara (naik dari 1.2)
MAX_RETRY             = 2     # Coba dengar ulang jika gagal
TIMEOUT_TUNGGU_BICARA = 15    # Maks tunggu Friday selesai bicara (detik)


def dengarkan(setelah_tts: bool = True) -> str | None:
    """
    Mendengarkan input suara dari mikrofon dan mengubahnya ke teks.

    Args:
        setelah_tts: Jika True, tambahkan buffer waktu agar TTS
                     selesai dulu sebelum mikrofon aktif.

    Returns:
        Teks hasil transkripsi, atau None jika tidak ada / gagal.
    """
    # ── Anti-echo: tunggu Friday selesai bicara dulu ──────────
    # Import di dalam fungsi untuk menghindari circular import
    try:
        from modules.suara import sedang_bicara
        if sedang_bicara():
            tampilkan_status("Menunggu Friday selesai bicara...", "info")
            batas = time.time() + TIMEOUT_TUNGGU_BICARA
            while sedang_bicara() and time.time() < batas:
                time.sleep(0.1)

    except ImportError:
        pass

    # Buffer tambahan setelah audio selesai agar gema di ruangan hilang
    if setelah_tts:
        time.sleep(BUFFER_SETELAH_TTS)

    recognizer = sr.Recognizer()

    # ✅ FIX #2: Coba dengarkan hingga MAX_RETRY kali
    for percobaan in range(1, MAX_RETRY + 1):
        try:
            with sr.Microphone() as source:
                # Kalibrasi noise — durasi lebih pendek agar tidak lama
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
