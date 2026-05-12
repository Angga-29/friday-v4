# ==============================================================
# skills/web.py — Friday | Skill Browser & Berita Online
# Versi : 1.0.0
# ==============================================================
"""
Skill ini menangani perintah-perintah terkait browser & berita:
  - "buka google"                  → Google homepage
  - "buka berita pertama/kedua/ke 3"→ buka URL berita yang sedang
                                     ditampilkan di dashboard
  - "tampilkan berita ke dua"      → sama seperti di atas
  - "buka youtube.com / detik.com" → buka URL apapun langsung
  - "cari resep nasi goreng di google" → Google search

Membutuhkan ctx["berita"] = list[dict] dari main.py.
"""

import re
import subprocess
import urllib.parse
from typing import Optional

NAMA      = "Browser & Berita Online"
PRIORITAS = 4   # dicek SEBELUM aplikasi.py (priority 5) supaya
                # "buka berita pertama" tidak salah ke skill aplikasi

TRIGGER_WORDS = [
    "buka berita", "tampilkan berita", "lihat berita",
    "buka google", "cari di google", "google",
    "buka situs", "buka link", "buka url", "buka website",
    "buka detik", "buka kompas", "buka cnn", "buka bbc",
    "buka youtube.com", "buka tiktok.com",
]

# Pemetaan kata urutan → index berita
_URUTAN = {
    "pertama": 0, "satu": 0, "1": 0, "ke 1": 0, "kesatu": 0,
    "kedua": 1, "dua": 1, "2": 1, "ke 2": 1,
    "ketiga": 2, "tiga": 2, "3": 2, "ke 3": 2,
    "keempat": 3, "empat": 3, "4": 3, "ke 4": 3,
    "kelima": 4, "lima": 4, "5": 4, "ke 5": 4,
    "keenam": 5, "enam": 5, "6": 5, "ke 6": 5,
}

# Shortcut situs berita / portal populer (key = kata kunci di voice)
_PORTAL = {
    "kompas"     : "https://www.kompas.com",
    "detik"      : "https://www.detik.com",
    "tempo"      : "https://www.tempo.co",
    "cnn indonesia": "https://www.cnnindonesia.com",
    "liputan6"   : "https://www.liputan6.com",
    "tribun"     : "https://www.tribunnews.com",
    "bbc"        : "https://www.bbc.com/news",
    "reuters"    : "https://www.reuters.com",
    "al jazeera" : "https://www.aljazeera.com",
    "guardian"   : "https://www.theguardian.com",
    "techcrunch" : "https://techcrunch.com",
}


