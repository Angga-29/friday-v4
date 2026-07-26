# ==============================================================
# skills/video.py — Friday | Cari & Putar Video YouTube
# ==============================================================
"""
Cara kerja:
  1. Deteksi kombinasi kata kerja (cari/putar/tonton/dll) + target
     (video/youtube) di ucapan user -- LEBIH FLEKSIBEL dari sekadar
     cocokkan frasa persis, supaya tangkap ucapan natural seperti
     "carikan aku video lucu" atau "tolong putar video kucing di youtube".
  2. Buang kata kerja/target/kata sambung dari ucapan -> sisanya jadi topik
  3. Cari video top-1 yang cocok pakai yt-dlp (tanpa API key/kuota,
     tanpa download -- cuma ambil metadata/URL)
  4. Buka video itu langsung di browser default (webbrowser.open)

Ini BUKAN cuma buka halaman pencarian YouTube -- Friday langsung
memilihkan & membuka video yang paling cocok dengan yang diminta.

PRIORITAS dibuat LEBIH KECIL dari skills/aplikasi.py supaya dicek
lebih dulu -- kalau tidak, ucapan seperti "buka video X di youtube"
bisa keburu direbut skill aplikasi (alias "youtube" -> buka youtube.com
polos) sebelum skill ini sempat jalan.
"""
import webbrowser
from typing import Optional

NAMA      = "Cari & Putar Video"
PRIORITAS = 4

KATA_KERJA  = [
    "carikan", "cariin", "cari", "putar", "mainkan",
    "tontonkan", "tonton", "nonton", "lihatkan",
]
KATA_TARGET = ["video", "youtube"]
KATA_BUANG  = KATA_KERJA + KATA_TARGET + [
    "di", "ke", "aku", "saya", "tolong", "dong", "yang", "coba", "kan",
]

# Gate awal di SkillManager (cek substring sederhana) -- deteksi akurat
# kombinasi kata kerja+target dilakukan di dalam jalankan().
TRIGGER_WORDS = KATA_TARGET + ["nonton", "tonton"]


def _ekstrak_topik(teks: str) -> str:
    """Buang kata kerja/target/kata sambung, sisanya jadi topik pencarian."""
    kata_list = teks.lower().split()
    sisa = [k for k in kata_list if k not in KATA_BUANG]
    return " ".join(sisa).strip(" ,.!?") or teks


def jalankan(teks: str, **ctx) -> Optional[str]:
    teks_lower = teks.lower()

    ada_kerja  = any(k in teks_lower for k in KATA_KERJA)
    ada_target = any(t in teks_lower for t in KATA_TARGET)
    if not (ada_kerja and ada_target):
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
