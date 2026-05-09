# ==============================================================
# skills/musik.py — Skill Pemutar Musik
# ==============================================================
import glob
import os
import subprocess
from typing import Optional

NAMA = "Pemutar Musik"
PRIORITAS = 20
TRIGGER_WORDS = [
    "putar musik", "play musik", "mainkan musik",
    "matikan musik", "stop musik", "hentikan musik",
    "pause musik", "lanjutkan musik",
]

_proses_musik = None


def _cari_file_musik() -> list:
    direktori = [
        os.path.expanduser("~/Music"),
        os.path.expanduser("~/music"),
        "/sdcard/Music",
        "/sdcard/musik",
        "/storage/emulated/0/Music",
        "/storage/emulated/0/musik",
    ]
    ekstensi = ("*.mp3", "*.m4a", "*.flac", "*.ogg", "*.aac", "*.wav")
    files = []
    for d in direktori:
        if os.path.isdir(d):
            for ext in ekstensi:
                files.extend(glob.glob(os.path.join(d, "**", ext), recursive=True))
    return files


def jalankan(teks: str, **ctx) -> Optional[str]:
    global _proses_musik
    teks_lower = teks.lower()

    if any(k in teks_lower for k in ["matikan", "stop", "pause", "hentikan"]):
        if _proses_musik and _proses_musik.poll() is None:
            _proses_musik.terminate()
            _proses_musik = None
            return "Musik dihentikan."
        return "Tidak ada musik yang sedang diputar."

    files = _cari_file_musik()
    if not files:
        return ("Tidak ada file musik ditemukan. "
                "Pastikan ada lagu di folder Music penyimpanan Anda.")

    if _proses_musik and _proses_musik.poll() is None:
        _proses_musik.terminate()

    try:
        _proses_musik = subprocess.Popen(
            ["mpv", "--no-video", "--shuffle", "--quiet",
             "--loop-playlist=inf"] + files[:100],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"Memutar {len(files)} lagu secara acak. Nikmati musiknya!"
    except FileNotFoundError:
        return "mpv tidak terinstal. Jalankan di Termux: pkg install mpv"
