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
RATE       = 16000    # sample rate (Hz)
CHUNK      = 512      # ukuran buffer kecil = respons cepat
THRESHOLD  = 0.28     # ambang batas RMS (0.0-1.0). Naikan jika terlalu sensitif
MIN_GAP    = 0.08     # jarak minimum antar tepuk (detik)
MAX_GAP    = 0.70     # jarak maksimum untuk dianggap double clap (detik)
COOLDOWN   = 3.0      # jeda setelah berhasil deteksi (detik)
MAX_RETRY  = 8        # maksimum percobaan buka mic saat gagal


class DetektorTepuk:
    """
    Detektor double clap yang berjalan di background thread.
    Tidak crash jika mic sedang dipakai — retry otomatis.
    """

    def __init__(self, callback, sedang_bicara=None):
        """
        Args:
            callback       : Fungsi yang dipanggil saat double clap terdeteksi
            sedang_bicara  : threading.Event — skip deteksi saat Friday bicara
        """
        self._cb            = callback
        self._sedang_bicara = sedang_bicara
        self._aktif         = False
        self._thread        = None
        self._last_clap     = 0.0   # waktu tepukan terakhir
        self._last_trigger  = 0.0   # waktu terakhir callback dipanggil

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

                # ── Skip saat Friday sedang bicara (anti-echo) ──
                if self._sedang_bicara and self._sedang_bicara.is_set():
                    time.sleep(0.05)
                    continue

                data = stream.read(CHUNK, exception_on_overflow=False)
                amp  = self._rms(data)

                if amp < THRESHOLD:
                    continue   # hening / suara biasa

                now = time.time()

                # Masih dalam cooldown setelah deteksi sebelumnya
                if now - self._last_trigger < COOLDOWN:
                    continue

                gap = now - self._last_clap
                if self._last_clap > 0 and MIN_GAP < gap < MAX_GAP:
                    # ✅ DOUBLE CLAP terdeteksi!
                    self._last_trigger = now
                    self._last_clap    = 0.0
                    tampilkan_status(
                        "👏 Double clap! Mengaktifkan Friday...", "deteksi"
                    )
                    try:
                        self._cb()
                    except Exception:
                        pass
                else:
                    # Tepukan pertama — catat waktu
                    self._last_clap = now

                # Debounce: abaikan gema langsung setelah tepukan
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
