# ==============================================================
# skills/aplikasi.py — Friday | Skill Buka/Tutup Aplikasi (Windows Desktop)
# Versi : 3.0.0 — Tambah kemampuan TUTUP aplikasi (taskkill)
# ==============================================================
"""
Setiap entri APP_MAP berisi (nama, alias_list, cara_buka, proses_exe):
  cara_buka  → salah satu dari:
    ("exe", "notepad.exe")            → dibuka via os.startfile (harus ada di PATH)
    ("path", "%APPDATA%\\Spotify\\Spotify.exe")  → path executable (env var di-expand)
    ("shell", "start ms-settings:")   → dijalankan lewat cmd /c start ...
    ("web", "https://web.whatsapp.com") → dibuka di browser default (app tanpa client desktop)
  proses_exe → nama proses Windows untuk ditutup via taskkill (mis. "Spotify.exe"),
               atau None kalau app itu tidak didukung untuk ditutup (mis. dibuka
               lewat tab browser, atau proses inti Windows yang berbahaya
               ditutup paksa seperti explorer.exe).
"""
import os
import subprocess
from typing import Optional

NAMA      = "Kontrol Aplikasi Desktop"
PRIORITAS = 5   # Tinggi — dicek sebelum skill lain

KATA_BUKA  = ["buka", "jalankan", "nyalakan", "aktifkan", "launch"]
KATA_TUTUP = ["tutup", "matikan", "keluar dari", "close", "stop"]

TRIGGER_WORDS = KATA_BUKA + KATA_TUTUP

# Peta nama app → alias suara → cara membuka → nama proses (untuk tutup)
APP_MAP = [
    # ── Aplikasi desktop asli (path instalasi umum) ──
    ("spotify",   ["spotify", "spotipai"],
        ("path", r"%APPDATA%\Spotify\Spotify.exe"), "Spotify.exe"),
    ("discord",   ["discord"],
        ("path", r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe"), "Discord.exe"),
    ("telegram",  ["telegram"],
        ("path", r"%APPDATA%\Telegram Desktop\Telegram.exe"), "Telegram.exe"),
    ("whatsapp",  ["whatsapp", "wa", "watsap"],
        ("web", "https://web.whatsapp.com"), None),
    ("zoom",      ["zoom", "zum"],
        ("path", r"%APPDATA%\Zoom\bin\Zoom.exe"), "Zoom.exe"),
    ("chrome",    ["chrome", "browser", "google chrome"],
        ("shell", "start chrome"), "chrome.exe"),

    # ── Utilitas sistem Windows ──
    ("kalkulator",     ["kalkulator", "calculator"], ("exe", "calc.exe"), "CalculatorApp.exe"),
    ("notepad",        ["notepad", "catatan"],       ("exe", "notepad.exe"), "notepad.exe"),
    # file explorer SENGAJA tidak bisa ditutup -- explorer.exe adalah shell
    # Windows itu sendiri (taskbar + desktop ikut mati kalau di-taskkill).
    ("file explorer",  ["file explorer", "explorer", "berkas"], ("exe", "explorer.exe"), None),
    ("pengaturan",     ["pengaturan", "settings", "setelan"], ("shell", "start ms-settings:"), "SystemSettings.exe"),
    ("kamera",         ["kamera", "camera", "kamer"], ("shell", "start microsoft.windows.camera:"), "WindowsCamera.exe"),
    ("task manager",   ["task manager", "pengelola tugas"], ("exe", "taskmgr.exe"), "Taskmgr.exe"),

    # ── Web (tanpa client desktop Windows resmi, tidak bisa ditutup spesifik) ──
    ("youtube",        ["youtube", "you tube", "yt"], ("web", "https://youtube.com"), None),
    ("youtube music",  ["youtube music", "yt music"], ("web", "https://music.youtube.com"), None),
    ("instagram",      ["instagram", "ig", "insta"], ("web", "https://instagram.com"), None),
    ("tiktok",         ["tiktok", "tik tok"], ("web", "https://tiktok.com"), None),
    ("twitter",        ["twitter", "x", "twiter"], ("web", "https://x.com"), None),
    ("facebook",       ["facebook", "fb"], ("web", "https://facebook.com"), None),
    ("gmail",          ["gmail", "email", "mail"], ("web", "https://mail.google.com"), None),
    ("maps",           ["maps", "google maps", "peta", "navigasi"], ("web", "https://maps.google.com"), None),
    ("netflix",        ["netflix"], ("web", "https://netflix.com"), None),
    ("gojek",          ["gojek", "go jek"], ("web", "https://gojek.com"), None),
    ("tokopedia",      ["tokopedia", "toped"], ("web", "https://tokopedia.com"), None),
    ("shopee",         ["shopee"], ("web", "https://shopee.co.id"), None),
]


def _cari_app(teks_lower: str):
    """Cari app yang disebutkan dalam teks. Return (nama, cara_buka, proses_exe) atau (None, None, None)."""
    for nama, alias_list, cara_buka, proses_exe in APP_MAP:
        for alias in alias_list:
            if alias in teks_lower:
                return nama, cara_buka, proses_exe
    return None, None, None


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


def _tutup_app(proses_exe: str) -> bool:
    """Tutup aplikasi paksa lewat taskkill /IM <proses>.exe /F."""
    try:
        ret = subprocess.run(
            ["taskkill", "/IM", proses_exe, "/F"],
            capture_output=True, timeout=5,
        )
        return ret.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def jalankan(teks: str, **ctx) -> Optional[str]:
    teks_lower = teks.lower()

    mau_tutup = any(k in teks_lower for k in KATA_TUTUP)
    mau_buka  = any(k in teks_lower for k in KATA_BUKA)

    if not (mau_tutup or mau_buka):
        return None

    nama, cara_buka, proses_exe = _cari_app(teks_lower)
    if not nama:
        return None

    if mau_tutup:
        if not proses_exe:
            return (
                f"Maaf, {nama.capitalize()} tidak bisa ditutup otomatis "
                f"(dibuka lewat tab browser, atau bagian inti sistem Windows)."
            )
        if _tutup_app(proses_exe):
            return f"{nama.capitalize()} ditutup, Bos."
        return f"{nama.capitalize()} sepertinya tidak sedang berjalan."

    # mau_buka
    try:
        from modules.tampilan import tampilkan_app_dibuka
        tampilkan_app_dibuka(nama.capitalize())
    except ImportError:
        pass

    if _buka_app(cara_buka):
        return f"{nama.capitalize()} dibuka, Bos."
    return (
        f"Tidak bisa membuka {nama.capitalize()}. "
        f"Pastikan aplikasinya terinstall di lokasi standar."
    )
