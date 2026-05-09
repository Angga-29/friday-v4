# ==============================================================
# modules/proaktif.py — Project Friday v4.0 | Mode Proaktif
# Terinspirasi dari OpenJarvis Persistent Autonomous Operators
# ==============================================================
"""
Friday bicara duluan dalam situasi terjadwal:

1. Morning Digest (07:00) — cuaca + berita utama + semangat pagi
2. Pengingat makan siang (12:00)
3. Pengingat makan malam (19:00)
4. Pengingat istirahat  (22:30)

Berjalan di thread terpisah dari main loop.
Lock non-blocking: jika TTS sedang dipakai, pengingat dilewati
agar tidak mengganggu percakapan aktif.
"""

import threading
import time
from datetime import datetime
from modules.tampilan import tampilkan_status

# Waktu pengingat (jam, menit)
WAKTU_MORNING_DIGEST = (7, 0)
WAKTU_MAKAN_SIANG    = (12, 0)
WAKTU_MAKAN_MALAM    = (19, 0)
WAKTU_TIDUR          = (22, 30)

COOLDOWN_PENGINGAT = 3600   # 1 jam — hindari spam

# Lock global — sinkronisasi TTS antar thread
_tts_lock = threading.Lock()


class ModeProaktif:
    """Pengelola pengingat terjadwal Friday — berjalan di background thread."""

    def __init__(
        self,
        callback_bicara,
        nama_pengguna: str = "Bos",
        callback_cuaca=None,
        callback_berita=None,
    ):
        self.callback_bicara = callback_bicara
        self.nama            = nama_pengguna
        self.callback_cuaca  = callback_cuaca   # Callable() -> str
        self.callback_berita = callback_berita  # Callable() -> list[str]
        self.aktif           = False
        self.thread          = None
        self.terakhir        = {}
        self.menit_terakhir  = -1

    def _bicara_aman(self, pesan: str):
        """TTS non-blocking — lewati jika thread lain sedang berbicara."""
        acquired = _tts_lock.acquire(blocking=False)
        if acquired:
            try:
                self.callback_bicara(pesan)
            finally:
                _tts_lock.release()
        else:
            tampilkan_status("TTS dipakai — pengingat dilewati.", "info")

    def _morning_digest(self):
        """
        Ringkasan pagi komprehensif — terinspirasi OpenJarvis Morning Digest Agent.
        Cuaca + berita utama + semangat → disampaikan satu per satu.
        """
        bagian = [f"Selamat pagi {self.nama}! Inilah ringkasan pagi Anda."]

        if self.callback_cuaca:
            try:
                cuaca = self.callback_cuaca()
                if cuaca:
                    bagian.append(cuaca)
            except Exception:
                pass

        if self.callback_berita:
            try:
                berita = self.callback_berita()
                if berita:
                    bagian.append(f"Berita hari ini: {berita[0]}")
            except Exception:
                pass

        bagian.append("Semangat menjalani hari. Saya siap membantu kapan saja!")

        for pesan in bagian:
            self._bicara_aman(pesan)
            time.sleep(0.8)

    def _cek_pengingat(self):
        sekarang = datetime.now()
        jam, menit = sekarang.hour, sekarang.minute

        if menit == self.menit_terakhir:
            return
        self.menit_terakhir = menit

        jadwal = [
            ("morning_digest", WAKTU_MORNING_DIGEST, None),
            ("makan_siang",    WAKTU_MAKAN_SIANG,
             f"{self.nama}, sudah jam dua belas siang. Waktunya makan siang."),
            ("makan_malam",    WAKTU_MAKAN_MALAM,
             f"{self.nama}, sudah jam tujuh malam. Waktunya makan malam."),
            ("tidur",          WAKTU_TIDUR,
             f"{self.nama}, sudah hampir jam sebelas. Saatnya beristirahat."),
        ]

        for kunci, (j, m), pesan in jadwal:
            if jam == j and menit == m:
                if time.time() - self.terakhir.get(kunci, 0) > COOLDOWN_PENGINGAT:
                    tampilkan_status(f"Proaktif: {kunci}", "ai")
                    if kunci == "morning_digest":
                        threading.Thread(
                            target=self._morning_digest, daemon=True
                        ).start()
                    else:
                        self._bicara_aman(pesan)
                    self.terakhir[kunci] = time.time()

    def _loop(self):
        while self.aktif:
            try:
                self._cek_pengingat()
            except Exception as e:
                tampilkan_status(f"Error proaktif: {e}", "peringatan")
            time.sleep(30)

    def mulai(self):
        if self.aktif:
            return
        self.aktif = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        tampilkan_status("Mode proaktif aktif (morning digest + pengingat jadwal).", "sukses")

    def hentikan(self):
        self.aktif = False
        if self.thread:
            self.thread.join(timeout=2)
