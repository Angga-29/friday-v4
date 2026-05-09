#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   fix_errors.sh — Friday AI v4.0 | Error Fixer
#
#   Mengatasi error umum saat menjalankan Friday di Termux:
#   1. OpenCV / cv2 tidak ditemukan
#   2. FLAC conversion utility not available
#   3. No module named 'edge_tts'
#   4. Gemini AI error (API key / model)
#   5. PyAudio / mikrofon tidak bisa dibuka
#
#   CARA PAKAI:
#     bash fix_errors.sh
# ==============================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[•] $1${NC}"; }
log_ok()    { echo -e "${GREEN}[✓] $1${NC}"; }
log_warn()  { echo -e "${YELLOW}[!] $1${NC}"; }
log_error() { echo -e "${RED}[✗] $1${NC}"; }

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   FRIDAY AI v4.0 — Error Fixer Script               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── FIX 1: OpenCV ─────────────────────────────────────────────
echo ""
log_info "FIX 1: OpenCV (cv2)"
log_info "Error: 'No module named cv2' atau 'ImportError: libopencv'"
echo ""

if python3 -c "import cv2" 2>/dev/null; then
    log_ok "cv2 sudah tersedia. (versi: $(python3 -c 'import cv2; print(cv2.__version__)' 2>/dev/null))"
else
    log_warn "cv2 tidak ditemukan — install via pkg (BUKAN pip)..."
    pkg install -y python-opencv 2>&1 | tail -5

    if python3 -c "import cv2" 2>/dev/null; then
        log_ok "OpenCV berhasil diinstall!"
    else
        log_error "OpenCV gagal. Coba manual:"
        log_error "  pkg install python-opencv"
        log_warn  "Friday tetap bisa jalan tanpa kamera (mode suara saja)."
    fi
fi

# ── FIX 2: FLAC ───────────────────────────────────────────────
echo ""
log_info "FIX 2: FLAC (dibutuhkan SpeechRecognition)"
log_info "Error: 'FLAC conversion utility not available'"
echo ""

if command -v flac &>/dev/null; then
    log_ok "FLAC sudah terinstall: $(flac --version 2>/dev/null | head -1)"
else
    pkg install -y flac 2>&1 | tail -3
    command -v flac &>/dev/null && log_ok "FLAC berhasil diinstall!" || \
        log_error "FLAC gagal. Coba: pkg install flac"
fi

# ── FIX 3: edge-tts ───────────────────────────────────────────
echo ""
log_info "FIX 3: edge-tts (Microsoft TTS Neural)"
log_info "Error: 'No module named edge_tts'"
echo ""

pip install edge-tts --upgrade --quiet 2>/dev/null
if python3 -c "import edge_tts" 2>/dev/null; then
    log_ok "edge-tts OK (versi: $(python3 -c 'import edge_tts; print(edge_tts.__version__)' 2>/dev/null))"
else
    log_warn "edge-tts gagal — Friday akan pakai Termux TTS sebagai fallback"
fi

# ── FIX 4: google-generativeai ────────────────────────────────
echo ""
log_info "FIX 4: Google Gemini SDK"
log_info "Error: 'No module named google.generativeai' atau model error"
echo ""

pip install "google-generativeai>=0.8.0" --upgrade --quiet 2>/dev/null
if python3 -c "import google.generativeai" 2>/dev/null; then
    VER=$(python3 -c "import google.generativeai as g; print(g.__version__)" 2>/dev/null)
    log_ok "google-generativeai OK (versi: $VER)"
else
    log_warn "google-generativeai gagal, coba google-genai (SDK baru)..."
    pip install "google-genai" --upgrade --quiet 2>/dev/null
    python3 -c "from google import genai" 2>/dev/null && \
        log_ok "google-genai OK" || \
        log_error "Gemini SDK gagal. Cek koneksi internet."
fi

# ── FIX 5: SpeechRecognition + PyAudio ────────────────────────
echo ""
log_info "FIX 5: SpeechRecognition + PyAudio"
log_info "Error: 'No module named speech_recognition' / OSError mikrofon"
echo ""

# portaudio dulu
pkg install -y portaudio 2>/dev/null | tail -2

pip install SpeechRecognition --upgrade --quiet 2>/dev/null
pip install PyAudio --quiet 2>/dev/null

