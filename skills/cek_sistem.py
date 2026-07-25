# ==============================================================
# skills/cek_sistem.py — Skill Diagnostik Sistem
# Terinspirasi dari OpenJarvis 'jarvis doctor' command
# ==============================================================
import importlib
import shutil
from pathlib import Path
from typing import Optional

NAMA = "Cek Sistem (Doctor)"
PRIORITAS = 3
TRIGGER_WORDS = [
    "cek sistem", "friday doctor", "status sistem",
    "cek komponen", "diagnosa friday", "test sistem",
    "cek semua", "sistem sehat",
]


def _cek_import(modul: str) -> bool:
    try:
        importlib.import_module(modul)
        return True
    except ImportError:
        return False


def _cek_perintah(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def jalankan(teks: str, callback_bicara=None, **ctx) -> Optional[str]:
    paket = [
        ("Claude AI (anthropic)", "anthropic"),
        ("Edge-TTS",          "edge_tts"),
        ("pyttsx3 (SAPI TTS)", "pyttsx3"),
        ("gTTS (fallback)",   "gtts"),
        ("SpeechRecognition", "speech_recognition"),
        ("OpenCV",            "cv2"),
        ("DuckDuckGo ddgs",   "ddgs"),
        ("python-dotenv",     "dotenv"),
        ("NumPy",             "numpy"),
        ("Requests",          "requests"),
    ]
    alat = [
        ("mpv (audio)",  "mpv"),
        ("ffplay (audio)", "ffplay"),
        ("python",       "python"),
    ]

    ok_pkg  = [n for n, m in paket if _cek_import(m)]
    fail_pkg = [n for n, m in paket if not _cek_import(m)]
    ok_alat  = [n for n, c in alat if _cek_perintah(c)]
    fail_alat = [n for n, c in alat if not _cek_perintah(c)]

    db_ok = (Path.home() / ".friday_memory" / "friday.db").exists()

    total = len(paket) + len(alat) + 1
    ok_total = len(ok_pkg) + len(ok_alat) + (1 if db_ok else 0)
    skor = int((ok_total / total) * 100)

    masalah = fail_pkg + fail_alat + ([] if db_ok else ["Database memori"])

    if not masalah:
        ringkasan = f"Sistem Friday dalam kondisi prima! Skor diagnostik {skor} persen."
    else:
        ringkasan = (
            f"Skor diagnostik {skor} persen. "
            f"Komponen bermasalah: {', '.join(masalah[:3])}"
            + (f", dan {len(masalah)-3} lainnya." if len(masalah) > 3 else ".")
        )

    detail = (
        f"[FRIDAY DOCTOR — Skor: {skor}%]\n"
        f"Paket OK    : {', '.join(ok_pkg) or '-'}\n"
        f"Paket GAGAL : {', '.join(fail_pkg) or '-'}\n"
        f"Alat OK     : {', '.join(ok_alat) or '-'}\n"
        f"Alat GAGAL  : {', '.join(fail_alat) or '-'}\n"
        f"Database    : {'OK' if db_ok else 'BELUM ADA'}\n"
        f"{'─'*40}\n"
        f"{ringkasan}"
    )

    if callback_bicara:
        callback_bicara(ringkasan)

    return detail
