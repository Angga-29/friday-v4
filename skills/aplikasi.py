# ==============================================================
# skills/aplikasi.py — Friday | Skill Buka Aplikasi Android
# ==============================================================
import subprocess
from typing import Optional

NAMA      = "Kontrol Aplikasi Android"
PRIORITAS = 5   # Tinggi — dicek sebelum skill lain

TRIGGER_WORDS = [
    "buka", "jalankan", "nyalakan", "aktifkan", "launch",
]

# Peta nama app → package Android
# alias: kata-kata yang dikenali dari suara user
APP_MAP = [
    # ── Sosial & Pesan ──
    ("spotify",         "com.spotify.music",              ["spotify", "spotipai"]),
    ("youtube",         "com.google.android.youtube",     ["youtube", "you tube", "yt"]),
    ("youtube music",   "com.google.android.apps.youtube.music", ["youtube music", "yt music"]),
    ("whatsapp",        "com.whatsapp",                   ["whatsapp", "wa", "watsap"]),
    ("instagram",       "com.instagram.android",          ["instagram", "ig", "insta"]),
    ("tiktok",          "com.zhiliaoapp.musically",       ["tiktok", "tik tok"]),
    ("telegram",        "org.telegram.messenger",         ["telegram"]),
    ("line",            "jp.naver.line.android",          ["line"]),
    ("twitter",         "com.twitter.android",            ["twitter", "x", "twiter"]),
    ("facebook",        "com.facebook.katana",            ["facebook", "fb"]),
    ("discord",         "com.discord",                    ["discord"]),
    ("zoom",            "us.zoom.videomeetings",          ["zoom", "zum"]),
    ("gmail",           "com.google.android.gm",          ["gmail", "email", "mail"]),

    # ── E-Wallet & Banking ──
    ("dana",            "id.dana",                        ["dana"]),
    ("ovo",             "ovo.id",                         ["ovo"]),
    ("gopay",           "com.gojek.app",                  ["gopay", "go pay"]),
    ("bca mobile",      "com.bca",                        ["bca", "bca mobile", "mybca"]),
    ("brimo",           "id.co.bri.brimo",                ["brimo", "bri", "bri mobile"]),
    ("mandiri online",  "com.bankmandiri.mandirionline",  ["mandiri", "mandiri online", "livin"]),

    # ── Browser & Sistem ──
    ("chrome",          "com.android.chrome",             ["chrome", "browser", "google chrome"]),
    ("play store",      "com.android.vending",            ["play store", "playstore", "google play"]),
    ("maps",            "com.google.android.apps.maps",   ["maps", "google maps", "peta", "navigasi"]),
    ("kamera",          "com.android.camera2",            ["kamera", "camera", "kamer"]),
    ("galeri",          "com.google.android.apps.photos", ["galeri", "gallery", "foto", "gambar"]),
    ("kalkulator",      "com.android.calculator2",        ["kalkulator", "calculator"]),
    ("pengaturan",      "com.android.settings",           ["pengaturan", "settings", "setelan"]),
    ("jam",             "com.android.deskclock",          ["jam", "clock", "alarm"]),

    # ── Hiburan & Belanja ──
    ("netflix",         "com.netflix.mediaclient",        ["netflix"]),
    ("capcut",          "com.lemon.lvoverseas",           ["capcut", "cap cut"]),
    ("gojek",           "com.gojek.app",                  ["gojek", "go jek"]),
    ("grab",            "com.grabtaxi.passenger",         ["grab"]),
    ("tokopedia",       "com.tokopedia.tkpd",             ["tokopedia", "toped"]),
    ("shopee",          "com.shopee.id",                  ["shopee"]),
]


def _cari_app(teks_lower: str):
    """Cari app yang disebutkan dalam teks. Return (nama, package) atau None."""
    for nama, pkg, alias_list in APP_MAP:
        for alias in alias_list:
            if alias in teks_lower:
                return nama, pkg
    return None, None


def _buka_package(pkg: str) -> bool:
    """Coba buka app Android via beberapa metode."""

    # Metode 1: am start (Activity Manager — tersedia di Termux)
    try:
        ret = subprocess.run(
            ["am", "start", "-n", f"{pkg}/.MainActivity"],
            capture_output=True, timeout=5
        )
        if ret.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Metode 2: am start tanpa activity (lebih fleksibel)
    try:
        ret = subprocess.run(
            ["am", "start", pkg],
            capture_output=True, timeout=5
        )
        if ret.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Metode 3: monkey launcher (tersedia di semua Android)
    try:
        ret = subprocess.run(
            ["monkey", "-p", pkg, "-c",
             "android.intent.category.LAUNCHER", "1"],
            capture_output=True, timeout=5
        )
        if ret.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Metode 4: termux-open-url dengan intent
    try:
        ret = subprocess.run(
            ["termux-open-url", f"intent:#Intent;package={pkg};end"],
            capture_output=True, timeout=5
        )
        if ret.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return False


def jalankan(teks: str, **ctx) -> Optional[str]:
    teks_lower = teks.lower()

    # Harus ada kata buka/jalankan/dll
    kata_buka = ["buka", "jalankan", "nyalakan", "aktifkan", "launch"]
    if not any(k in teks_lower for k in kata_buka):
        return None

    nama, pkg = _cari_app(teks_lower)
    if not nama:
        return None

    # Tampilkan panel di layar
    try:
        from modules.tampilan import tampilkan_app_dibuka
        tampilkan_app_dibuka(nama.capitalize())
    except ImportError:
        pass

    if _buka_package(pkg):
        return f"{nama.capitalize()} dibuka, Bos."
    else:
        return (
            f"Tidak bisa membuka {nama.capitalize()}. "
            f"Pastikan aplikasinya terinstall dan Termux punya izin."
        )
