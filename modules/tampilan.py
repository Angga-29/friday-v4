# ==============================================================
# modules/tampilan.py — Project Friday | JARVIS-Style Display
# Versi : 6.0.0 — Animated spinner, proper word-wrap, richer UI
# ==============================================================

import os
import sys
import time
import threading
from colorama import Fore, Back, Style, init
from datetime import datetime

init(autoreset=True)

VERSION = "4.0.0"
LEBAR   = 58   # lebar konten dalam box

# ── Warna tema ────────────────────────────────────────────────
C   = Fore.CYAN    + Style.BRIGHT
W   = Fore.WHITE   + Style.BRIGHT
G   = Fore.GREEN   + Style.BRIGHT
Y   = Fore.YELLOW  + Style.BRIGHT
R   = Fore.RED     + Style.BRIGHT
M   = Fore.MAGENTA + Style.BRIGHT
B   = Fore.BLUE    + Style.BRIGHT
DIM = Style.DIM
RST = Style.RESET_ALL


# ==============================================================
# WORD-WRAP HELPER
# ==============================================================
def _wrap_teks(teks: str, lebar: int) -> list:
    """Pecah teks menjadi list baris dengan panjang maks lebar karakter.
    Tidak memotong kata di tengah."""
    kata_list = teks.split()
    baris_list = []
    baris = ""
    for kata in kata_list:
        if len(baris) + len(kata) + (1 if baris else 0) <= lebar:
            baris = (baris + " " + kata) if baris else kata
        else:
            if baris:
                baris_list.append(baris)
            baris = kata
    if baris:
        baris_list.append(baris)
    return baris_list or [""]


def bersihkan_layar():
    os.system('clear')


# ==============================================================
# HEADER UTAMA
# ==============================================================
def tampilkan_header():
    bersihkan_layar()
    sekarang = datetime.now().strftime("%A, %d %B %Y  ·  %H:%M:%S")

    garis = "═" * LEBAR
    print()
    print(C + "╔" + garis + "╗")
    print(C + "║" + " " * LEBAR + "║")
    print(C + "║" + W +
          "    ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗   " + C + "║")
    print(C + "║" + C +
          "    ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝   " + C + "║")
    print(C + "║" + W +
          "    █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝    " + C + "║")
    print(C + "║" + C +
          "    ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝     " + C + "║")
    print(C + "║" + W +
          "    ██║     ██║  ██║██║██████╔╝██║  ██║   ██║       " + C + "║")
    print(C + "║" + " " * LEBAR + "║")
    print(C + "╠" + "═" * LEBAR + "╣")

    sub = " JARVIS INTERFACE  ·  ANGGA PROJECT  ·  v4.0 PREMIUM "
    pad = LEBAR - len(sub)
    print(C + "║" + Fore.CYAN + DIM + sub + " " * pad + C + "║")
    print(C + "╠" + "═" * LEBAR + "╣")

    waktu_pad = LEBAR - len(sekarang) - 4
    print(C + "║  " + Y + sekarang + " " * waktu_pad + C + "  ║")
    print(C + "╠" + "─" * LEBAR + "╣")

    fitur = [
        ("●", "Gemini 2.5 Flash",     "ONLINE", G),
        ("●", "Edge-TTS  (en-GB-Ryan)", "AKTIF", G),
        ("●", "Wake Word + Clap",      "AKTIF",  G),
        ("●", "Skills System",         "LOADED", G),
        ("●", "Browser + Berita",      "AKTIF",  G),
        ("●", "Memori Permanen",       "AKTIF",  G),
        ("●", "Riset Mendalam",        "AKTIF",  G),
        ("●", "Mode Proaktif",         "AKTIF",  G),
    ]
    mid = len(fitur) // 2
    for i in range(mid):
        a_ikon, a_nama, a_status, a_warna = fitur[i]
        b_ikon, b_nama, b_status, b_warna = fitur[i + mid]
        kol_a = f"  {a_ikon} {a_nama:<22} {a_warna}{a_status}{C}"
        kol_b = f"  {b_ikon} {b_nama:<22} {b_warna}{b_status}{C}"
        print(C + "║" + kol_a + " │" + kol_b + " " * 3 + "║")

    print(C + "╚" + "═" * LEBAR + "╝")
    print()