python3 -c "import speech_recognition" 2>/dev/null && \
    log_ok "SpeechRecognition OK" || \
    log_warn "SpeechRecognition bermasalah"

python3 -c "import pyaudio" 2>/dev/null && \
    log_ok "PyAudio OK" || \
    log_warn "PyAudio bermasalah — coba: pkg install portaudio && pip install pyaudio"

# ── FIX 6: ddgs (DuckDuckGo) ──────────────────────────────────
echo ""
log_info "FIX 6: ddgs (browsing internet)"
echo ""

pip install ddgs --upgrade --quiet 2>/dev/null
if python3 -c "from ddgs import DDGS" 2>/dev/null; then
    log_ok "ddgs OK"
else
    pip install duckduckgo-search --upgrade --quiet 2>/dev/null
    python3 -c "from duckduckgo_search import DDGS" 2>/dev/null && \
        log_ok "duckduckgo-search OK (fallback)" || \
        log_warn "Browsing tidak tersedia"
fi

# ── FIX 7: python-dotenv ──────────────────────────────────────
echo ""
log_info "FIX 7: python-dotenv"
pip install python-dotenv --quiet 2>/dev/null
python3 -c "import dotenv" 2>/dev/null && log_ok "python-dotenv OK" || log_warn "dotenv gagal"

# ── FIX 8: Termux API + mpv ───────────────────────────────────
echo ""
log_info "FIX 8: Termux tools (audio player + TTS)"
echo ""

if command -v mpv &>/dev/null; then
    log_ok "mpv tersedia"
else
    log_warn "mpv tidak ditemukan — install: pkg install mpv"
    pkg install -y mpv 2>/dev/null | tail -2
fi

if command -v termux-tts-speak &>/dev/null; then
    log_ok "Termux TTS tersedia (offline fallback)"
else
    log_warn "Termux TTS tidak tersedia — install Termux:API dari Play Store"
    log_warn "lalu jalankan: pkg install termux-api"
fi

# ── VERIFIKASI AKHIR ──────────────────────────────────────────
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
log_info "RINGKASAN STATUS KOMPONEN:"
echo ""

check_py() {
    local label=$1; local mod=$2
    python3 -c "import $mod" 2>/dev/null && \
        echo -e "  ${GREEN}✓${NC} $label" || \
        echo -e "  ${RED}✗${NC} $label"
}

check_tool() {
    local label=$1; local cmd=$2
    command -v "$cmd" &>/dev/null && \
        echo -e "  ${GREEN}✓${NC} $label" || \
        echo -e "  ${RED}✗${NC} $label"
}

echo "  [ Python Packages ]"
check_py "OpenCV (cv2)"           "cv2"
check_py "Gemini AI"              "google.generativeai"
check_py "SpeechRecognition"      "speech_recognition"
check_py "PyAudio"                "pyaudio"
check_py "edge-tts"               "edge_tts"
check_py "gTTS (fallback TTS)"    "gtts"
check_py "requests"               "requests"
check_py "colorama"               "colorama"
check_py "python-dotenv"          "dotenv"
check_py "ddgs (browsing)"        "ddgs"
check_py "numpy"                  "numpy"

echo ""
echo "  [ System Tools ]"
check_tool "FLAC (speech)"  "flac"
check_tool "mpv (audio)"    "mpv"
check_tool "ffmpeg"         "ffmpeg"
check_tool "python3"        "python3"
check_tool "Termux TTS"     "termux-tts-speak"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Fix selesai! Sekarang jalankan Friday:${NC}"
echo ""
echo -e "  ${CYAN}bash start.sh${NC}"
echo -e "  ${CYAN}# atau: python main.py${NC}"
echo ""
echo -e "${YELLOW}Tips penting:${NC}"
echo "  • OpenCV (cv2) HARUS diinstall via: pkg install python-opencv"
echo "  • Jika kamera gagal, Friday tetap jalan dalam mode SUARA SAJA"
echo "  • Pastikan KAMERA_WAJIB = False di config.py"
echo "  • Restart Termux jika wake word masih error FLAC"
echo "  • Mikrofon perlu izin di Termux:API (Settings → Apps → Termux:API)"
echo ""
