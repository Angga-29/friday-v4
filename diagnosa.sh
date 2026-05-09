#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   diagnosa.sh — Friday AI v4.0 | Diagnostik Konfigurasi
#   Menampilkan APA YANG SEBENARNYA dimuat Friday saat dijalankan.
#
#   Pakai script ini kalau:
#     - Kamera tidak terhubung padahal IP sudah benar di config.py
#     - API key error padahal sudah diganti yang baru
#     - Friday menyapa "Bos NamaMu" padahal sudah set nama
#     - git pull tidak terlihat efeknya
#
#   CARA PAKAI:
#     bash diagnosa.sh
# ==============================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║       FRIDAY AI — DIAGNOSTIK KONFIGURASI            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Lokasi & Branch Git ────────────────────────────────────
echo -e "${BOLD}[1] LOKASI & GIT${NC}"
echo "  Direktori : $(pwd)"
if [ -d ".git" ]; then
    echo "  Branch    : $(git branch --show-current 2>/dev/null)"
    echo "  Commit    : $(git log -1 --oneline 2>/dev/null)"
    if ! git diff --quiet 2>/dev/null; then
        echo -e "  ${YELLOW}[!] Ada perubahan lokal yang belum di-commit:${NC}"
        git status -s 2>/dev/null | head -10 | sed 's/^/      /'
        echo -e "  ${YELLOW}    git pull tidak akan menimpa file ini!${NC}"
    fi
else
    echo -e "  ${RED}[X] Bukan repo git!${NC}"
fi
echo ""