# ==============================================================
# STATUS — notifikasi satu baris dengan ikon & warna per tipe
# ==============================================================
_STATUS_CFG = {
    "info":      (Fore.CYAN,    "·", False),
    "sukses":    (Fore.GREEN,   "✓", True),
    "peringatan":(Fore.YELLOW,  "⚠", True),
    "error":     (Fore.RED,     "✗", True),
    "ai":        (Fore.MAGENTA, "◈", True),
    "deteksi":   (Fore.YELLOW,  "⚡", True),
    "browsing":  (Fore.BLUE,    "◎", True),
    "wake":      (Fore.CYAN,    "◉", True),
    "vision":    (Fore.MAGENTA, "◑", True),
    "memori":    (Fore.GREEN,   "◆", False),
}

def tampilkan_status(pesan: str, tipe: str = "info"):
    waktu            = datetime.now().strftime("%H:%M:%S")
    warna, ikon, bold = _STATUS_CFG.get(tipe, (Fore.WHITE, "?", False))
    tebal            = Style.BRIGHT if bold else ""
    for i, baris in enumerate(pesan.splitlines()):
        if i == 0:
            print(f"{Fore.CYAN}{DIM}[{waktu}]{RST} {warna}{tebal}[{ikon}] {baris}{RST}")
        else:
            print(f"          {warna}    {baris}{RST}")


# ==============================================================
# ANIMATED SPINNER — untuk proses yang makan waktu
# ==============================================================
_spinner_aktif  = False
_spinner_thread = None

_SPINNER_FRAMES = ["⠋","⠙","⠸","⠴","⠦","⠇"]   # braille spinner

def mulai_spinner(pesan: str = "Memproses"):
    """Jalankan spinner animasi di background thread."""
    global _spinner_aktif, _spinner_thread
    if _spinner_aktif:
        return
    _spinner_aktif = True

    def _loop():
        idx = 0
        while _spinner_aktif:
            frame  = _SPINNER_FRAMES[idx % len(_SPINNER_FRAMES)]
            waktu  = datetime.now().strftime("%H:%M:%S")
            sys.stdout.write(
                f"\r{Fore.CYAN}{DIM}[{waktu}]{RST} "
                f"{M}{Style.BRIGHT}[{frame}] {pesan}...{RST}"
            )
            sys.stdout.flush()
            idx += 1
            time.sleep(0.12)
        sys.stdout.write("\r" + " " * 72 + "\r")
        sys.stdout.flush()

    _spinner_thread = threading.Thread(target=_loop, daemon=True)
    _spinner_thread.start()

def stop_spinner():
    global _spinner_aktif
    _spinner_aktif = False
    if _spinner_thread:
        _spinner_thread.join(timeout=0.5)


# ==============================================================
# MEMPROSES — Gemini (dengan spinner)
# ==============================================================
def tampilkan_memproses():
    mulai_spinner("Berpikir via Gemini 2.5")


# ==============================================================
# SPEECH BUBBLE FRIDAY — word-wrap proper
# ==============================================================
def tampilkan_friday_bicara(teks: str):
    stop_spinner()   # hentikan spinner kalau masih jalan
    print()
    lebar_isi = LEBAR - 4   # ruang teks dalam box

    # Pecah per kalimat dulu, lalu word-wrap tiap kalimat
    semua_baris = []
    for kalimat in teks.replace('. ', '.||').replace('! ', '!||').replace('? ', '?||').split('||'):
        kalimat = kalimat.strip()
        if not kalimat:
            continue
        semua_baris.extend(_wrap_teks(kalimat, lebar_isi))

    # Judul bubble
    judul   = "◈ FRIDAY"
    garis_t = "─" * (LEBAR - len(judul) - 4)
    print(C + "  ╭─ " + W + judul + C + " " + garis_t + "╮")

    for baris in semua_baris:
        pad = lebar_isi - len(baris)
        print(C + "  │  " + W + baris + " " * pad + C + "  │")

    print(C + "  ╰" + "─" * (LEBAR) + "╯")
    print()


# ==============================================================
# USER BERBICARA
# ==============================================================
def tampilkan_user_bicara(teks: str):
    print()
    baris_list = _wrap_teks(teks, LEBAR - 12)
    print(G + "  ╭─ " + W + "▶ ANDA" + G + " " + "─" * (LEBAR - 7) + "╮")
    for b in baris_list:
        pad = LEBAR - 2 - len(b)
        print(G + "  │  " + W + b + " " * pad + G + "  │")
    print(G + "  ╰" + "─" * LEBAR + "╯")
    print()


