# ==============================================================
# skills/musik.py — Friday | Kontrol Musik (Windows Desktop)
# v3.0 — Port dari Android (termux-media-player/intent) ke Windows
#        virtual media key via ctypes, sistem-wide untuk Spotify
#        Desktop/browser/app apa pun yang sedang fokus/aktif.
# ==============================================================
import glob
import os
import subprocess
from typing import Optional

NAMA      = "Kontrol Musik"
PRIORITAS = 8

TRIGGER_WORDS = [
    # Putar
    "putar musik", "play musik", "mainkan musik", "nyalakan musik",
    "putar spotify", "buka spotify musik", "play spotify",
    "putar lagu", "mainkan lagu",
    # Stop / Pause / Resume
    "hentikan musik", "stop musik", "matikan musik", "pause musik",
    "berhenti musik", "jeda musik", "jeda lagu",
    "lanjutkan musik", "resume musik", "play lagi", "putar lagi",
    # Next / Prev
    "lagu berikutnya", "next lagu", "skip lagu", "ganti lagu",
    "lagu sebelumnya", "previous lagu", "lagu tadi",
    # Volume
    "volume musik", "kencangkan", "keraskan", "kecilkan", "volume",
    "naikkan volume", "turunkan volume", "volume naik", "volume turun",
    # Spotify khusus
    "spotify",
]

_proses_mpv: Optional[subprocess.Popen] = None

# Virtual-key code Windows untuk media key (dipakai via keybd_event)
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_UP        = 0xAF
VK_VOLUME_DOWN      = 0xAE


# ── Helpers ───────────────────────────────────────────────────

def _tampil_musik(aksi: str, detail: str = ""):
    try:
        from modules.tampilan import tampilkan_musik
        tampilkan_musik(aksi, detail)
    except ImportError:
        pass


def _cari_file_lokal() -> list:
    direktori = [
        os.path.expanduser("~\\Music"),
        os.path.expanduser("~/Music"),
    ]
    files = []
    for d in direktori:
        if os.path.isdir(d):
            for ext in ("*.mp3", "*.m4a", "*.flac", "*.ogg", "*.aac"):
                files.extend(glob.glob(os.path.join(d, "**", ext), recursive=True))
    return files


def _kirim_media_key(vk_code: int) -> bool:
    """
    Simulasikan penekanan virtual media key Windows via ctypes/user32.
    Bekerja system-wide (Spotify Desktop, browser, app apa pun) tanpa
    perlu API khusus per-aplikasi — menggantikan broadcast intent Android.
    """
    try:
        import ctypes
        user32 = ctypes.windll.user32   # hanya ada di Windows
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP       = 0x0002
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        return True
    except (AttributeError, OSError):
        # ctypes.windll hanya tersedia di Windows
        return False


def _kontrol_media(aksi: str) -> bool:
    """Kontrol media playback: play/pause, next, prev via virtual media key."""
    kode = {
        "play_pause": VK_MEDIA_PLAY_PAUSE,
        "pause":      VK_MEDIA_PLAY_PAUSE,
        "play":       VK_MEDIA_PLAY_PAUSE,
        "next":       VK_MEDIA_NEXT_TRACK,
        "previous":   VK_MEDIA_PREV_TRACK,
    }.get(aksi)
    return _kirim_media_key(kode) if kode else False


def _atur_volume(arah: str) -> str:
    """Naikkan atau turunkan volume sistem lewat virtual media key."""
    vk = VK_VOLUME_UP if arah == "naik" else VK_VOLUME_DOWN
    berhasil = any(_kirim_media_key(vk) for _ in range(3))
    if not berhasil:
        return "Tidak bisa mengatur volume."
    return f"Volume {'dinaikkan' if arah == 'naik' else 'diturunkan'}."


