#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   setup_config.sh — Friday AI v4.0 | Setup Konfigurasi
#   - Enter = pakai nilai yang sudah ada di config.py
#   - Tidak akan reset nilai lama jika dikosongkan
#
#   CARA PAKAI:
#     bash setup_config.sh
# ==============================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

log_info()  { echo -e "${CYAN}[•] $1${NC}"; }
log_ok()    { echo -e "${GREEN}[✓] $1${NC}"; }
log_warn()  { echo -e "${YELLOW}[!] $1${NC}"; }
log_tanya() { echo -e "${BOLD}${CYAN}  → $1${NC}"; }

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   FRIDAY AI v4.0 — Setup Konfigurasi                ║"
echo "║   Tekan Enter untuk memakai nilai yang sudah ada     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Baca nilai lama dari config.py (jika ada) ─────────────────
OLD_NAMA="Angga"
OLD_KAMERA="http://127.0.0.1:8080/shot.jpg"
OLD_GEMINI="your_gemini_api_key_here"
OLD_WEATHER="your_openweathermap_key_here"
OLD_NEWS="your_newsapi_key_here"
OLD_KOTA="Jakarta,ID"

if [ -f "config.py" ]; then
    _val=$(python3 -c "import sys; sys.path.insert(0,'.'); import config; print(config.NAMA_PENGGUNA)" 2>/dev/null)
    [ -n "$_val" ] && OLD_NAMA="$_val"

    _val=$(python3 -c "import sys; sys.path.insert(0,'.'); import config; print(config.URL_KAMERA)" 2>/dev/null)
    [ -n "$_val" ] && OLD_KAMERA="$_val"

    _val=$(python3 -c "import sys; sys.path.insert(0,'.'); import config; print(config.API_KEY_GEMINI)" 2>/dev/null)
    [ -n "$_val" ] && OLD_GEMINI="$_val"

    _val=$(python3 -c "import sys; sys.path.insert(0,'.'); import config; print(config.API_KEY_CUACA)" 2>/dev/null)
    [ -n "$_val" ] && OLD_WEATHER="$_val"

    _val=$(python3 -c "import sys; sys.path.insert(0,'.'); import config; print(config.API_KEY_BERITA)" 2>/dev/null)
    [ -n "$_val" ] && OLD_NEWS="$_val"

    _val=$(python3 -c "import sys; sys.path.insert(0,'.'); import config; print(config.KOTA_CUACA)" 2>/dev/null)
    [ -n "$_val" ] && OLD_KOTA="$_val"
fi

# ── 1. Nama Pengguna ──────────────────────────────────────────
echo ""
log_info "NAMA PENGGUNA"
echo "  Friday akan menyapa: 'Halo, Bos [nama]'"
log_tanya "Nama Anda [saat ini: ${OLD_NAMA}]: "
read -r INPUT
NAMA="${INPUT:-$OLD_NAMA}"
log_ok "Nama: $NAMA"

# ── 2. URL Kamera ─────────────────────────────────────────────
echo ""
log_info "URL KAMERA (IP Webcam)"
echo ""
echo "  [A] IP Webcam di tablet yang SAMA dengan Friday"
echo "      → Otomatis pakai: http://127.0.0.1:8080/shot.jpg"
echo ""
echo "  [B] IP Webcam di HP/tablet LAIN di WiFi yang sama"
echo "      → Anda isi IP-nya sendiri"
echo ""
echo "  [C] Tidak pakai kamera (mode suara saja)"
echo ""
echo "  [D] Pakai URL yang sudah ada: ${OLD_KAMERA}"
echo ""
log_tanya "Pilih [A/B/C/D, default: D]: "
read -r PILIH_KAMERA

case "${PILIH_KAMERA^^}" in
    A)
        URL_KAMERA="http://127.0.0.1:8080/shot.jpg"
        log_ok "Kamera: localhost (tidak perlu input IP manual)"
        ;;
    B)
        log_tanya "Masukkan IP dari aplikasi IPWebcam (contoh: 10.196.238.137): "
        read -r IP_INPUT
        URL_KAMERA="http://${IP_INPUT}:8080/shot.jpg"
        log_ok "Kamera: $URL_KAMERA"
        ;;
    C)
        URL_KAMERA="http://127.0.0.1:8080/shot.jpg"
        log_warn "Mode tanpa kamera aktif (KAMERA_WAJIB=false)"
        ;;
    *)
        URL_KAMERA="$OLD_KAMERA"
        log_ok "Kamera: pakai nilai lama → $URL_KAMERA"
        ;;
esac

