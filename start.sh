#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   start.sh — Project Friday v3.0.0
#   Script launcher untuk Termux (Android)
#
#   CARA PAKAI:
#     chmod +x start.sh
#     bash start.sh
# ==============================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Pindah ke direktori script (agar path relatif benar)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cek config.py
if [ ! -f "config.py" ]; then
    echo -e "${RED}[✗] config.py tidak ditemukan!${NC}"
    echo -e "${YELLOW}    Jalankan: bash setup_termux.sh${NC}"
    exit 1
fi

# Cek main.py
if [ ! -f "main.py" ]; then
    echo -e "${RED}[✗] main.py tidak ditemukan!${NC}"
    echo -e "${YELLOW}    Pastikan Anda berada di folder yang benar.${NC}"
    exit 1
fi

# Aktifkan virtual environment jika ada
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}[✓] Virtual environment aktif.${NC}"
fi

echo -e "${CYAN}"
echo "  ┌─────────────────────────────────────────────────┐"
echo "  │   🤖 FRIDAY AI v3.0.0 — Starting...             │"
echo "  │   Platform : Termux + IPWebcam + Xiaomi Pad 7   │"
echo "  └─────────────────────────────────────────────────┘"
echo -e "${NC}"

# Jalankan Friday
python main.py

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}[✗] Friday berhenti dengan error (kode: $EXIT_CODE)${NC}"
    echo -e "${YELLOW}Tips troubleshooting:${NC}"
    echo "  • Pastikan IPWebcam sudah Start server"
    echo "  • Cek URL kamera di config.py"
    echo "  • Pastikan API key Gemini valid"
    echo "  • Jalankan: bash setup_termux.sh (untuk reinstall)"
fi
