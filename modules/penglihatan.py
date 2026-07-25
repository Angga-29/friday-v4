# ==============================================================
# modules/penglihatan.py — Project Friday | Claude Vision
# Versi : 2.0.0 — Pindah dari Gemini Vision ke Claude Vision
# Friday bisa "melihat" dan mendeskripsikan apa yang ada di kamera
# ==============================================================
"""
Cara kerja:
1. Frame dari kamera diambil
2. Frame di-encode menjadi JPEG bytes lalu base64
3. Dikirim ke Claude (Anthropic) beserta pertanyaan
4. Claude menjawab dengan deskripsi visual

Kata kunci pemicu: "lihat", "apa yang kamu lihat", "deskripsikan",
                   "ada apa", "siapa di depan kamera"
"""

import base64
import cv2
from modules.tampilan import tampilkan_status

try:
    import anthropic
    _SDK_TERSEDIA = True
except ImportError:
    anthropic = None
    _SDK_TERSEDIA = False

MODEL_VISION = "claude-sonnet-5"

# Kata kunci yang memicu mode penglihatan
KATA_KUNCI_VISION = [
    "lihat", "melihat", "kamu lihat", "apa yang ada",
    "deskripsikan", "deskripsi", "gambarkan", "perhatikan",
    "siapa di depan", "ada apa di", "ada siapa",
    "tunjukkan", "perlihatkan"
]

# Singleton client — dibuat sekali saat pertama dipakai
_client       = None
_client_key   = None


def _dapatkan_client(api_key: str):
    """Lazy-init Anthropic client — dibuat hanya sekali."""
    global _client, _client_key
    if _client is None or api_key != _client_key:
        _client     = anthropic.Anthropic(api_key=api_key)
        _client_key = api_key
    return _client


def perlu_penglihatan(teks: str) -> bool:
    """Apakah pertanyaan butuh akses kamera (vision)?"""
    teks_lower = teks.lower()
    return any(kata in teks_lower for kata in KATA_KUNCI_VISION)


def frame_ke_bytes(frame) -> bytes | None:
    """Encode frame OpenCV ke JPEG bytes (kualitas 85%)."""
    success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        return None
    return buffer.tobytes()


def deskripsikan_pemandangan(frame, pertanyaan: str, api_key: str) -> str:
    """
    Kirim frame ke Claude Vision untuk dideskripsikan.

    Args:
        frame     : Frame OpenCV (BGR numpy array)
        pertanyaan: Pertanyaan user
        api_key   : Claude (Anthropic) API key

    Returns:
        Deskripsi dalam Bahasa Indonesia (maks 3 kalimat).
    """
    if frame is None:
        return "Saya tidak bisa melihat — kamera tidak merespons."

    if not _SDK_TERSEDIA:
        return "Package 'anthropic' tidak terinstall. Jalankan: pip install anthropic"

    tampilkan_status("Mengirim gambar ke Claude Vision...", "ai")

    try:
        img_bytes = frame_ke_bytes(frame)
        if img_bytes is None:
            return "Gagal memproses gambar dari kamera."

        img_b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
        client  = _dapatkan_client(api_key)

        prompt = (
            f"Kamu adalah FRIDAY, asisten AI. Lihat gambar dari kamera ini "
            f"dan jawab pertanyaan berikut secara natural dan ringkas dalam "
            f"Bahasa Indonesia (maksimal 3 kalimat). "
            f"Tidak perlu pakai markdown atau karakter khusus.\n\n"
            f"PERTANYAAN: {pertanyaan}"
        )

        resp = client.messages.create(
            model=MODEL_VISION,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )

        teks = "".join(blok.text for blok in resp.content if blok.type == "text").strip()
        teks = teks.replace("**", "").replace("*", "")
        teks = teks.replace("##", "").replace("#", "").replace("`", "")
        return teks

    except Exception as e:
        tampilkan_status(f"Error Vision: {e}", "error")
        return "Maaf, saya tidak bisa menganalisis gambar saat ini."
