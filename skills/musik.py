# ==============================================================
# skills/musik.py — Friday | Kontrol Musik
# v2.0 — Spotify + musik lokal + volume + next/prev
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


# ── Helpers ───────────────────────────────────────────────────

def _tampil_musik(aksi: str, detail: str = ""):
    try:
        from modules.tampilan import tampilkan_musik
        tampilkan_musik(aksi, detail)
    except ImportError:
        pass


def _cari_file_lokal() -> list:
    direktori = [
        os.path.expanduser("~/Music"),
        "/sdcard/Music",
        "/sdcard/musik",
        "/storage/emulated/0/Music",
    ]
    files = []
    for d in direktori:
        if os.path.isdir(d):
            for ext in ("*.mp3", "*.m4a", "*.flac", "*.ogg", "*.aac"):
                files.extend(glob.glob(os.path.join(d, "**", ext), recursive=True))
    return files


def _kontrol_media(aksi: str) -> bool:
    """
    Kontrol media playback Android — pause, play, next, prev.
    Urutan: termux-media-player → input keyevent → am broadcast Spotify.
    termux-media-player menggunakan MediaSession Android sehingga
    langsung menjangkau Spotify tanpa perlu root.
    """
    # ── Metode 1: termux-media-player (terbaik — pakai MediaSession) ──
    # Tersedia jika Termux:API terinstall (pkg install termux-api)
    termux_cmd = {
        "play_pause": ["termux-media-player", "play"],  # toggle
        "pause":      ["termux-media-player", "pause"],
        "play":       ["termux-media-player", "play"],
        "next":       ["termux-media-player", "next"],
        "previous":   ["termux-media-player", "previous"],
    }.get(aksi)

    if termux_cmd:
        try:
            ret = subprocess.run(termux_cmd, capture_output=True, timeout=5)
            if ret.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # ── Metode 2: Spotify broadcast intent langsung ────────────────
    spotify_aksi = {
        "play_pause": "com.spotify.mobile.android.ui.widget.PLAY_PAUSE",
        "pause":      "com.spotify.mobile.android.ui.widget.PAUSE",
        "play":       "com.spotify.mobile.android.ui.widget.PLAY",
        "next":       "com.spotify.mobile.android.ui.widget.NEXT",
        "previous":   "com.spotify.mobile.android.ui.widget.PREVIOUS",
    }.get(aksi)

    if spotify_aksi:
        try:
            ret = subprocess.run(
                ["am", "broadcast", "-a", spotify_aksi,
                 "-p", "com.spotify.music"],
                capture_output=True, timeout=5
            )
            if ret.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # ── Metode 3: input keyevent (fallback terakhir) ───────────────
    # 85=MEDIA_PLAY_PAUSE (toggle), 126=MEDIA_PLAY (explicit), 127=MEDIA_PAUSE
    kode = {"play_pause": "85", "pause": "127", "play": "126",
            "next": "87", "previous": "88"}.get(aksi)
    if kode:
        try:
            ret = subprocess.run(
                ["input", "keyevent", kode],
                capture_output=True, timeout=3
            )
            return ret.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return False


def _atur_volume(arah: str) -> str:
    """Naikkan atau turunkan volume media Android."""
    kode = "24" if arah == "naik" else "25"
    try:
        for _ in range(3):
            subprocess.run(["input", "keyevent", kode],
                           capture_output=True, timeout=2)
        return f"Volume {'dinaikkan' if arah == 'naik' else 'diturunkan'}."
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "Tidak bisa mengatur volume."


def _buka_spotify() -> bool:
    pkg = "com.spotify.music"
    for cmd in [
        # Syntax am start yang benar untuk Termux/Android
        ["am", "start", "-a", "android.intent.action.MAIN",
         "-c", "android.intent.category.LAUNCHER", "-p", pkg],
        ["monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"],
    ]:
        try:
            ret = subprocess.run(cmd, capture_output=True, timeout=5)
            if ret.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
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
        if _proses_mpv and _proses_mpv.poll() is None:
            # mpv: kirim 'q' lalu maju ke lagu berikut via playlist
            _proses_mpv.stdin and None   # mpv tidak pakai stdin di mode ini
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
        # Pause Spotify via MediaSession (termux-media-player pause)
        _kontrol_media("pause")
        _tampil_musik("⏹ Musik Dijeda")
        return "Musik dihentikan." if dihentikan else "Spotify dijeda."

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
            # Kirim play setelah jeda singkat
            import time; time.sleep(1.5)
            _kontrol_media("play_pause")
            return "Spotify dibuka dan diputar, Bos."
        return "Tidak bisa membuka Spotify. Pastikan aplikasinya terinstall."

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
        return "mpv tidak terinstall. Jalankan: pkg install mpv"
