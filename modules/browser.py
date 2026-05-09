# ==============================================================
# modules/browser.py — Project Friday | Modul Browsing Internet
# Versi : 1.0.1
# Engine: DuckDuckGo Search (gratis, tanpa API key)
# ==============================================================

import requests
from modules.tampilan import tampilkan_status

# --- Konfigurasi ---
MAX_HASIL        = 4      # Jumlah hasil pencarian yang diambil
TIMEOUT_CARI     = 8      # Detik timeout pencarian
MAX_PANJANG_BODY = 300    # Karakter maksimal per hasil (hemat token)

# --- Kata kunci yang memicu browsing otomatis ---
KATA_KUNCI_BROWSING = [
    # Temporal — butuh data terkini
    "terbaru", "terkini", "hari ini", "sekarang", "minggu ini",
    "bulan ini", "kemarin", "baru saja", "update", "tadi",
    # Perintah eksplisit
    "cari", "carikan", "browsing", "googling", "cek internet",
    "temukan", "lihat di internet", "search",
    # Info yang butuh data real-time
    "harga", "kurs", "nilai tukar", "saham", "crypto", "bitcoin",
    "berapa sekarang", "berapa harga",
    # Tokoh & jabatan (berubah-ubah)
    "presiden", "perdana menteri", "ceo", "pemimpin", "gubernur",
    # Hiburan & budaya populer (selalu berubah)
    "film terbaru", "lagu terbaru", "album baru", "game terbaru",
    # Pertanyaan faktual terbuka
    "apa itu", "siapa itu", "jelaskan tentang", "bagaimana cara",
    "tutorial", "cara membuat", "langkah",
    # Berita
    "berita tentang", "kabar", "kejadian", "peristiwa",
]


def perlu_browsing(teks: str) -> bool:
    """
    Mendeteksi apakah pertanyaan pengguna memerlukan pencarian internet.

    Args:
        teks: Input teks dari pengguna.

    Returns:
        True jika perlu browsing, False jika tidak.
    """
    teks_lower = teks.lower()
    return any(kata in teks_lower for kata in KATA_KUNCI_BROWSING)


def cari_web(query: str) -> list[dict]:
    """
    Mencari informasi di internet menggunakan DuckDuckGo Instant Answer API.
    Tidak memerlukan API key — gratis dan aman.

    Args:
        query: Kata kunci pencarian.

    Returns:
        List of dict dengan key 'judul', 'isi', 'url'.
        List kosong jika gagal.
    """
    tampilkan_status(f"Mencari: '{query}'", "browsing")

    # --- Metode 1: DuckDuckGo library (coba ddgs dulu, fallback ke duckduckgo_search) ---
    try:
        try:
            from ddgs import DDGS          # nama package baru
        except ImportError:
            from duckduckgo_search import DDGS  # nama package lama
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=MAX_HASIL))

        if raw:
            hasil = []
            for r in raw:
                isi = r.get("body", "")[:MAX_PANJANG_BODY]
                hasil.append({
                    "judul": r.get("title", "Tanpa judul"),
                    "isi"  : isi,
                    "url"  : r.get("href", "")
                })
            tampilkan_status(f"{len(hasil)} hasil ditemukan.", "sukses")
            return hasil

    except ImportError:
        tampilkan_status(
            "duckduckgo_search belum terinstall. Jalankan: pip install duckduckgo_search",
            "peringatan"
        )
    except Exception as e:
        tampilkan_status(f"DuckDuckGo error: {e}", "peringatan")

    # --- Metode 2: DuckDuckGo Instant Answer API (fallback tanpa library) ---
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q"            : query,
            "format"       : "json",
            "no_html"      : 1,
            "skip_disambig": 1
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT_CARI)
        data = resp.json()

        hasil = []

        # Abstract (ringkasan topik)
        if data.get("AbstractText"):
            hasil.append({
                "judul": data.get("Heading", query),
                "isi"  : data["AbstractText"][:MAX_PANJANG_BODY],
                "url"  : data.get("AbstractURL", "")
            })

        # Related Topics
        for topic in data.get("RelatedTopics", [])[:MAX_HASIL - 1]:
            if isinstance(topic, dict) and topic.get("Text"):
                hasil.append({
                    "judul": topic.get("Text", "")[:60],
                    "isi"  : topic.get("Text", "")[:MAX_PANJANG_BODY],
                    "url"  : topic.get("FirstURL", "")
                })

        if hasil:
            tampilkan_status(f"{len(hasil)} hasil ditemukan (fallback).", "sukses")
            return hasil

    except Exception as e:
        tampilkan_status(f"Fallback search error: {e}", "error")

    tampilkan_status("Tidak ada hasil pencarian ditemukan.", "peringatan")
    return []


def format_untuk_gemini(query: str, hasil: list[dict]) -> str:
    """
    Memformat hasil pencarian web menjadi konteks yang siap dikirim ke Gemini.

    Args:
        query  : Pertanyaan asli pengguna.
        hasil  : List hasil pencarian dari cari_web().

    Returns:
        String konteks terformat untuk Gemini.
    """
    if not hasil:
        return (
            f"[PENCARIAN WEB GAGAL]\n"
            f"Tidak menemukan hasil untuk: '{query}'.\n"
            f"Jawab berdasarkan pengetahuanmu saja dan informasikan bahwa "
            f"data terbaru tidak tersedia saat ini."
        )

    baris_hasil = []
    for i, r in enumerate(hasil, 1):
        baris_hasil.append(
            f"Sumber {i}: {r['judul']}\n"
            f"Info     : {r['isi']}\n"
            f"URL      : {r['url']}"
        )

    return (
        f"[HASIL PENCARIAN INTERNET - {len(hasil)} sumber]\n"
        f"{'=' * 40}\n"
        + "\n\n".join(baris_hasil) +
        f"\n{'=' * 40}\n\n"
        f"[PERTANYAAN PENGGUNA]\n{query}\n\n"
        f"Gunakan hasil pencarian di atas untuk menjawab pertanyaan pengguna "
        f"secara ringkas, akurat, dan natural dalam Bahasa Indonesia. "
        f"Jangan menyebut nama sumber atau URL. Langsung sampaikan informasinya."
    )