# ==============================================================
# DIVIDER
# ==============================================================
def tampilkan_divider():
    print(C + DIM + "  " + "·" * 56)


# ==============================================================
# MENDENGARKAN — pulse waveform
# ==============================================================
_WAVE = "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"

def tampilkan_mendengarkan():
    print()
    garis = "═" * LEBAR
    print(G + "  ╔" + garis + "╗")
    print(G + "  ║  " + W + "◉  MENDENGARKAN" +
          G + DIM + f"  {_WAVE}  " + RST + G + " " * 6 + "║")
    print(G + "  ║  " + Fore.GREEN + DIM +
          "  Silakan bicara sekarang..." + " " * 27 + G + "║")
    print(G + "  ╚" + garis + "╝")
    print()


# ==============================================================
# BERITA — panel pop-up
# ==============================================================
def pop_up_berita(daftar_berita: list):
    if not daftar_berita:
        return
    print()
    lebar_b = LEBAR - 2
    print(Y + "  ╔══ " + W + "📡 INTEL FEED" + Y + " " + "═" * (lebar_b - 15) + "╗")
    for i, berita in enumerate(daftar_berita, 1):
        if isinstance(berita, dict):
            sumber = berita.get("sumber", "")
            judul  = berita.get("judul", "")
            teks   = f"{sumber}: {judul}" if sumber else judul
        else:
            teks = str(berita)
        pendek  = (teks[:lebar_b - 5] + "..") if len(teks) > lebar_b - 3 else teks
        padding = " " * (lebar_b - 3 - len(pendek))
        print(Y + "  ║ " + Fore.YELLOW + DIM + f"{i}. " + W + pendek + padding + Y + "║")
    print(Y + "  ╚" + "═" * lebar_b + "╝")
    print()


# ==============================================================
# BROWSING — panel biru
# ==============================================================
def tampilkan_browsing(query: str):
    print()
    print(B + "  ╔══ " + W + "◎ BROWSING INTERNET" + B + " " + "─" * (LEBAR - 21) + "╗")
    baris_list = _wrap_teks(f"🔍  {query}", LEBAR - 4)
    for b in baris_list:
        pad = LEBAR - len(b)
        print(B + "  ║  " + Fore.CYAN + b + " " * (pad - 2) + B + "║")
    print(B + "  ╚" + "═" * LEBAR + "╝")
    print()


# ==============================================================
# VISION — panel magenta
# ==============================================================
def tampilkan_vision():
    print()
    print(M + "  ╔══ " + W + "◑ FRIDAY VISION" + M + " " + "─" * (LEBAR - 17) + "╗")
    print(M + "  ║  " + W + "Kamera aktif → Gemini Vision menganalisis..." +
          " " * (LEBAR - 46) + M + "║")
    print(M + "  ╚" + "═" * LEBAR + "╝")
    print()


# ==============================================================
# APP DIBUKA — panel hijau
# ==============================================================
def tampilkan_app_dibuka(nama_app: str):
    print()
    print(G + "  ╔══ " + W + "▶ MEMBUKA APLIKASI" + G + " " + "─" * (LEBAR - 20) + "╗")
    baris   = f"  Launching: {nama_app}"
    padding = " " * (LEBAR - len(baris))
    print(G + "  ║" + W + baris + padding + G + "║")
    print(G + "  ╚" + "═" * LEBAR + "╝")
    print()


# ==============================================================
# MUSIK — panel ungu
# ==============================================================
def tampilkan_musik(aksi: str, detail: str = ""):
    UNGU = Fore.MAGENTA + Style.BRIGHT
    print()
    print(UNGU + "  ╔══ " + W + "♪ MUSIK KONTROL" + UNGU + " " + "─" * (LEBAR - 17) + "╗")
    baris = f"  ▶ {aksi}"
    if detail:
        baris += f": {detail}"
    baris_list = _wrap_teks(baris, LEBAR - 2)
    for b in baris_list:
        padding = " " * (LEBAR - len(b))
        print(UNGU + "  ║" + W + b + padding + UNGU + "║")
    print(UNGU + "  ╚" + "═" * LEBAR + "╝")
    print()


# ==============================================================
# STREAMING BUBBLE — tampilkan jawaban Gemini secara live
# ==============================================================
_ss = {          # stream state
    "aktif"   : False,
    "buf"     : "",    # kata yang belum di-print
    "line_len": 0,     # panjang baris aktif
    "lebar"   : 52,    # lebar isi (diset saat mulai)
}


