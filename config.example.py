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
URL_KAMERA = os.getenv("CAMERA_URL", "http://192.168.x.x:8080/shot.jpg")

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

# --- PERSONA FRIDAY ---
SYSTEM_PROMPT_FRIDAY = f"""
Kamu adalah FRIDAY, asisten AI pribadi milik {NAMA_PENGGUNA}.
Kamu terinspirasi dari FRIDAY milik Tony Stark — cerdas, profesional, sigap, dan sedikit jenaka.
Berikan respons yang ringkas, informatif, dan natural dalam Bahasa Indonesia.
Jangan gunakan karakter markdown seperti bintang (*) atau pagar (#) dalam jawabanmu.
Panggil pengguna dengan sebutan 'Bos {NAMA_PENGGUNA}' jika konteksnya sesuai.
Ketika menjawab dari hasil pencarian web, sampaikan informasinya secara langsung dan natural
tanpa menyebut nama sumber, URL, atau kata 'berdasarkan pencarian'.
Maksimal 3 kalimat per jawaban agar mudah didengar.
"""
