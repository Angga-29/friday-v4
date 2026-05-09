#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   setup_termux.sh — Project Friday v4.0.0
#   Auto-setup untuk Termux di Android (Xiaomi Pad 7)
#
#   CARA PAKAI:
#     chmod +x setup_termux.sh
#     bash setup_termux.sh
# ==============================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()    { echo -e "${CYAN}[•] $1${NC}"; }
log_sukses()  { echo -e "${GREEN}[✓] $1${NC}"; }
log_warning() { echo -e "${YELLOW}[!] $1${NC}"; }
log_error()   { echo -e "${RED}[✗] $1${NC}"; }

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║        FRIDAY AI v4.0 — Termux Setup Script          ║"
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
log_info "Install package sistem Termux..."

SYS_PACKAGES=(
    "python"          # Python 3
    "python-pip"      # Package manager Python
    "python-opencv"   # OpenCV untuk Android ARM (WAJIB — pip tidak bisa!)
    "mpv"             # Player audio utama (untuk Edge-TTS)
    "ffmpeg"          # Multimedia tools (fallback audio)
    "portaudio"       # Library audio (wajib untuk PyAudio)
    "libsndfile"      # Library audio support
    "flac"            # WAJIB untuk SpeechRecognition (konversi audio)
    "clang"           # Compiler (dibutuhkan beberapa package Python)
    "cmake"           # Build tools
    "pkg-config"      # Build config tools
    "termux-api"      # Untuk mikrofon & TTS Termux
)

for p in "${SYS_PACKAGES[@]}"; do
    log_info "  Install: $p"
    pkg install -y "$p" 2>/dev/null && log_sukses "  $p OK" || log_warning "  $p gagal (mungkin sudah ada)"
done

log_sukses "Package sistem selesai."

# ── 4. Upgrade pip ────────────────────────────────────────────
log_info "Upgrade pip..."
pip install --upgrade pip --quiet 2>/dev/null

# ── 5. Install Python packages (TANPA opencv) ─────────────────
log_info "Install Python packages..."
log_warning "OpenCV di-skip (sudah diinstall via pkg install python-opencv)"

PY_PACKAGES=(
    "requests>=2.31.0"
    "google-generativeai>=0.8.0"
    "edge-tts>=6.1.0"
    "gTTS>=2.4.0"
    "SpeechRecognition>=3.10.0"
    "ddgs>=0.6.0"
    "colorama>=0.4.6"
    "python-dotenv>=1.0.0"
    "numpy>=1.24.0"
)

for pkg_py in "${PY_PACKAGES[@]}"; do
    log_info "  pip install: $pkg_py"
    pip install "$pkg_py" --quiet 2>/dev/null && \
        log_sukses "  OK: $pkg_py" || \
        log_warning "  Gagal: $pkg_py"
done

# Install PyAudio (perlu portaudio sudah terinstall)
log_info "  pip install: PyAudio (perlu portaudio)"
pip install PyAudio --quiet 2>/dev/null && \
    log_sukses "  OK: PyAudio" || \
    log_warning "  PyAudio gagal — coba: pip install pyaudio"

log_sukses "Python packages selesai."

# ── 6. Siapkan konfigurasi ────────────────────────────────────
log_info "Menyiapkan konfigurasi..."

if [ ! -f "config.py" ]; then
    if [ -f "config.example.py" ]; then
        cp config.example.py config.py
        log_warning "config.py dibuat dari template."
        log_warning "EDIT config.py dan masukkan API key Anda!"
        log_warning "  nano config.py"
    else
        log_error "config.example.py tidak ditemukan! Jalankan dari folder friday-v4/"
    fi
else
    log_sukses "config.py sudah ada."
fi

# PENTING: JANGAN auto-copy .env.example → .env
# File .env akan menimpa config.py via load_dotenv() — kalau berisi
# placeholder ("192.168.x.x", "your_gemini_api_key_here", "NamaMu"),
# semua perbaikan di config.py akan PERCUMA.
# User cukup edit config.py saja (atau jalankan setup_config.sh).
if [ -f ".env" ]; then
    log_warning ".env terdeteksi — akan menimpa config.py!"
    log_warning "Kalau .env berisi placeholder, hapus: rm .env"
fi

# ── 7. Buat folder yang diperlukan ────────────────────────────
log_info "Membuat folder data..."
mkdir -p data/wajah_dikenal

log_sukses "Folder data siap."

# ── 8. Test komponen ──────────────────────────────────────────
log_info "Verifikasi komponen..."
echo ""

check_py() {
    python3 -c "import $1" 2>/dev/null && \
        log_sukses "  Python: $1" || \
        log_warning "  Python: $1 — BELUM TERINSTALL"
}

check_cmd_tool() {
    command -v "$1" &>/dev/null && \
        log_sukses "  Tool: $1" || \
        log_warning "  Tool: $1 — tidak ditemukan"
}

echo "  [ Python Packages ]"
check_py "cv2"
check_py "google.generativeai"
check_py "speech_recognition"
check_py "edge_tts"
check_py "gtts"
check_py "requests"
check_py "colorama"
check_py "dotenv"
check_py "ddgs"

echo ""
echo "  [ System Tools ]"
check_cmd_tool "flac"
check_cmd_tool "mpv"
check_cmd_tool "ffmpeg"
check_cmd_tool "python3"

# ── Selesai ───────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗"
echo "║                  SETUP SELESAI!                      ║"
echo "╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Langkah selanjutnya:${NC}"
echo ""
echo "  1. Edit config.py dan masukkan API key Anda:"
echo "     nano config.py"
echo ""
echo "  2. Set URL IP Webcam (atau biarkan jika mau mode suara saja):"
echo "     URL_KAMERA = \"http://<IP_ANDROID>:8080/shot.jpg\""
echo "     KAMERA_WAJIB = False   ← agar tetap jalan walau kamera gagal"
echo ""
echo "  3. Tambahkan foto wajah untuk pengenalan (opsional):"
echo "     mkdir data/wajah_dikenal/NamaAnda"
echo "     cp foto*.jpg data/wajah_dikenal/NamaAnda/"
echo ""
echo "  4. Jalankan Friday!"
echo "     bash start.sh"
echo "     # atau: python main.py"
echo ""
echo -e "${CYAN}Jika ada error saat pertama jalan:${NC}"
echo "     bash fix_errors.sh"
echo ""
