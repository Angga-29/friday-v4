# ==============================================================
# config.example.py — Project Friday | Template Konfigurasi
# Versi : 3.0.0
# ==============================================================
# CARA PAKAI:
#   1. Salin file ini menjadi config.py
#      cp config.example.py config.py
#   2. Isi nilai yang sesuai (API key, IP kamera, dll.)
#   3. JANGAN upload config.py ke GitHub (sudah ada di .gitignore)
#
# ALTERNATIF (lebih aman — gunakan .env):
#   1. Salin .env.example menjadi .env
#      cp .env.example .env
#   2. Isi .env, lalu biarkan config.py tetap menggunakan os.getenv()
# ==============================================================

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- KAMERA (IP Webcam) ---
# Buka aplikasi IPWebcam di Android → Start server → salin URL yang muncul
# Jika tidak punya IP Webcam, biarkan default dan set KAMERA_WAJIB = False
URL_KAMERA = os.getenv("CAMERA_URL", "http://192.168.x.x:8080/shot.jpg")

# False = Friday tetap jalan walau kamera gagal (mode suara saja)
# True  = Friday berhenti jika kamera tidak tersambung
KAMERA_WAJIB = os.getenv("KAMERA_WAJIB", "false").lower() == "true"

# --- API KEYS ---
# Google Gemini  → https://aistudio.google.com/app/apikey (GRATIS)
API_KEY_GEMINI = os.getenv("GEMINI_API_KEY", "MASUKKAN_GEMINI_API_KEY_DISINI")

# OpenWeatherMap → https://openweathermap.org/api (GRATIS tier tersedia)
API_KEY_CUACA = os.getenv("WEATHER_API_KEY", "MASUKKAN_OPENWEATHER_API_KEY_DISINI")

# NewsAPI        → https://newsapi.org (GRATIS untuk developer)
API_KEY_BERITA = os.getenv("NEWS_API_KEY", "MASUKKAN_NEWS_API_KEY_DISINI")

# --- IDENTITAS ---
NAMA_PENGGUNA = os.getenv("USER_NAME", "NamaMu")

# --- LOKASI CUACA ---
# Format: "NamaKota,KODENEGARA" — contoh: "Jakarta,ID" | "Tokyo,JP"
KOTA_CUACA = os.getenv("WEATHER_CITY", "Jakarta,ID")

# --- OLLAMA (Local AI — fallback saat offline) ---
# Install di Termux: pkg install ollama
# Jalankan server: ollama serve &
# Download model: ollama pull qwen2:1.5b
OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:1.5b")

# --- PERSONA FRIDAY ---
SYSTEM_PROMPT_FRIDAY = f"""
Kamu adalah FRIDAY — AI personal assistant milik {NAMA_PENGGUNA}, persis seperti yang melayani Tony Stark di Iron Man.
Bicara santai dan natural dalam Bahasa Indonesia, boleh selipkan istilah Inggris umum.
Panggil pengguna 'Bos' atau 'Bos {NAMA_PENGGUNA}' — natural, jangan setiap kalimat.
DILARANG markdown: tidak ada *, **, #, ##, backtick.
Maksimal 3 kalimat untuk pertanyaan biasa.
"""
