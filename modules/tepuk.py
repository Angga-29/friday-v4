# ==============================================================
# modules/tepuk.py — Project Friday | Deteksi Double Clap
# Versi : 1.0.0
# Cara kerja:
#   1. Buka stream PyAudio → baca audio terus-menerus
#   2. Hitung RMS per chunk → deteksi spike (tepukan)
#   3. Dua spike berturut dalam 0.1-0.7 detik = double clap
#   4. Panggil callback (sama seperti wake word)
# ==============================================================

import math
import struct
import threading
import time

# ── Parameter (bisa ditambah ke config.py jika perlu di-tune) ──
RATE                = 16000   # sample rate (Hz)
CHUNK               = 512     # ukuran buffer kecil = respons cepat
THRESHOLD           = 0.28    # ambang batas RMS untuk double clap (0.0-1.0)
THRESHOLD_INTERRUPT = 0.35    # ambang lebih tinggi untuk barge-in (hindari false trigger)
MIN_GAP             = 0.08    # jarak minimum antar tepuk (detik)
MAX_GAP             = 0.70    # jarak maksimum untuk dianggap double clap (detik)
COOLDOWN            = 3.0     # jeda setelah berhasil deteksi wake (detik)
COOLDOWN_INTERRUPT  = 1.5     # jeda setelah berhasil interrupt
MAX_RETRY           = 8       # maksimum percobaan buka mic saat gagal


class DetektorTepuk:
    """
    Detektor tepukan yang berjalan di background thread.

    Mode:
    - _sedang_bicara tidak aktif → deteksi double clap → callback wake word
    - _sedang_bicara aktif       → deteksi single clap  → callback_interrupt (barge-in)
    """

    def __init__(self, callback, sedang_bicara=None, callback_interrupt=None):
        """
        Args:
            callback           : Dipanggil saat double clap (wake word)
            sedang_bicara      : threading.Event dari suara.py
            callback_interrupt : Dipanggil saat single clap selama TTS aktif (barge-in)
        """
        self._cb            = callback
        self._cb_interrupt  = callback_interrupt
        self._sedang_bicara = sedang_bicara
        self._aktif         = False
        self._thread        = None
        self._last_clap     = 0.0
        self._last_trigger  = 0.0
        self._last_interrupt = 0.0

    # ── Public ────────────────────────────────────────────────

    def mulai(self):
        if self._aktif:
            return
        self._aktif = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="TepukDetector"
        )
        self._thread.start()

    def hentikan(self):
        self._aktif = False

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _rms(data: bytes) -> float:
        """Hitung RMS (root mean square) dari raw PCM bytes → 0.0–1.0."""
        n = len(data) // 2
        if n == 0:
            return 0.0
        shorts = struct.unpack(f'<{n}h', data)
        mean_sq = sum(s * s for s in shorts) / n
        return math.sqrt(mean_sq) / 32768.0

    # ── Loop utama ────────────────────────────────────────────

    def _loop(self):
        try:
            import pyaudio
        except ImportError:
            from modules.tampilan import tampilkan_status
            tampilkan_status("pyaudio tidak ada — double clap dinonaktifkan.", "peringatan")
            return

        from modules.tampilan import tampilkan_status

        pa     = None
        stream = None
        retry  = 0

        while self._aktif:
            try:
                # ── Buka mic jika belum ──
                if pa is None:
                    pa = pyaudio.PyAudio()
                if stream is None:
                    stream = pa.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                    )
                    retry = 0
                    tampilkan_status(
                        "👏 Double clap aktif. Tepuk 2x untuk memanggil Friday.", "sukses"
                    )

                data = stream.read(CHUNK, exception_on_overflow=False)
                amp  = self._rms(data)
                now  = time.time()

                tts_aktif = self._sedang_bicara and self._sedang_bicara.is_set()

                # ── MODE BARGE-IN: Friday sedang bicara ──────────────
                if tts_aktif:
                    if self._cb_interrupt and amp >= THRESHOLD_INTERRUPT:
                        if now - self._last_interrupt > COOLDOWN_INTERRUPT:
                            self._last_interrupt = now
                            tampilkan_status(
                                "👏 Tepukan! Menghentikan Friday...", "deteksi"
                            )
                            try:
                                self._cb_interrupt()
                            except Exception:
                                pass
                    time.sleep(0.05)
                    continue

                # ── MODE NORMAL: deteksi double clap ─────────────────
                if amp < THRESHOLD:
                    continue

                if now - self._last_trigger < COOLDOWN:
                    continue

                gap = now - self._last_clap
                if self._last_clap > 0 and MIN_GAP < gap < MAX_GAP:
                    # ✅ DOUBLE CLAP → aktifkan Friday
                    self._last_trigger = now
                    self._last_clap    = 0.0
                    tampilkan_status("👏 Double clap! Mengaktifkan Friday...", "deteksi")
                    try:
                        self._cb()
                    except Exception:
                        pass
                else:
                    self._last_clap = now

                time.sleep(0.06)

            except OSError as e:
                # Mic sedang dipakai → retry dengan backoff
                if stream:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except Exception:
                        pass
                    stream = None
                if pa:
                    try:
                        pa.terminate()
                    except Exception:
                        pass
                    pa = None

                retry += 1
                if retry > MAX_RETRY:
                    tampilkan_status(
                        "Double clap: mic tidak bisa dibuka, dinonaktifkan.", "peringatan"
                    )
                    return

                jeda = min(2 ** retry, 30)
                tampilkan_status(
                    f"Double clap: mic sibuk, retry {retry}/{MAX_RETRY} dalam {jeda}s...",
                    "peringatan"
                )
                time.sleep(jeda)

            except Exception as e:
                from modules.tampilan import tampilkan_status
                tampilkan_status(f"Double clap error: {e}", "peringatan")
                time.sleep(1)

        # ── Cleanup ──
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        if pa:
            try:
                pa.terminate()
            except Exception:
                pass
