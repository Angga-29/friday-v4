# ==============================================================
# skills/video.py — Friday | Cari & Putar Video YouTube
# ==============================================================
"""
Cara kerja:
  1. Ambil topik dari ucapan user (buang kata pemicu)
  2. Cari video top-1 yang cocok pakai yt-dlp (tanpa API key/kuota,
     tanpa download -- cuma ambil metadata/URL)
  3. Buka video itu langsung di browser default (webbrowser.open)

Ini BUKAN cuma buka halaman pencarian YouTube -- Friday langsung
memilihkan & membuka video yang paling cocok dengan yang diminta.
"""
import webbrowser
from typing import Optional

NAMA      = "Cari & Putar Video"
PRIORITAS = 6

TRIGGER_WORDS = [
    "putar video", "cari video", "tonton video", "carikan video",
    "video tentang", "cari di youtube", "cariin video",
    "putar youtube", "mainkan video",
]


def _ekstrak_topik(teks: str) -> str:
    """Bersihkan trigger words dari input untuk mendapat topik/judul video."""
    topik = teks.lower()
    for trigger in sorted(TRIGGER_WORDS, key=len, reverse=True):
        topik = topik.replace(trigger, "").strip()
    return topik.strip(" ,.!?") or teks


def jalankan(teks: str, **ctx) -> Optional[str]:
    teks_lower = teks.lower()
    if not any(t in teks_lower for t in TRIGGER_WORDS):
        return None

    topik = _ekstrak_topik(teks)
    if not topik:
        return "Video apa yang mau ditonton, Bos?"

    try:
        import yt_dlp
    except ImportError:
        return "Package 'yt-dlp' belum terinstall. Jalankan: pip install yt-dlp"

    try:
        opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{topik}", download=False)
            entries = info.get("entries") or []
            if not entries:
                return f"Tidak ketemu video tentang {topik}, Bos."
            video = entries[0]
            url   = video.get("webpage_url") or f"https://www.youtube.com/watch?v={video.get('id')}"
            judul = video.get("title", topik)
    except Exception as e:
        return f"Gagal mencari video: {e}"

    if webbrowser.open(url):
        return f"Memutar '{judul}' di YouTube, Bos."
    return f"Ketemu videonya ('{judul}') tapi gagal membuka browser."
