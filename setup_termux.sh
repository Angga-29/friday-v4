#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   setup_termux.sh — Project Friday v3.0.0
#   Auto-setup untuk Termux di Android (Xiaomi Pad 7)
#
#   CARA PAKAI:
#     chmod +x setup_termux.sh
#     bash setup_termux.sh
# ==============================================================

# set -e dihapus agar error satu package tidak menghentikan seluruh setup

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'   # No Color

log_info()    { echo -e "${CYAN}[•] $1${NC}"; }
log_sukses()  { echo -e "${GREEN}[✓] $1${NC}"; }
log_warning() { echo -e "${YELLOW}[!] $1${NC}"; }
log_error()   { echo -e "${RED}[✗] $1${NC}"; exit 1; }

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║        FRIDAY AI — Termux Setup Script               ║"
echo "║        Platform: Android (Xiaomi Pad 7)              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Izin storage Termux ────────────────────────────────────
log_info "Meminta izin akses storage..."
termux-setup-storage 2>/dev/null || log_warning "Storage sudah diizinkan atau perlu izin manual"

# ── 2. Update package repository ─────────────────────────────
log_info "Update repository Termux..."
pkg update -y 2>/dev/null || log_warning "Update gagal, lanjut..."

# ── 3. Install package sistem ─────────────────────────────────
log_info "Install package sistem..."

PACKAGES=(
    python          # Python 3
    python-pip      # Package manager Python
    mpv             # Player audio (untuk Edge-TTS)
    ffmpeg          # Multimedia tools (fallback audio)
    portaudio       # Library audio (wajib untuk PyAudio)
    libsndfile      # Library audio support
    flac            # WAJIB untuk SpeechRecognition — konversi audio ke FLAC
    clang           # Compiler (dibutuhkan beberapa package Python)
    cmake           # Build tools
    pkg-config      # Build config tools
)

for pkg in "${PACKAGES[@]}"; do
    log_info "  Install: $pkg"
    pkg install -y "$pkg" 2>/dev/null || log_warning "  $pkg gagal, mungkin sudah terinstall"
done

log_sukses "Package sistem selesai."

# ── 4. Upgrade pip ────────────────────────────────────────────
log_info "Upgrade pip..."
pip install --upgrade pip --quiet

# ── 5. Install Python packages ────────────────────────────────
log_info "Install Python packages dari requirements.txt..."

if [ ! -f "requirements.txt" ]; then
    log_error "File requirements.txt tidak ditemukan! Jalankan dari folder friday-v3/"
fi

# Install satu per satu agar error satu package tidak menghentikan semua
while IFS= read -r line; do
    # Skip baris komentar dan kosong
    [[ "$line" =~ ^#.*$ ]] && continue
    [[ -z "$line" ]] && continue

    log_info "  pip install: $line"
    pip install "$line" --quiet 2>/dev/null || log_warning "  Gagal install: $line"
done < requirements.txt

log_sukses "Python packages selesai."

# ── 6. Siapkan konfigurasi ────────────────────────────────────
log_info "Menyiapkan konfigurasi..."

if [ ! -f "config.py" ]; then
    if [ -f "config.example.py" ]; then
        cp config.example.py config.py
        log_warning "config.py dibuat dari template."
        log_warning "EDIT config.py dan masukkan API key Anda!"
    else
        log_error "config.example.py tidak ditemukan!"
    fi
else
    log_sukses "config.py sudah ada."
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    log_warning ".env dibuat dari template. Edit dan isi API key Anda."
fi

# ── 7. Buat folder yang diperlukan ────────────────────────────
log_info "Membuat folder data..."
mkdir -p data/wajah_dikenal
mkdir -p /tmp

log_sukses "Folder data siap."

# ── 8. Test microphone ────────────────────────────────────────
log_info "Cek izin microphone Termux..."
if command -v termux-microphone-record &>/dev/null; then
    log_sukses "Termux API tersedia (microphone)."
else
    log_warning "termux-api tidak terinstall."
    log_warning "Install dari Play Store: Termux:API"
    log_warning "Lalu jalankan: pkg install termux-api"
fi

# ── 9. Test audio player ──────────────────────────────────────
log_info "Cek audio player..."
if command -v mpv &>/dev/null; then
    log_sukses "mpv tersedia (audio player utama)."
elif command -v ffplay &>/dev/null; then
    log_sukses "ffplay tersedia (audio player fallback)."
else
    log_warning "Tidak ada audio player terdeteksi!"
    log_warning "Jalankan: pkg install mpv"
fi

# ── Selesai ───────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗"
echo "║                  SETUP SELESAI!                      ║"
echo "╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Langkah selanjutnya:${NC}"
echo "  1. Edit config.py dan masukkan API key Anda"
echo "     nano config.py"
echo ""
echo "  2. Set URL IP Webcam (IP Android yang menjalankan IPWebcam)"
echo "     URL_KAMERA = \"http://<IP_ANDROID>:8080/shot.jpg\""
echo ""
echo "  3. Tambahkan foto wajah (opsional)"
echo "     mkdir data/wajah_dikenal/NamaAnda"
echo "     cp foto*.jpg data/wajah_dikenal/NamaAnda/"
echo ""
echo "  4. Jalankan Friday!"
echo "     bash start.sh"
echo "     # atau: python main.py"
echo ""
