# ==============================================================
# modules/riset.py — Project Friday v4.0 | Deep Research
# Terinspirasi dari OpenJarvis Research Agent (multi-hop analysis)
# ==============================================================
"""
Riset mendalam = 3 pencarian dengan sudut pandang berbeda,
lalu disintesis oleh Gemini menjadi jawaban komprehensif.

Berbeda dari browsing biasa:
  Browsing  → 1 pencarian → jawab langsung
  Riset     → 3 pencarian → deduplikasi → sintesis mendalam
"""

from modules.browser import cari_web, format_untuk_gemini
from modules.tampilan import tampilkan_status

TRIGGER_WORDS = [
    "riset tentang", "riset mendalam", "penelitian tentang",
    "analisis mendalam", "cari tahu lengkap", "jelaskan secara mendalam",
    "analisis tentang", "telusuri",
]


def perlu_riset(teks: str) -> bool:
    teks_lower = teks.lower()
    return any(t in teks_lower for t in TRIGGER_WORDS)


def _ekstrak_topik(teks: str) -> str:
    """Bersihkan trigger words dari input untuk mendapat topik inti."""
    topik = teks.lower()
    for trigger in sorted(TRIGGER_WORDS, key=len, reverse=True):
        topik = topik.replace(trigger, "").strip()
    return topik.strip(" ,.!?") or teks


def riset_mendalam(teks_asli: str, ai) -> str:
    """
    3-step deep research terinspirasi OpenJarvis Research Agent.

    Langkah:
      1. Pencarian topik utama
      2. Pencarian detail/penjelasan lengkap
      3. Pencarian perkembangan terbaru
      → Deduplikasi → Sintesis via Gemini
    """
    topik = _ekstrak_topik(teks_asli)
    tampilkan_status(f"Riset mendalam: '{topik}'", "browsing")

    queries = [
        topik,
        f"{topik} penjelasan lengkap",
        f"{topik} terbaru",
    ]

    semua_hasil = []
    for i, q in enumerate(queries, 1):
        tampilkan_status(f"Pencarian {i}/3: '{q}'", "browsing")
        semua_hasil.extend(cari_web(q))

    # Deduplikasi berdasarkan URL
    seen_urls: set = set()
    unik = []
    for r in semua_hasil:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unik.append(r)
        elif not url:
            unik.append(r)

    tampilkan_status(f"{len(unik)} sumber unik ditemukan. Mensintesis...", "sukses")

    konteks = format_untuk_gemini(topik, unik[:9])
    prompt = (
        f"{konteks}\n\n"
        f"[INSTRUKSI RISET MENDALAM]\n"
        f"Topik: {topik}\n"
        f"Buat analisis komprehensif yang bisa didengarkan: "
        f"mulai dengan fakta terpenting, lanjutkan dengan 3 poin detail kunci, "
        f"akhiri dengan kesimpulan singkat. "
        f"Gunakan bahasa natural tanpa bullet point. Maksimal 6 kalimat."
    )

    # Gunakan tanya_riset() yang punya token limit lebih besar
    if hasattr(ai, 'tanya_riset'):
        return ai.tanya_riset(prompt)
    return ai.tanya_dengan_web(topik, prompt)
