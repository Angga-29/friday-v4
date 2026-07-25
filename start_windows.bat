@echo off
REM ==============================================================
REM   start_windows.bat — Project Friday v5.0.0
REM   Script launcher untuk Windows (ASUS TUF dkk)
REM
REM   CARA PAKAI:
REM     start_windows.bat
REM ==============================================================

cd /d "%~dp0"

if not exist "config.py" (
    echo [X] config.py tidak ditemukan!
    echo     Jalankan dulu: setup_windows.ps1
    exit /b 1
)

if not exist "main.py" (
    echo [X] main.py tidak ditemukan!
    echo     Pastikan Anda berada di folder yang benar.
    exit /b 1
)

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment aktif.
)

echo.
echo   ============================================================
echo     FRIDAY AI v5.0.0 — Starting...
echo     Platform : Windows Desktop + USB Webcam (eMeet C960)
echo   ============================================================
echo.

python main.py

set EXIT_CODE=%ERRORLEVEL%

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [X] Friday berhenti dengan error ^(kode: %EXIT_CODE%^)
    echo Tips troubleshooting:
    echo   - Pastikan webcam USB ^(eMeet C960^) tercolok dan CAMERA_INDEX benar
    echo   - Cek ANTHROPIC_API_KEY di .env / config.py valid
    echo   - Jalankan ulang: setup_windows.ps1 untuk reinstall dependencies
)

pause
