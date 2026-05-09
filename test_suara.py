#!/usr/bin/env python3
# ==============================================================
# test_suara.py — Friday AI | Test Suara & Audio Player
# Jalankan: python test_suara.py
# ==============================================================
"""
Script ini menguji setiap komponen TTS dan audio player secara
terpisah sehingga mudah diketahui mana yang tidak bekerja.
"""

import os
import sys
import subprocess
import tempfile
import time

CYAN   = '\033[0;36m'
GREEN  = '\033[0;32m'
YELLOW = '\033[1;33m'
RED    = '\033[0;31m'
BOLD   = '\033[1m'
NC     = '\033[0m'

TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())
TEST_MP3 = os.path.join(TMPDIR, "friday_test_audio.mp3")

def ok(msg):  print(f"{GREEN}[OK]{NC} {msg}")
def err(msg): print(f"{RED}[X]{NC}  {msg}")
def warn(msg):print(f"{YELLOW}[!]{NC}  {msg}")
def info(msg):print(f"{CYAN}[·]{NC}  {msg}")

print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗")
print(        "║       FRIDAY AI — TEST SUARA & AUDIO PLAYER          ║")
print(       f"╚══════════════════════════════════════════════════════╝{NC}\n")

# ── 1. Cek audio player ───────────────────────────────────────
print(f"{BOLD}[1] CEK AUDIO PLAYER{NC}")
ada_player = []
for p in ["mpv", "ffplay", "play", "termux-tts-speak"]:
    if subprocess.run(["which", p], capture_output=True).returncode == 0:
        ok(f"{p} tersedia")
        ada_player.append(p)
    else:
        warn(f"{p} tidak ada")

if not ada_player:
    err("Tidak ada audio player sama sekali!")
    print(f"\n  {YELLOW}Install mpv:{NC}")
    print(  "    pkg install mpv")
    sys.exit(1)
print()

# ── 2. Test Edge-TTS (generate MP3) ──────────────────────────
print(f"{BOLD}[2] TEST EDGE-TTS (generate MP3){NC}")
edge_ok = False
try:
    import asyncio
    import edge_tts

    async def _gen():
        c = edge_tts.Communicate("Halo, ini adalah tes suara Friday.", "id-ID-GadisNeural")
        await c.save(TEST_MP3)

    asyncio.run(_gen())
    ukuran = os.path.getsize(TEST_MP3)
    if ukuran > 1000:
        ok(f"Edge-TTS berhasil generate MP3 ({ukuran} bytes)")
        edge_ok = True
    else:
        err(f"Edge-TTS generate file terlalu kecil ({ukuran} bytes) — mungkin offline?")
except ImportError:
    warn("edge-tts tidak terinstall. Install: pip install edge-tts")
except Exception as e:
    err(f"Edge-TTS gagal: {e}")
print()

# ── 3. Test play MP3 dengan setiap player ────────────────────
if edge_ok and os.path.exists(TEST_MP3):
    print(f"{BOLD}[3] TEST PUTAR MP3{NC}")
    print(  "  Anda akan mendengar suara test dari setiap player yang ada.")
    print(  "  Jawab: apakah suara keluar? (y/n)\n")

    players = [
        ("mpv",    ["mpv", "--no-video", "--volume=100", "--quiet", "--really-quiet", TEST_MP3]),
        ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-volume", "100",
                    "-loglevel", "quiet", TEST_MP3]),
        ("play",   ["play", "-q", TEST_MP3]),
    ]

    player_berhasil = None
    for nama, cmd in players:
        if subprocess.run(["which", cmd[0]], capture_output=True).returncode != 0:
            continue
        info(f"Mencoba {nama}...")
        try:
            ret = subprocess.run(cmd, capture_output=True, timeout=30)
            if ret.returncode == 0:
                jawab = input(f"  → Apakah suara keluar dari {nama}? (y/n): ").strip().lower()
                if jawab == 'y':
                    ok(f"{nama} BEKERJA — inilah player yang akan dipakai Friday")
                    player_berhasil = nama
                    break
                else:
                    warn(f"{nama} jalan tapi tidak ada suara → coba player berikut")
            else:
                err(f"{nama} return code {ret.returncode}")
        except FileNotFoundError:
            warn(f"{nama} tidak ditemukan")
        except subprocess.TimeoutExpired:
            err(f"{nama} timeout")

    if not player_berhasil:
        print()
        err("TIDAK ADA PLAYER YANG MENGHASILKAN SUARA!")
        print(f"\n{YELLOW}Kemungkinan penyebab:{NC}")
        print("  1. Volume tablet di-mute atau terlalu kecil")
        print("  2. Audio output salah (misal ke Bluetooth yang tidak terhubung)")
        print("  3. Perlu restart audio: jalankan 'pulseaudio --start' di Termux")
        print()
        print(f"{YELLOW}Coba solusi:{NC}")
        print("  a) Naikkan volume tablet lewat tombol fisik")
        print("  b) Cabut headphone/earphone jika terpasang")
        print("  c) Di Termux: pkg install pulseaudio && pulseaudio --start")
    print()
else:
    print(f"{BOLD}[3] TEST PUTAR MP3{NC}")
    warn("Edge-TTS gagal generate MP3 — skip test putar")
    print()

# ── 4. Test Termux TTS langsung ──────────────────────────────
print(f"{BOLD}[4] TEST TERMUX TTS LANGSUNG{NC}")
if subprocess.run(["which", "termux-tts-speak"], capture_output=True).returncode == 0:
    info("Mencoba termux-tts-speak...")
    ret = subprocess.run(
        ["termux-tts-speak", "Halo ini tes Termux TTS"],
        capture_output=True, timeout=30
    )
    if ret.returncode == 0:
        jawab = input("  → Apakah suara Termux TTS keluar? (y/n): ").strip().lower()
        if jawab == 'y':
            ok("Termux TTS bekerja sebagai fallback")
        else:
            warn("Termux TTS jalan tapi tidak ada suara")
    else:
        err(f"termux-tts-speak gagal (code {ret.returncode})")
else:
    warn("termux-tts-speak tidak ada — install Termux:API dari Play Store")
    warn("lalu: pkg install termux-api")
print()

# ── Bersihkan ─────────────────────────────────────────────────
try:
    if os.path.exists(TEST_MP3):
        os.remove(TEST_MP3)
except OSError:
    pass

# ── Kesimpulan ────────────────────────────────────────────────
print(f"{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗")
print(        "║                    SELESAI                           ║")
print(       f"╚══════════════════════════════════════════════════════╝{NC}")
print()
print("Setelah test, jalankan Friday:")
print(f"  {CYAN}python main.py{NC}")
print()
print("Jika suara masih hilang saat Friday jalan, perhatikan baris:")
print(f"  {CYAN}Audio diputar via mpv.{NC}  ← harus muncul setiap Friday bicara")
print(f"  Kalau baris ini tidak muncul → {YELLOW}cek error di atasnya.{NC}")
print()
