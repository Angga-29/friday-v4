# ==============================================================
# skills/pengingat.py — Skill Timer & Pengingat
# ==============================================================
import threading
import re
from typing import Optional

NAMA = "Timer & Pengingat"
PRIORITAS = 10
TRIGGER_WORDS = [
    "set timer", "timer", "hitung mundur",
    "ingatkan saya", "ingatkan aku", "pengingat",
    "set alarm", "kasih tahu saya dalam", "beritahu saya dalam",
]

_timers_aktif: list = []


def _format_durasi(total_detik: int) -> str:
    jam    = total_detik // 3600
    menit  = (total_detik % 3600) // 60
    detik  = total_detik % 60
    bagian = []
    if jam:   bagian.append(f"{jam} jam")
    if menit: bagian.append(f"{menit} menit")
    if detik: bagian.append(f"{detik} detik")
    return " ".join(bagian) or "0 detik"


def jalankan(teks: str, callback_bicara=None, **ctx) -> Optional[str]:
    # Batalkan semua timer
    if any(k in teks.lower() for k in ["batalkan timer", "stop timer", "cancel timer"]):
        aktif = [t for t in _timers_aktif if t.is_alive()]
        if aktif:
            for t in aktif:
                t.cancel()
            _timers_aktif.clear()
            return "Semua timer aktif telah dibatalkan."
        return "Tidak ada timer yang aktif saat ini."

    # Ekstrak durasi
    jam = menit = detik = 0
    m = re.search(r'(\d+)\s*jam', teks, re.I)
    if m: jam = int(m.group(1))
    m = re.search(r'(\d+)\s*menit', teks, re.I)
    if m: menit = int(m.group(1))
    m = re.search(r'(\d+)\s*detik', teks, re.I)
    if m: detik = int(m.group(1))

    total = jam * 3600 + menit * 60 + detik
    if total <= 0:
        return None

    # Pesan opsional
    m_pesan = re.search(r'(?:untuk|bahwa|kalau|tentang)\s+(.+)', teks, re.I)
    pesan_custom = m_pesan.group(1).strip() if m_pesan else ""

    def _selesai():
        _timers_aktif[:] = [t for t in _timers_aktif if t.is_alive()]
        pesan = (f"Pengingat! {pesan_custom}" if pesan_custom
                 else "Timer selesai. Saatnya bertindak!")
        if callback_bicara:
            callback_bicara(pesan)

    timer = threading.Timer(total, _selesai)
    timer.daemon = True
    timer.start()
    _timers_aktif.append(timer)

    durasi = _format_durasi(total)
    if pesan_custom:
        return f"Oke, akan mengingatkan Anda dalam {durasi} untuk {pesan_custom}."
    return f"Timer {durasi} dimulai. Saya akan memberitahu Anda saat selesai."
