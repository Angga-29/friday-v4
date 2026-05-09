#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   fix_errors.sh — Friday AI Error Fixer
#   Jalankan ini untuk mengatasi 2 error yang muncul:
#   1. No module named 'edge_tts'
#   2. FLAC conversion utility not available
#
#   CARA PAKAI (di Termux, dalam folder friday-v3/):
#     bash fix_errors.sh
# ==============================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()   { echo -e "${CYAN}[•] $1${NC}"; }
log_ok()     { echo -e "${GREEN}[✓] $1${NC}"; }
log_warn()   { echo -e "${YELLOW}[!] $1${NC}"; }
log_error()  { echo -e "${RED}[✗] $1${NC}"; }

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║     FRIDAY AI — Error Fixer Script                   ║"
echo "║     Fix: edge_tts  +  FLAC  +  SpeechRecognition     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── FIX 1: Install FLAC ───────────────────────────────────────
echo ""
log_info "FIX 1: Install FLAC (dibutuhkan oleh SpeechRecognition)"
log_info "Error: 'FLAC conversion utility not available'"
echo ""

pkg install -y flac 2>&1
if command -v flac &>/dev/null; then
    log_ok "FLAC berhasil diinstall: $(flac --version 2>/dev/null | head -1)"
else
    log_error "FLAC gagal install. Coba manual: pkg install flac"
fi

# ── FIX 2: Install edge-tts ───────────────────────────────────
echo ""
log_info "FIX 2: Install edge-tts (Microsoft TTS Neural)"
log_info "Error: 'No module named edge_tts'"
echo ""

pip install edge-tts --upgrade 2>&1
if python3 -c "import edge_tts; print('edge_tts version:', edge_tts.__version__)" 2>/dev/null; then
    log_ok "edge-tts berhasil diinstall!"
else
    log_warn "edge-tts gagal — Friday akan pakai Termux TTS sebagai fallback (masih bisa bicara)"
fi

# ── FIX 3: Install ddgs (pengganti duckduckgo_search) ─────────
echo ""
log_info "FIX 3: Install ddgs (DuckDuckGo — package baru)"
log_info "Warning: 'duckduckgo_search has been renamed to ddgs'"
echo ""

pip install ddgs --upgrade --quiet 2>&1 | tail -3
if python3 -c "from ddgs import DDGS; print('ddgs ok')" 2>/dev/null; then
    log_ok "ddgs berhasil diinstall!"
else
    log_warn "ddgs gagal, coba fallback: pip install duckduckgo-search"
    pip install duckduckgo-search --upgrade --quiet 2>/dev/null
fi

# ── FIX 4: Pastikan SpeechRecognition lengkap ─────────────────
echo ""
log_info "FIX 4: Pastikan SpeechRecognition + PyAudio lengkap"
echo ""

pip install SpeechRecognition --upgrade --quiet 2>&1 | tail -3
pip install pyaudio --quiet 2>&1 | tail -3

if python3 -c "import speech_recognition; print('SpeechRecognition ok')" 2>/dev/null; then
    log_ok "SpeechRecognition siap."
else
    log_warn "SpeechRecognition bermasalah. Coba: pkg install portaudio && pip install pyaudio"
fi

# ── FIX 4: Install python-dotenv (untuk config .env) ──────────
echo ""
log_info "FIX 4: Pastikan python-dotenv tersedia"
pip install python-dotenv --quiet 2>/dev/null
log_ok "python-dotenv siap."

# ── Verifikasi Akhir ──────────────────────────────────────────
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
log_info "Verifikasi semua komponen..."
echo ""

check_module() {
    local name=$1
    local import_name=$2
    if python3 -c "import ${import_name}" 2>/dev/null; then
        log_ok "  ${name}"
    else
        log_error "  ${name} — BELUM TERINSTALL"
    fi
}

check_cmd() {
    local name=$1
    local cmd=$2
    if command -v "$cmd" &>/dev/null; then
        log_ok "  ${name}"
    else
        log_error "  ${name} — TIDAK DITEMUKAN"
    fi
}

echo "  [ Python Packages ]"
check_module "edge-tts"           "edge_tts"
check_module "SpeechRecognition"  "speech_recognition"
check_module "google-generativeai" "google.generativeai"
check_module "opencv-contrib"     "cv2"
check_module "numpy"              "numpy"
check_module "requests"           "requests"
check_module "colorama"           "colorama"
check_module "python-dotenv"      "dotenv"
check_module "ddgs"               "ddgs"

echo ""
echo "  [ System Tools ]"
check_cmd "FLAC"  "flac"
check_cmd "mpv"   "mpv"
check_cmd "ffmpeg" "ffmpeg"
check_cmd "python3" "python3"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Fix selesai! Sekarang jalankan Friday lagi:${NC}"
echo ""
echo -e "  ${CYAN}bash start.sh${NC}"
echo -e "  ${CYAN}# atau: python main.py${NC}"
echo ""
echo -e "${YELLOW}Catatan:${NC}"
echo "  • Jika wake word masih error FLAC → restart Termux dulu, lalu coba lagi"
echo "  • Edge-TTS butuh koneksi internet — Termux TTS aktif jika offline"
echo ""