# ── 2. File .env (PENYEBAB UTAMA MASALAH) ─────────────────────
echo -e "${BOLD}[2] FILE .env${NC}"
if [ -f ".env" ]; then
    echo -e "  ${RED}[X] File .env DITEMUKAN — INI BAHAYA!${NC}"
    echo -e "  ${YELLOW}    .env akan MENIMPA config.py via load_dotenv().${NC}"
    echo "    Isinya:"
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then continue; fi
        # Sensor API key
        if [[ "$line" == *"_KEY="* ]]; then
            kunci="${line%%=*}"
            nilai="${line#*=}"
            if [ ${#nilai} -gt 12 ]; then
                echo "      $kunci = ${nilai:0:6}...${nilai: -4}"
            else
                echo "      $line"
            fi
        else
            echo "      $line"
        fi
        # Cek placeholder
        if [[ "$line" == *"192.168.x.x"* ]] || \
           [[ "$line" == *"your_"*"_here"* ]] || \
           [[ "$line" == *"NamaMu"* ]]; then
            echo -e "      ${RED}↑ PLACEHOLDER! Inilah penyebab error.${NC}"
        fi
    done < .env
    echo ""
    echo -e "  ${GREEN}SOLUSI: Hapus .env agar config.py jadi sumber utama:${NC}"
    echo -e "  ${GREEN}    rm .env${NC}"
else
    echo -e "  ${GREEN}[OK] Tidak ada .env — config.py jadi sumber utama${NC}"
fi
echo ""

# ── 3. Apa yang DIMUAT oleh Python ────────────────────────────
echo -e "${BOLD}[3] NILAI YANG SEBENARNYA DIMUAT FRIDAY${NC}"
if [ -f "config.py" ]; then
    python3 << 'PYEOF'
import sys, os
sys.path.insert(0, '.')
try:
    import config
except Exception as e:
    print(f"  [X] Gagal load config.py: {e}")
    sys.exit(1)

def sensor(s):
    s = str(s)
    if len(s) > 12:
        return f"{s[:6]}...{s[-4:]}"
    return s

def cek(label, nilai, placeholder_pattern=None):
    nilai_str = str(nilai)
    is_placeholder = False
    if placeholder_pattern:
        for p in placeholder_pattern:
            if p in nilai_str:
                is_placeholder = True
                break
    tampil = sensor(nilai) if "API_KEY" in label or "KEY" in label else nilai_str
    if is_placeholder:
        print(f"  [X] {label:18} = {tampil}  <- PLACEHOLDER!")
    else:
        print(f"  [OK] {label:18} = {tampil}")

cek("URL_KAMERA", config.URL_KAMERA, ["192.168.x.x", "x.x:8080"])
cek("API_KEY_GEMINI", config.API_KEY_GEMINI, ["your_", "_here"])
cek("API_KEY_CUACA", config.API_KEY_CUACA, ["your_", "_here"])
cek("API_KEY_BERITA", config.API_KEY_BERITA, ["your_", "_here"])
cek("NAMA_PENGGUNA", config.NAMA_PENGGUNA, ["NamaMu"])
cek("KOTA_CUACA", config.KOTA_CUACA, [])
cek("KAMERA_WAJIB", config.KAMERA_WAJIB, [])
PYEOF
else
    echo -e "  ${RED}[X] config.py tidak ada!${NC}"
    echo "      Jalankan: bash setup_config.sh"
fi
echo ""

# ── 4. Test Kamera ────────────────────────────────────────────
echo -e "${BOLD}[4] TEST KONEKSI KAMERA${NC}"
if [ -f "config.py" ]; then
    URL=$(python3 -c "import sys; sys.path.insert(0,'.'); import config; print(config.URL_KAMERA)" 2>/dev/null)
    if [ -n "$URL" ]; then
        echo "  URL: $URL"
        if [[ "$URL" == *"192.168.x.x"* ]]; then
            echo -e "  ${RED}[X] URL berisi placeholder! Perbaiki dulu.${NC}"
        elif command -v curl &>/dev/null; then
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$URL" 2>/dev/null)
            if [ "$STATUS" = "200" ]; then
                echo -e "  ${GREEN}[OK] Kamera RESPON — URL benar dan terjangkau${NC}"
            else
                echo -e "  ${RED}[X] Kamera tidak respon (HTTP: $STATUS)${NC}"
                echo "      Periksa: aplikasi IP Webcam sudah Start server?"
                echo "      Periksa: IP di config.py sama dengan yang ditampilkan IP Webcam?"
            fi
        else
            echo -e "  ${YELLOW}[?] curl tidak ada — install: pkg install curl${NC}"
        fi
    fi
fi
echo ""

# ── 5. Audio Player ───────────────────────────────────────────
echo -e "${BOLD}[5] AUDIO PLAYER (untuk TTS)${NC}"
ada_player=false
for player in mpv ffplay termux-media-player play; do
    if command -v "$player" &>/dev/null; then
        echo -e "  ${GREEN}[OK] $player tersedia${NC}"
        ada_player=true
    fi
done
if ! $ada_player; then
    echo -e "  ${RED}[X] TIDAK ADA AUDIO PLAYER — Friday tidak akan bersuara!${NC}"
    echo -e "  ${GREEN}    Install: pkg install mpv${NC}"
fi
echo ""

# ── 6. Python Modules Penting ─────────────────────────────────
echo -e "${BOLD}[6] PYTHON MODULES${NC}"
for mod in cv2 google.generativeai speech_recognition edge_tts dotenv requests; do
    if python3 -c "import $mod" 2>/dev/null; then
        echo -e "  ${GREEN}[OK] $mod${NC}"
    else
        echo -e "  ${RED}[X] $mod TIDAK ADA${NC}"
    fi
done
echo ""

# ── Kesimpulan ────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════╗"
echo -e "║                   LANGKAH PERBAIKAN                  ║"
echo -e "╚══════════════════════════════════════════════════════╝${NC}"
echo ""
if [ -f ".env" ]; then
    echo -e "  ${RED}1. HAPUS .env (penyebab utama):${NC}"
    echo -e "     ${BOLD}rm .env${NC}"
    echo ""
fi
echo "  2. Jalankan ulang setup_config.sh untuk isi config.py:"
echo -e "     ${BOLD}bash setup_config.sh${NC}"
echo ""
echo "  3. Jalankan diagnosa lagi untuk verifikasi:"
echo -e "     ${BOLD}bash diagnosa.sh${NC}"
echo ""
echo "  4. Kalau semua OK, jalankan Friday:"
echo -e "     ${BOLD}python main.py${NC}"
echo ""