def _buka_spotify() -> bool:
    """Coba buka Spotify Desktop (path instalasi default Windows), fallback web player."""
    path = os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")
    try:
        if os.path.exists(path):
            os.startfile(path)
            return True
    except (AttributeError, OSError):
        pass

    try:
        import webbrowser
        return webbrowser.open("https://open.spotify.com")
    except Exception:
        return False


# ── Skill entry point ─────────────────────────────────────────

def jalankan(teks: str, **ctx) -> Optional[str]:
    global _proses_mpv
    teks_lower = teks.lower()

    # ── VOLUME ────────────────────────────────────────────────
    if any(k in teks_lower for k in
           ["kencangkan", "keraskan", "naikkan volume", "volume naik", "volume keras"]):
        _tampil_musik("Volume", "naik ▲▲▲")
        return _atur_volume("naik")

    if any(k in teks_lower for k in
           ["kecilkan", "turunkan volume", "volume turun", "volume kecil"]):
        _tampil_musik("Volume", "turun ▼▼▼")
        return _atur_volume("turun")

    # ── NEXT / PREV ───────────────────────────────────────────
    if any(k in teks_lower for k in
           ["berikutnya", "next", "skip", "ganti lagu"]):
        _tampil_musik("▶▶ Next Track")
        _kontrol_media("next")
        return "Lagu selanjutnya."

    if any(k in teks_lower for k in
           ["sebelumnya", "previous", "lagu tadi"]):
        _tampil_musik("◀◀ Previous Track")
        _kontrol_media("previous")
        return "Kembali ke lagu sebelumnya."

    # ── STOP / PAUSE ──────────────────────────────────────────
    if any(k in teks_lower for k in
           ["hentikan", "stop", "matikan musik", "pause", "berhenti", "jeda"]):
        dihentikan = False
        if _proses_mpv and _proses_mpv.poll() is None:
            _proses_mpv.terminate()
            _proses_mpv = None
            dihentikan = True
        # Pause Spotify/app aktif via virtual media key
        _kontrol_media("pause")
        _tampil_musik("⏹ Musik Dijeda")
        return "Musik dihentikan." if dihentikan else "Musik dijeda."

    # ── LANJUTKAN / RESUME ────────────────────────────────────
    if any(k in teks_lower for k in
           ["lanjutkan musik", "resume musik", "play lagi", "putar lagi"]):
        _kontrol_media("play")
        _tampil_musik("▶ Lanjutkan Musik")
        return "Musik dilanjutkan."

    # ── SPOTIFY ───────────────────────────────────────────────
    if "spotify" in teks_lower:
        _tampil_musik("▶ Membuka Spotify")
        if _buka_spotify():
            import time; time.sleep(1.5)
            _kontrol_media("play_pause")
            return "Spotify dibuka dan diputar, Bos."
        return "Tidak bisa membuka Spotify."

    # ── MUSIK LOKAL (mpv) ─────────────────────────────────────
    files = _cari_file_lokal()
    if not files:
        # Tidak ada lokal → coba buka Spotify
        _tampil_musik("▶ Spotify (tidak ada musik lokal)")
        if _buka_spotify():
            import time; time.sleep(1.5)
            _kontrol_media("play_pause")
            return ("Tidak ada musik lokal ditemukan. "
                    "Membuka Spotify sebagai gantinya.")
        return ("Tidak ada file musik lokal. "
                "Install Spotify atau tambahkan lagu ke folder Music.")

    if _proses_mpv and _proses_mpv.poll() is None:
        _proses_mpv.terminate()

    try:
        _proses_mpv = subprocess.Popen(
            ["mpv", "--no-video", "--shuffle",
             "--quiet", "--loop-playlist=inf"] + files[:200],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _tampil_musik("▶ Memutar Musik Lokal", f"{len(files)} lagu (acak)")
        return f"Memutar {len(files)} lagu lokal secara acak. Nikmati, Bos!"
    except FileNotFoundError:
        return "mpv tidak terinstall. Install dari https://mpv.io atau via winget."
