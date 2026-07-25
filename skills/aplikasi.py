# ==============================================================
# skills/aplikasi.py — Friday | Skill Buka Aplikasi (Windows Desktop)
# Versi : 2.0.0 — Port dari Android (am start) ke Windows
# ==============================================================
"""
Setiap entri APP_MAP berisi (nama, alias_list, cara_buka) di mana
cara_buka adalah salah satu:
  ("exe", "notepad.exe")            → dibuka via os.startfile (harus ada di PATH)
  ("path", "%APPDATA%\\Spotify\\Spotify.exe")  → path executable (env var di-expand)
  ("shell", "start ms-settings:")   → dijalankan lewat cmd /c start ...
  ("web", "https://web.whatsapp.com") → dibuka di browser default (app tanpa client desktop)
"""
import os
import subprocess
from typing import Optional

NAMA      = "Kontrol Aplikasi Desktop"
PRIORITAS = 5   # Tinggi — dicek sebelum skill lain

TRIGGER_WORDS = [
    "buka", "jalankan", "nyalakan", "aktifkan", "launch",
]

# Peta nama app → alias suara → cara membuka di Windows
APP_MAP = [
    # ── Aplikasi desktop asli (path instalasi umum) ──
    ("spotify",   ["spotify", "spotipai"],
        ("path", r"%APPDATA%\Spotify\Spotify.exe")),
    ("discord",   ["discord"],
        ("path", r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe")),
    ("telegram",  ["telegram"],
        ("path", r"%APPDATA%\Telegram Desktop\Telegram.exe")),
    ("whatsapp",  ["whatsapp", "wa", "watsap"],
        ("web", "https://web.whatsapp.com")),
    ("zoom",      ["zoom", "zum"],
        ("path", r"%APPDATA%\Zoom\bin\Zoom.exe")),
    ("chrome",    ["chrome", "browser", "google chrome"],
        ("shell", "start chrome")),

    # ── Utilitas sistem Windows ──
    ("kalkulator",     ["kalkulator", "calculator"], ("exe", "calc.exe")),
    ("notepad",        ["notepad", "catatan"],       ("exe", "notepad.exe")),
    ("file explorer",  ["file explorer", "explorer", "berkas"], ("exe", "explorer.exe")),
    ("pengaturan",     ["pengaturan", "settings", "setelan"], ("shell", "start ms-settings:")),
    ("kamera",         ["kamera", "camera", "kamer"], ("shell", "start microsoft.windows.camera:")),
    ("task manager",   ["task manager", "pengelola tugas"], ("exe", "taskmgr.exe")),

    # ── Web (tanpa client desktop Windows resmi) ──
    ("youtube",        ["youtube", "you tube", "yt"], ("web", "https://youtube.com")),
    ("youtube music",  ["youtube music", "yt music"], ("web", "https://music.youtube.com")),
    ("instagram",      ["instagram", "ig", "insta"], ("web", "https://instagram.com")),
    ("tiktok",         ["tiktok", "tik tok"], ("web", "https://tiktok.com")),
    ("twitter",        ["twitter", "x", "twiter"], ("web", "https://x.com")),
    ("facebook",       ["facebook", "fb"], ("web", "https://facebook.com")),
    ("gmail",          ["gmail", "email", "mail"], ("web", "https://mail.google.com")),
    ("maps",           ["maps", "google maps", "peta", "navigasi"], ("web", "https://maps.google.com")),
    ("netflix",        ["netflix"], ("web", "https://netflix.com")),
    ("gojek",          ["gojek", "go jek"], ("web", "https://gojek.com")),
    ("tokopedia",      ["tokopedia", "toped"], ("web", "https://tokopedia.com")),
    ("shopee",         ["shopee"], ("web", "https://shopee.co.id")),
]


def _cari_app(teks_lower: str):
    """Cari app yang disebutkan dalam teks. Return (nama, cara_buka) atau (None, None)."""
    for nama, alias_list, cara_buka in APP_MAP:
        for alias in alias_list:
            if alias in teks_lower:
                return nama, cara_buka
    return None, None


def _buka_app(cara_buka) -> bool:
    """Buka aplikasi sesuai jenis cara_buka."""
    jenis, target = cara_buka

    try:
        if jenis == "web":
            import webbrowser
            return webbrowser.open(target)

        if jenis == "exe":
            os.startfile(target)
            return True

        if jenis == "path":
            path_expanded = os.path.expandvars(target)
            if " " in path_expanded and "--" in path_expanded:
                # Path dengan argumen (mis. Discord Update.exe --processStart)
                bagian = path_expanded.split(" ", 1)
                subprocess.Popen(
                    [bagian[0]] + bagian[1].split(),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                return True
            if not os.path.exists(path_expanded):
                return False
            os.startfile(path_expanded)
            return True

        if jenis == "shell":
            subprocess.Popen(
                ["cmd", "/c", target],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True

    except (FileNotFoundError, OSError, AttributeError):
        # AttributeError: os.startfile hanya ada di Windows
        return False

    return False


def jalankan(teks: str, **ctx) -> Optional[str]:
    teks_lower = teks.lower()

    kata_buka = ["buka", "jalankan", "nyalakan", "aktifkan", "launch"]
    if not any(k in teks_lower for k in kata_buka):
        return None

    nama, cara_buka = _cari_app(teks_lower)
    if not nama:
        return None

    try:
        from modules.tampilan import tampilkan_app_dibuka
        tampilkan_app_dibuka(nama.capitalize())
    except ImportError:
        pass

    if _buka_app(cara_buka):
        return f"{nama.capitalize()} dibuka, Bos."
    else:
        return (
            f"Tidak bisa membuka {nama.capitalize()}. "
            f"Pastikan aplikasinya terinstall di lokasi standar."
        )