def mulai_bubble_stream():
    """Cetak header bubble streaming — dipanggil SEBELUM iterasi chunks."""
    stop_spinner()
    _ss["aktif"]    = True
    _ss["buf"]      = ""
    _ss["line_len"] = 0
    _ss["lebar"]    = LEBAR - 6   # padding kiri+kanan

    print()
    judul    = "◈ FRIDAY  ·  live"
    garis_t  = "─" * (LEBAR - len(judul) - 4)
    print(C + "  ╭─ " + W + judul + C + " " + garis_t + "╮")
    sys.stdout.write(C + "  │  " + W)
    sys.stdout.flush()


def _cetak_kata(kata: str):
    """Print satu kata ke baris aktif; wrap jika melebihi lebar."""
    lebar   = _ss["lebar"]
    spasi   = 1 if _ss["line_len"] > 0 else 0

    if _ss["line_len"] + spasi + len(kata) > lebar:
        # Pindah baris
        sisa = lebar - _ss["line_len"]
        sys.stdout.write(" " * sisa + C + "  │\n  │  " + W)
        _ss["line_len"] = 0
        spasi = 0

    if spasi:
        sys.stdout.write(" ")
        _ss["line_len"] += 1

    sys.stdout.write(kata)
    _ss["line_len"] += len(kata)
    sys.stdout.flush()


def stream_chunk(chunk: str):
    """
    Terima potongan teks dari Gemini dan cetak word-by-word ke dalam bubble.
    Dipanggil berulang saat iterasi generator tanya_stream().
    """
    if not _ss["aktif"] or not chunk:
        return

    _ss["buf"] += chunk

    # Proses kata-kata yang sudah lengkap (dipisah spasi)
    while True:
        idx = _ss["buf"].find(" ")
        if idx == -1:
            break
        kata = _ss["buf"][:idx].strip()
        _ss["buf"] = _ss["buf"][idx + 1:]
        if kata:
            _cetak_kata(kata)

    # Kata yang diakhiri newline → cetak dan bungkus baris
    while "\n" in _ss["buf"]:
        idx  = _ss["buf"].find("\n")
        kata = _ss["buf"][:idx].strip()
        _ss["buf"] = _ss["buf"][idx + 1:]
        if kata:
            _cetak_kata(kata)
        sisa = _ss["lebar"] - _ss["line_len"]
        sys.stdout.write(" " * sisa + C + "  │\n  │  " + W)
        _ss["line_len"] = 0
        sys.stdout.flush()


def tutup_bubble_stream():
    """Flush sisa kata + cetak footer bubble — dipanggil SETELAH stream selesai."""
    if not _ss["aktif"]:
        return

    # Flush kata terakhir yang belum diprint
    sisa_kata = _ss["buf"].strip()
    if sisa_kata:
        _cetak_kata(sisa_kata)
    _ss["buf"] = ""

    # Tutup baris terakhir
    sisa_spasi = _ss["lebar"] - _ss["line_len"]
    sys.stdout.write(" " * sisa_spasi + C + "  │\n")
    print(C + "  ╰" + "─" * LEBAR + "╯")
    print()

    _ss["aktif"]    = False
    _ss["line_len"] = 0


# ==============================================================
# STATISTIK
# ==============================================================
def tampilkan_statistik(stats: dict):
    print()
    print(G + "  ╔══ " + W + "📊 STATISTIK HARI INI" + G + " " + "─" * (LEBAR - 23) + "╗")
    items = [
        ("💬", "Total Interaksi",   stats.get("interaksi", 0)),
        ("🌐", "Browsing Internet", stats.get("browsing",  0)),
        ("⚡", "Skill Lokal",       stats.get("skill",     0)),
        ("🔬", "Riset Mendalam",    stats.get("riset",     0)),
        ("👤", "Deteksi Wajah",     stats.get("wajah",     0)),
    ]
    for ikon, label, nilai in items:
        bar_max  = 18
        bar_fill = min(int(nilai * 2), bar_max) if nilai else 0
        bar      = "█" * bar_fill + "░" * (bar_max - bar_fill)
        angka    = str(nilai)
        sisa     = LEBAR - 4 - len(label) - len(bar) - len(angka) - 5
        print(G + "  ║" + W + f"  {ikon} {label:<20} " +
              G + bar + W + f" {angka}" + " " * max(0, sisa) + G + "║")
    print(G + "  ╚" + "═" * LEBAR + "╝")
    print()