def _buka_url(url: str) -> bool:
    """Buka URL di browser default Android via beberapa fallback."""
    cmds = [
        ["am", "start", "-a", "android.intent.action.VIEW",
         "-d", url, "-p", "com.android.chrome"],
        ["am", "start", "-a", "android.intent.action.VIEW",
         "-d", url, "-p", "com.google.android.apps.chrome"],
        ["am", "start", "-a", "android.intent.action.VIEW", "-d", url],
        ["termux-open-url", url],
        ["xdg-open", url],
    ]
    for cmd in cmds:
        try:
            subprocess.Popen(cmd,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue
    return False


def _cari_urutan(teks_lower: str) -> Optional[int]:
    """Cari kata urutan (pertama, kedua, ...) dalam teks. Return index 0-based."""
    # Cek angka eksplisit lebih dulu: "berita 2", "berita ke 3"
    m = re.search(r"berita\s+(?:ke\s+)?(\d+)", teks_lower)
    if m:
        return int(m.group(1)) - 1
    for kata, idx in _URUTAN.items():
        if f" {kata}" in f" {teks_lower}":
            return idx
    return None


def _ekstrak_query_google(teks: str) -> str:
    """Ambil query setelah 'cari ... di google' atau 'google ...'."""
    teks_low = teks.lower()
    # Pattern 1: cari X di google
    m = re.search(r"cari\s+(.+?)\s+(?:di\s+)?google", teks_low)
    if m:
        return m.group(1).strip()
    # Pattern 2: google + topic
    m = re.search(r"\bgoogle\s+(.+)$", teks_low)
    if m:
        q = m.group(1).strip()
        if q and q not in ("saja", "dong", "ya"):
            return q
    return ""


def _ekstrak_url_langsung(teks: str) -> Optional[str]:
    """Deteksi URL/domain dalam teks (mis. 'buka detik.com')."""
    m = re.search(r"\b([a-z0-9\-]+\.(com|co\.id|id|net|org|io|tv|app))\b",
                  teks.lower())
    if m:
        domain = m.group(1)
        return f"https://{domain}"
    return None


def jalankan(teks: str, **ctx) -> Optional[str]:
    teks_lower = teks.lower().strip()
    berita     = ctx.get("berita") or []

    # ── 1. BUKA BERITA KE-N ─────────────────────────────────────
    if "berita" in teks_lower and any(
        k in teks_lower for k in ("buka", "tampilkan", "lihat")
    ):
        idx = _cari_urutan(teks_lower)
        if idx is None:
            idx = 0   # default: berita pertama

        if not berita:
            return "Berita belum tersedia, Bos. Coba sebentar lagi."

        if idx >= len(berita):
            return (
                f"Saya hanya punya {len(berita)} berita di dashboard, "
                f"Bos. Mau saya buka yang pertama saja?"
            )

        item = berita[idx]
        if isinstance(item, dict):
            url   = item.get("url", "")
            judul = item.get("judul", "")
        else:
            url, judul = "", str(item)

        if not url:
            return f"Berita itu tidak punya link, Bos. Judulnya: {judul}"

        urutan_kata = ["pertama", "kedua", "ketiga", "keempat", "kelima", "keenam"]
        urut = urutan_kata[idx] if idx < len(urutan_kata) else f"ke-{idx+1}"

        if _buka_url(url):
            judul_pendek = judul[:60] + ("..." if len(judul) > 60 else "")
            return f"Buka berita {urut}: {judul_pendek}"
        return "Tidak bisa membuka browser, Bos. Cek izin Termux."

    # ── 2. CARI DI GOOGLE ───────────────────────────────────────
    if "google" in teks_lower and any(
        k in teks_lower for k in ("cari", "search", "googling")
    ):
        query = _ekstrak_query_google(teks)
        if query:
            url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
            if _buka_url(url):
                return f"Mencari {query} di Google, Bos."
            return "Tidak bisa membuka browser, Bos."

    # ── 3. BUKA GOOGLE HOMEPAGE ─────────────────────────────────
    # Skip kalau ada kata yang menunjuk app Google lain (maps, music, drive, dll)
    if re.search(r"\bbuka\s+google\b", teks_lower) and not any(
        k in teks_lower for k in (
            "maps", "music", "drive", "photos", "play", "translate", "calendar"
        )
    ):
        if _buka_url("https://www.google.com"):
            return "Google dibuka, Bos."
        return "Tidak bisa membuka browser, Bos."

    # ── 4. BUKA URL LANGSUNG (domain.com) ───────────────────────
    if any(k in teks_lower for k in ("buka", "tampilkan")):
        url = _ekstrak_url_langsung(teks)
        if url:
            if _buka_url(url):
                return f"Membuka {url.replace('https://','')}, Bos."
            return "Tidak bisa membuka browser, Bos."

    # ── 5. BUKA PORTAL BERITA (kompas, detik, bbc, dll) ─────────
    if any(k in teks_lower for k in ("buka", "tampilkan", "lihat")):
        for nama, url in _PORTAL.items():
            if nama in teks_lower:
                if _buka_url(url):
                    return f"Buka {nama.title()}, Bos."
                return "Tidak bisa membuka browser, Bos."

    return None