# ── 3. Gemini API Key ─────────────────────────────────────────
echo ""
log_info "GEMINI API KEY"
echo "  Dapatkan GRATIS di: https://aistudio.google.com/app/apikey"
echo "  (Enter = pakai key yang sudah ada)"
log_tanya "Gemini API Key: "
read -r INPUT
GEMINI="${INPUT:-$OLD_GEMINI}"
# Sensor tampilan
if [ ${#GEMINI} -gt 8 ]; then
    TAMPIL_GEMINI="${GEMINI:0:6}...${GEMINI: -4}"
else
    TAMPIL_GEMINI="$GEMINI"
fi
log_ok "Gemini key: $TAMPIL_GEMINI"

# ── 4. OpenWeatherMap API Key ─────────────────────────────────
echo ""
log_info "OPENWEATHERMAP API KEY (cuaca)"
echo "  Daftar GRATIS: https://openweathermap.org/api"
echo "  Pilih 'Current Weather Data' → copy API key"
echo "  (Enter = pakai key yang sudah ada)"
[ "$OLD_WEATHER" = "your_openweathermap_key_here" ] && \
    log_warn "Belum ada key — isi untuk mengaktifkan info cuaca"
log_tanya "OpenWeatherMap Key: "
read -r INPUT
WEATHER="${INPUT:-$OLD_WEATHER}"
log_ok "Weather key: ${WEATHER:0:6}..."

# ── 5. NewsAPI Key ────────────────────────────────────────────
echo ""
log_info "NEWSAPI KEY (berita)"
echo "  Daftar GRATIS: https://newsapi.org → Register → copy key"
echo "  (Enter = pakai key yang sudah ada)"
[ "$OLD_NEWS" = "your_newsapi_key_here" ] && \
    log_warn "Belum ada key — isi untuk mengaktifkan berita"
log_tanya "NewsAPI Key: "
read -r INPUT
NEWS="${INPUT:-$OLD_NEWS}"
log_ok "News key: ${NEWS:0:6}..."

# ── 6. Kota Cuaca ─────────────────────────────────────────────
echo ""
log_info "LOKASI CUACA"
echo "  Format: NamaKota,KODE — contoh: Jakarta,ID | Bandung,ID"
log_tanya "Kota Anda [saat ini: ${OLD_KOTA}]: "
read -r INPUT
KOTA="${INPUT:-$OLD_KOTA}"
log_ok "Kota: $KOTA"

# ── Tulis config.py ───────────────────────────────────────────
echo ""
log_info "Menulis config.py..."

# Tulis file — gunakan {NAMA_PENGGUNA} sebagai Python variable di f-string
# BUKAN {NAMA} agar tidak dicoba-evaluasi sebagai bash variable
cat > config.py << CONFIGEOF
# ==============================================================
# config.py — Project Friday v4.0
# Di-generate oleh setup_config.sh — $(date)
# ==============================================================

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- KAMERA ---
URL_KAMERA   = os.getenv("CAMERA_URL", "${URL_KAMERA}")
KAMERA_WAJIB = os.getenv("KAMERA_WAJIB", "false").lower() == "true"

# --- API KEYS ---
API_KEY_GEMINI = os.getenv("GEMINI_API_KEY", "${GEMINI}")
API_KEY_CUACA  = os.getenv("WEATHER_API_KEY", "${WEATHER}")
API_KEY_BERITA = os.getenv("NEWS_API_KEY", "${NEWS}")

# --- IDENTITAS ---
NAMA_PENGGUNA = os.getenv("USER_NAME", "${NAMA}")

# --- LOKASI CUACA ---
KOTA_CUACA = os.getenv("WEATHER_CITY", "${KOTA}")

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
CONFIGEOF

# Cek hasil — pastikan tidak ada NAMA_INPUT yang tersisa
if grep -q "NAMA_INPUT" config.py 2>/dev/null; then
    log_warn "Terdeteksi sisa variabel lama, memperbaiki..."
    sed -i "s/{NAMA_INPUT}/$NAMA/g" config.py
fi

log_ok "config.py berhasil dibuat!"

# ── Cek dan install mpv ───────────────────────────────────────
echo ""
log_info "Mengecek audio player (mpv)..."
if ! command -v mpv &>/dev/null; then
    log_warn "mpv tidak ada — install sekarang..."
    pkg install -y mpv 2>/dev/null
    command -v mpv &>/dev/null && log_ok "mpv berhasil diinstall!" || \
        log_warn "mpv gagal — coba manual: pkg install mpv"
else
    log_ok "mpv sudah tersedia."
fi

# ── Ringkasan ─────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗"
echo "║             KONFIGURASI SELESAI!                     ║"
echo "╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Nama       : $NAMA"
echo "  Kamera URL : $URL_KAMERA"
echo "  Kota Cuaca : $KOTA"
echo ""

[ "$WEATHER" = "your_openweathermap_key_here" ] && \
    echo -e "${YELLOW}  [!] OpenWeatherMap key belum diisi → cuaca tidak aktif${NC}"
[ "$NEWS" = "your_newsapi_key_here" ] && \
    echo -e "${YELLOW}  [!] NewsAPI key belum diisi → berita tidak aktif${NC}"

echo ""
echo -e "${GREEN}Jalankan Friday:${NC}"
echo ""
echo -e "  ${CYAN}python main.py${NC}"
echo ""
