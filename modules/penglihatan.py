# ==============================================================
# modules/penglihatan.py — Project Friday | Gemini Vision
# Versi : 1.0.1
# Friday bisa "melihat" dan mendeskripsikan apa yang ada di kamera
# ==============================================================
"""
Cara kerja:
1. Frame dari kamera diambil
2. Frame di-encode menjadi JPEG bytes
3. Dikirim ke Gemini Vision API beserta pertanyaan
4. Gemini menjawab dengan deskripsi visual

Kata kunci pemicu: "lihat", "apa yang kamu lihat", "deskripsikan",
                   "ada apa", "siapa di depan kamera"
"""

import cv2
import google.generativeai as genai
from modules.tampilan import tampilkan_status

# Kata kunci yang memicu mode penglihatan
KATA_KUNCI_VISION = [
    "lihat", "melihat", "kamu lihat", "apa yang ada",
    "deskripsikan", "deskripsi", "gambarkan", "perhatikan",
    "siapa di depan", "ada apa di", "ada siapa",
    "tunjukkan", "perlihatkan"
]

# Singleton model — dikonfigurasi sekali saat pertama dipakai
_vision_model = None
_vision_api_key = None


def _dapatkan_model(api_key: str):
    """Lazy-init Gemini Vision model — konfigurasi hanya sekali."""
    global _vision_model, _vision_api_key
    if _vision_model is None or api_key != _vision_api_key:
        genai.configure(api_key=api_key)
        _vision_model = genai.GenerativeModel("gemini-2.5-flash")
        _vision_api_key = api_key
    return _vision_model


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
    Kirim frame ke Gemini Vision untuk dideskripsikan.

    Args:
        frame     : Frame OpenCV (BGR numpy array)
        pertanyaan: Pertanyaan user
        api_key   : Gemini API key

    Returns:
        Deskripsi dalam Bahasa Indonesia (maks 3 kalimat).
    """
    if frame is None:
        return "Saya tidak bisa melihat — kamera tidak merespons."

    tampilkan_status("Mengirim gambar ke Gemini Vision...", "ai")

    try:
        img_bytes = frame_ke_bytes(frame)
        if img_bytes is None:
            return "Gagal memproses gambar dari kamera."

        model = _dapatkan_model(api_key)

        prompt = (
            f"Kamu adalah FRIDAY, asisten AI. Lihat gambar dari kamera ini "
            f"dan jawab pertanyaan berikut secara natural dan ringkas dalam "
            f"Bahasa Indonesia (maksimal 3 kalimat). "
            f"Tidak perlu pakai markdown atau karakter khusus.\n\n"
            f"PERTANYAAN: {pertanyaan}"
        )

        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": img_bytes}
        ])

        teks = response.text.strip()
        teks = teks.replace("**", "").replace("*", "")
        teks = teks.replace("##", "").replace("#", "").replace("`", "")
        return teks

    except Exception as e:
        tampilkan_status(f"Error Vision: {e}", "error")
        return "Maaf, saya tidak bisa menganalisis gambar saat ini."
