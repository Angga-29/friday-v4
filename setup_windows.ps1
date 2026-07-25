# ==============================================================
#   setup_windows.ps1 — Project Friday v5.0.0
#   Script setup untuk Windows (ASUS TUF dkk)
#
#   CARA PAKAI (PowerShell):
#     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#     .\setup_windows.ps1
# ==============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host ""
Write-Host "  FRIDAY AI v5.0.0 — Setup Windows" -ForegroundColor Cyan
Write-Host "  Platform: Windows Desktop + USB Webcam (eMeet C960)" -ForegroundColor Cyan
Write-Host ""

# 1. Cek Python
try {
    $pyVersion = python --version
    Write-Host "[OK] $pyVersion terdeteksi." -ForegroundColor Green
} catch {
    Write-Host "[GAGAL] Python tidak ditemukan. Install dari https://python.org (centang 'Add to PATH')." -ForegroundColor Red
    exit 1
}

# 2. Buat virtual environment jika belum ada
if (-not (Test-Path "venv")) {
    Write-Host "[..] Membuat virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}
Write-Host "[OK] Virtual environment siap." -ForegroundColor Green

# 3. Aktifkan venv & install dependencies
& ".\venv\Scripts\Activate.ps1"
Write-Host "[..] Menginstall dependencies (pip)..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# 4. Setup config.py
if (-not (Test-Path "config.py")) {
    Copy-Item "config.example.py" "config.py"
    Write-Host "[OK] config.py dibuat dari template. Edit config.py untuk isi API key." -ForegroundColor Green
} else {
    Write-Host "[SKIP] config.py sudah ada, tidak ditimpa." -ForegroundColor Yellow
}

# 5. Setup .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] .env dibuat dari template. Edit .env untuk isi API key." -ForegroundColor Green
} else {
    Write-Host "[SKIP] .env sudah ada, tidak ditimpa." -ForegroundColor Yellow
}

# 6. Buat folder data/wajah_dikenal & assets
New-Item -ItemType Directory -Force -Path "data\wajah_dikenal" | Out-Null
New-Item -ItemType Directory -Force -Path "assets" | Out-Null

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  Setup selesai! Langkah manual yang MASIH perlu dilakukan:" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  1. Isi ANTHROPIC_API_KEY di .env (atau config.py)"
Write-Host "     -> https://console.anthropic.com/settings/keys"
Write-Host "  2. Install mpv (audio player wajib):"
Write-Host "     winget install mpv   (atau download dari https://mpv.io)"
Write-Host "  3. (Opsional) Install Ollama untuk fallback offline:"
Write-Host "     https://ollama.com/download/windows"
Write-Host "     ollama pull qwen2.5:7b"
Write-Host "  4. Colokkan webcam USB (eMeet C960), lalu cek index-nya:"
Write-Host "     python -c ""from modules.kamera import daftar_kamera_tersedia; daftar_kamera_tersedia()"""
Write-Host "     Set CAMERA_INDEX di .env/config.py sesuai hasilnya."
Write-Host "  5. (Opsional) Taruh logo/animasi custom di folder assets\ —"
Write-Host "     lihat assets\README.txt untuk nama file yang benar."
Write-Host "  6. Jalankan Friday:"
Write-Host "     - Dengan jendela terminal (untuk lihat log): .\start_windows.bat"
Write-Host "     - TANPA jendela sama sekali (UI hanya di browser):"
Write-Host "       double-click start_windows_silent.vbs"
Write-Host "       (kalau error, cek isi friday.log di folder ini)"
Write-Host "==================================================================" -ForegroundColor Cyan
