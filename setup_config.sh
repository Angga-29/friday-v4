#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   setup_config.sh — Friday AI v4.0 | Setup Konfigurasi
#   Script interaktif untuk mengisi config.py dengan benar
#
#   CARA PAKAI:
#     bash setup_config.sh
# ==============================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[•] $1${NC}"; }
log_ok()    { echo -e "${GREEN}[✓] $1${NC}"; }
log_warn()  { echo -e "${YELLOW}[!] $1${NC}"; }
log_tanya() { echo -e "${BOLD}${CYAN}  → $1${NC}"; }

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   FRIDAY AI v4.0 — Setup Konfigurasi                ║"
echo "║   Isi data di bawah ini (tekan Enter untuk default)  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Nama Pengguna ──────────────────────────────────────────
echo ""
log_info "NAMA PENGGUNA"
echo "  Friday akan menyapa Anda dengan nama ini."
echo "  Contoh: Angga, Budi, Sari"
echo ""
log_tanya "Nama Anda: "
read -r NAMA_INPUT
NAMA_INPUT="${NAMA_INPUT:-Angga}"
log_ok "Nama: $NAMA_INPUT"

# ── 2. URL Kamera ─────────────────────────────────────────────
echo ""
log_info "URL KAMERA (IP Webcam)"
echo ""
echo "  Opsi:"
echo "  [A] IP Webcam di HP/tablet yang SAMA dengan Friday"
echo "      → URL: http://127.0.0.1:8080/shot.jpg"
echo ""
echo "  [B] IP Webcam di HP/tablet BERBEDA (HP lain di WiFi sama)"
echo "      → Cari IP di aplikasi IPWebcam (contoh: 10.196.238.137)"
echo ""
echo "  [C] Tidak pakai kamera (mode suara saja)"
echo ""
log_tanya "Pilih opsi [A/B/C]: "
read -r PILIH_KAMERA

case "${PILIH_KAMERA^^}" in
    A)
        URL_KAMERA="http://127.0.0.1:8080/shot.jpg"
        KAMERA_WAJIB="false"
        log_ok "Kamera: localhost (127.0.0.1:8080)"
        ;;
    B)
        log_tanya "Masukkan IP dari aplikasi IPWebcam (contoh: 10.196.238.137): "
        read -r IP_INPUT
        URL_KAMERA="http://${IP_INPUT}:8080/shot.jpg"
        KAMERA_WAJIB="false"
        log_ok "Kamera: $URL_KAMERA"
        ;;
    *)
        URL_KAMERA="http://127.0.0.1:8080/shot.jpg"
        KAMERA_WAJIB="false"
        log_warn "Mode tanpa kamera — KAMERA_WAJIB=false"
        ;;
esac

# ── 3. Gemini API Key ─────────────────────────────────────────
echo ""
log_info "GEMINI API KEY"
echo "  Dapatkan GRATIS di: https://aistudio.google.com/app/apikey"
echo ""
log_tanya "Gemini API Key (Enter = pakai yang sudah ada): "
read -r GEMINI_INPUT

# ── 4. OpenWeatherMap API Key ─────────────────────────────────
echo ""
log_info "OPENWEATHERMAP API KEY (untuk info cuaca)"
echo "  Daftar GRATIS di: https://openweathermap.org/api"
echo "  Pilih 'Current Weather Data' yang GRATIS"
echo ""
log_warn "API key lama tidak valid — perlu key baru!"
log_tanya "OpenWeatherMap API Key (Enter = skip/abaikan cuaca): "
read -r WEATHER_INPUT

# ── 5. NewsAPI Key ────────────────────────────────────────────
echo ""
log_info "NEWSAPI KEY (untuk berita terkini)"
echo "  Daftar GRATIS di: https://newsapi.org"
echo ""
log_warn "API key lama tidak valid — perlu key baru!"
log_tanya "NewsAPI Key (Enter = skip/abaikan berita): "
read -r NEWS_INPUT

# ── 6. Kota Cuaca ─────────────────────────────────────────────
echo ""
log_info "LOKASI CUACA"
echo "  Format: NamaKota,KODE_NEGARA"
echo "  Contoh: Jakarta,ID | Bandung,ID | Surabaya,ID"
echo ""
log_tanya "Kota Anda [default: Jakarta,ID]: "
read -r KOTA_INPUT
KOTA_INPUT="${KOTA_INPUT:-Jakarta,ID}"

