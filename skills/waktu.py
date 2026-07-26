# ==============================================================
# skills/waktu.py — Friday | Info Waktu Lokal (hari, tanggal, jam)
# ==============================================================
"""
Dijawab langsung dari jam sistem lokal — tidak butuh Claude/internet
sama sekali, jadi lebih cepat & hemat kuota untuk pertanyaan sederhana
seperti "jam berapa sekarang" atau "hari ini tanggal berapa".
"""
from datetime import datetime
from typing import Optional

NAMA      = "Info Waktu Lokal"
PRIORITAS = 6

TRIGGER_WORDS = [
    "jam berapa", "pukul berapa", "sekarang jam", "sekarang pukul",
    "hari apa", "hari ini hari", "sekarang hari",
    "tanggal berapa", "tanggal hari ini", "hari ini tanggal", "sekarang tanggal",
]

_HARI = {
    0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
    4: "Jumat", 5: "Sabtu", 6: "Minggu",
}
_BULAN = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


def _nama_hari(dt: datetime) -> str:
    return _HARI[dt.weekday()]


def _format_tanggal(dt: datetime) -> str:
    return f"{dt.day} {_BULAN[dt.month]} {dt.year}"


def jalankan(teks: str, **ctx) -> Optional[str]:
    teks_lower = teks.lower()
    sekarang   = datetime.now()

    tanya_jam     = any(k in teks_lower for k in ("jam berapa", "pukul berapa", "sekarang jam", "sekarang pukul"))
    tanya_hari    = any(k in teks_lower for k in ("hari apa", "hari ini hari", "sekarang hari"))
    tanya_tanggal = any(k in teks_lower for k in ("tanggal berapa", "tanggal hari ini", "hari ini tanggal", "sekarang tanggal"))

    if not (tanya_jam or tanya_hari or tanya_tanggal):
        return None

    bagian = []
    if tanya_hari:
        bagian.append(f"Hari ini {_nama_hari(sekarang)}")
    if tanya_tanggal:
        bagian.append(f"tanggal {_format_tanggal(sekarang)}")
    if tanya_jam:
        bagian.append(f"sekarang pukul {sekarang.hour}:{sekarang.minute:02d}")

    hasil = ", ".join(bagian) + "."
    return hasil[0].upper() + hasil[1:]   # kapital di huruf pertama saja
