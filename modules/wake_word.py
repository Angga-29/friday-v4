# ==============================================================
# modules/wake_word.py — Project Friday | Wake Word Detector
# Versi: 3.0.2 — Fix FLAC error handling, anti-spam log
# Mendeteksi panggilan "Hai Friday" / "Hey Friday" / "Friday"
# ==============================================================
"""
Modul ini berjalan dalam THREAD TERPISAH dari loop utama.
Selalu mendengarkan di background — saat mendengar wake word,
dia akan trigger callback ke main untuk masuk ke mode dengarkan aktif.

CATATAN: Membutuhkan package 'flac' di Termux:
  pkg install flac
"""

import threading
import time
import speech_recognition as sr
from modules.tampilan import tampilkan_status
from modules.audio_lock import PYAUDIO_INIT_LOCK

# --- Wake word yang dikenal ---
WAKE_WORDS = [
    "hai friday",   "hey friday",   "halo friday",
    "ok friday",    "oke friday",   "friday",
    "ai friday",    "hi friday"
]

# Konfigurasi listener background
DURASI_FRAME   = 4     # detik per chunk listening
JEDA_KALIBRASI = 0.5

# Anti-spam: log error FLAC maksimal 1x per sesi
_flac_error_sudah_dilog = False


class WakeWordDetector:
    """
    Detector berjalan di thread terpisah.
    Saat wake word terdeteksi → memanggil callback yang Anda set.
    """

    def __init__(self, callback_terdeteksi=None):
        self.callback   = callback_terdeteksi
        self.aktif      = False
        self.thread     = None
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6

    def _loop_listener(self):
        """Loop background yang terus mendengarkan."""
        global _flac_error_sudah_dilog

        try:
            with PYAUDIO_INIT_LOCK:
                mic = sr.Microphone()
            with PYAUDIO_INIT_LOCK:
                source = mic.__enter__()
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=JEDA_KALIBRASI)
                tampilkan_status("Wake word listener aktif. Panggil 'Hai Friday'.", "info")

                while self.aktif:
                    # ── Anti-echo: skip saat Friday sedang bicara ──
                    try:
                        from modules.suara import sedang_bicara
                        if sedang_bicara():
                            time.sleep(0.2)
                            continue
                    except ImportError:
                        pass

                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=DURASI_FRAME,
                            phrase_time_limit=DURASI_FRAME
                        )
                        try:
                            teks = self.recognizer.recognize_google(
                                audio, language='id-ID'
                            ).lower()

                            if any(w in teks for w in WAKE_WORDS):
                                tampilkan_status(
                                    f"Wake word terdeteksi: '{teks}'", "sukses"
                                )
                                if self.callback:
                                    self.callback(teks)

                        except sr.UnknownValueError:
                            pass  # Suara tidak jelas, normal — lanjut listen
                        except sr.RequestError as e:
                            tampilkan_status(f"Speech API error: {e}", "peringatan")
                            time.sleep(2)

                    except sr.WaitTimeoutError:
                        continue

                    except Exception as e:
                        err_str = str(e)
                        # Error FLAC: log hanya sekali, lalu tunjukkan solusi
                        if "FLAC" in err_str or "flac" in err_str:
                            if not _flac_error_sudah_dilog:
                                _flac_error_sudah_dilog = True
                                tampilkan_status(
                                    "Wake word: FLAC tidak ditemukan di sistem.", "peringatan"
                                )
                                tampilkan_status(
                                    "Solusi → jalankan di Termux: pkg install flac", "info"
                                )
                                tampilkan_status(
                                    "Wake word dinonaktifkan. Restart Friday setelah install flac.",
                                    "peringatan"
                                )
                            # Berhenti loop agar tidak spam error
                            self.aktif = False
                            return
                        else:
                            tampilkan_status(f"Wake word error: {e}", "peringatan")
                            time.sleep(1)
            finally:
                mic.__exit__(None, None, None)

        except OSError:
            tampilkan_status(
                "Mikrofon tidak tersedia untuk wake word. "
                "Pastikan Termux:API terinstall dan izin mikrofon aktif.",
                "peringatan"
            )

    def mulai(self):
        if self.aktif:
            return
        self.aktif = True
        self.thread = threading.Thread(target=self._loop_listener, daemon=True)
        self.thread.start()

    def hentikan(self):
        self.aktif = False
        if self.thread:
            self.thread.join(timeout=2)