# ── Tulis config.py ───────────────────────────────────────────
echo ""
log_info "Menulis config.py..."

# Gunakan nilai yang diisi, atau fallback ke nilai lama di config.py
GEMINI_FINAL="${GEMINI_INPUT}"
if [ -z "$GEMINI_FINAL" ] && [ -f "config.py" ]; then
    GEMINI_FINAL=$(python3 -c "import config; print(config.API_KEY_GEMINI)" 2>/dev/null || echo "your_gemini_api_key_here")
fi
GEMINI_FINAL="${GEMINI_FINAL:-your_gemini_api_key_here}"

WEATHER_FINAL="${WEATHER_INPUT:-your_openweathermap_key_here}"
NEWS_FINAL="${NEWS_INPUT:-your_newsapi_key_here}"

cat > config.py << CONFIGEOF
# ==============================================================
# config.py — Project Friday v4.0 | Konfigurasi Utama
# Di-generate oleh setup_config.sh
# ==============================================================

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- KAMERA ---
URL_KAMERA   = os.getenv("CAMERA_URL", "${URL_KAMERA}")
KAMERA_WAJIB = os.getenv("KAMERA_WAJIB", "${KAMERA_WAJIB}").lower() == "true"

# --- API KEYS ---
API_KEY_GEMINI = os.getenv("GEMINI_API_KEY", "${GEMINI_FINAL}")
API_KEY_CUACA  = os.getenv("WEATHER_API_KEY", "${WEATHER_FINAL}")
API_KEY_BERITA = os.getenv("NEWS_API_KEY", "${NEWS_FINAL}")

# --- IDENTITAS ---
NAMA_PENGGUNA = os.getenv("USER_NAME", "${NAMA_INPUT}")

# --- LOKASI CUACA ---
KOTA_CUACA = os.getenv("WEATHER_CITY", "${KOTA_INPUT}")

# --- PERSONA FRIDAY ---
SYSTEM_PROMPT_FRIDAY = f"""
Kamu adalah FRIDAY, asisten AI pribadi milik {NAMA_INPUT}.
Kamu terinspirasi dari FRIDAY milik Tony Stark — cerdas, profesional, sigap, dan sedikit jenaka.
Berikan respons yang ringkas, informatif, dan natural dalam Bahasa Indonesia.
Jangan gunakan karakter markdown seperti bintang (*) atau pagar (#) dalam jawabanmu.
Panggil pengguna dengan sebutan 'Bos {NAMA_INPUT}' jika konteksnya sesuai.
Ketika menjawab dari hasil pencarian web, sampaikan informasinya secara langsung dan natural
tanpa menyebut nama sumber, URL, atau kata 'berdasarkan pencarian'.
Maksimal 3 kalimat per jawaban agar mudah didengar.
"""
CONFIGEOF

log_ok "config.py berhasil dibuat!"

# ── Fix suara: install mpv ────────────────────────────────────
echo ""
log_info "Mengecek audio player (mpv)..."
if ! command -v mpv &>/dev/null; then
    log_warn "mpv tidak ditemukan — install sekarang..."
    pkg install -y mpv 2>/dev/null
    command -v mpv &>/dev/null && log_ok "mpv berhasil diinstall!" || \
        log_warn "mpv gagal — coba manual: pkg install mpv"
else
    log_ok "mpv sudah tersedia."
fi

# ── Verifikasi ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗"
echo "║             KONFIGURASI SELESAI!                     ║"
echo "╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Ringkasan config.py:${NC}"
echo "  Nama        : $NAMA_INPUT"
echo "  Kamera URL  : $URL_KAMERA"
echo "  Kota Cuaca  : $KOTA_INPUT"
echo ""

if [ "$WEATHER_FINAL" = "your_openweathermap_key_here" ]; then
    echo -e "${YELLOW}  [!] OpenWeatherMap key belum diisi${NC}"
    echo "      Daftar di: https://openweathermap.org/api"
fi
if [ "$NEWS_FINAL" = "your_newsapi_key_here" ]; then
    echo -e "${YELLOW}  [!] NewsAPI key belum diisi${NC}"
    echo "      Daftar di: https://newsapi.org"
fi

echo ""
echo -e "${GREEN}Sekarang jalankan Friday:${NC}"
echo ""
echo -e "  ${CYAN}python main.py${NC}"
echo ""
