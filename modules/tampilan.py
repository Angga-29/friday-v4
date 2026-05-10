# ==============================================================
# modules/tampilan.py — Project Friday | JARVIS-Style Display
# Versi : 5.0.0 — Redesign penuh: banner, panel, speech bubble
# ==============================================================

import os
from colorama import Fore, Back, Style, init
from datetime import datetime

init(autoreset=True)

VERSION   = "4.0.0"
LEBAR     = 56   # lebar konten dalam box

# ── Warna tema ────────────────────────────────────────────────
C  = Fore.CYAN    + Style.BRIGHT   # Cyan terang  — frame utama
W  = Fore.WHITE   + Style.BRIGHT   # Putih terang — teks
G  = Fore.GREEN   + Style.BRIGHT   # Hijau        — sukses / user
Y  = Fore.YELLOW  + Style.BRIGHT   # Kuning       — peringatan
R  = Fore.RED     + Style.BRIGHT   # Merah        — error
M  = Fore.MAGENTA + Style.BRIGHT   # Magenta      — AI / vision
B  = Fore.BLUE    + Style.BRIGHT   # Biru         — browsing
DIM = Style.DIM
RST = Style.RESET_ALL


def bersihkan_layar():
    os.system('clear')


# ==============================================================
# HEADER UTAMA
# ==============================================================
def tampilkan_header():
    bersihkan_layar()
    sekarang = datetime.now().strftime("%d %B %Y  |  %H:%M:%S")

    garis = "═" * LEBAR
    print(C + "╔" + garis + "╗")
    print(C + "║" + W +
          "   ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗  " + C + "║")
    print(C + "║" + C +
          "   ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝  " + C + "║")
    print(C + "║" + W +
          "   █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝   " + C + "║")
    print(C + "║" + C +
          "   ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝    " + C + "║")
    print(C + "║" + W +
          "   ██║     ██║  ██║██║██████╔╝██║  ██║   ██║      " + C + "║")
    print(C + "╠" + garis + "╣")
    print(C + "║  " + G + f"AI Personal Assistant  •  v{VERSION}  PREMIUM" +
          " " * (LEBAR - 43) + C + "║")
    print(C + "║  " + Y + f"{sekarang:<54}" + C + "║")
    print(C + "╠" + garis + "╣")

    fitur = [
        ("⬡", "Kamera & Vision",  "ONLINE", G),
        ("⬡", "Gemini AI 2.5",   "ONLINE", G),
        ("⬡", "Wake Word",       "AKTIF",  G),
        ("⬡", "Pengenalan Wajah","AKTIF",  G),
        ("⬡", "Browsing Internet","AKTIF", G),
        ("⬡", "Mode Proaktif",   "AKTIF",  G),
        ("⬡", "Memori Permanen", "AKTIF",  G),
        ("⬡", "Edge-TTS Premium","AKTIF",  G),
    ]
    for ikon, nama, status, warna in fitur:
        baris = f"  {ikon} {nama:<20}  {status}"
        sisa  = LEBAR - len(baris) - 1
        print(C + "║" + warna + baris + " " * sisa + C + "║")

    print(C + "╚" + garis + "╝")
    print()


# ==============================================================
# STATUS — notifikasi satu baris dengan ikon & warna per tipe
# ==============================================================
_STATUS_CFG = {
    "info":      (Fore.CYAN,    "·", False),
    "sukses":    (Fore.GREEN,   "✓", True),
    "peringatan":(Fore.YELLOW,  "!", True),
    "error":     (Fore.RED,     "✗", True),
    "ai":        (Fore.MAGENTA, "◈", True),
    "deteksi":   (Fore.YELLOW,  "⚡", True),
    "browsing":  (Fore.BLUE,    "◎", True),
    "wake":      (Fore.CYAN,    "◉", True),
    "vision":    (Fore.MAGENTA, "◑", True),
    "memori":    (Fore.GREEN,   "◆", False),
}

def tampilkan_status(pesan: str, tipe: str = "info"):
    waktu           = datetime.now().strftime("%H:%M:%S")
    warna, ikon, bold = _STATUS_CFG.get(tipe, (Fore.WHITE, "?", False))
    tebal           = Style.BRIGHT if bold else ""
    for i, baris in enumerate(pesan.splitlines()):
        if i == 0:
            print(f"{Fore.CYAN}[{waktu}]{RST} {warna}{tebal}[{ikon}] {baris}{RST}")
        else:
            print(f"          {warna}    {baris}{RST}")


# ==============================================================
# SPEECH BUBBLE FRIDAY
# ==============================================================
def tampilkan_friday_bicara(teks: str):
    print()
    lebar_bubble = LEBAR - 4
    print(C + "  ╔══ " + W + "FRIDAY" + C + " " + "═" * (lebar_bubble - 7) + "╗")
    # Pecah teks per kalimat
    kalimat_list = []
    for bagian in teks.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|'):
        bagian = bagian.strip()
        if not bagian:
            continue
        # Wrap panjang > lebar_bubble
        while len(bagian) > lebar_bubble:
            kalimat_list.append(bagian[:lebar_bubble])
            bagian = bagian[lebar_bubble:]
        if bagian:
            kalimat_list.append(bagian)
    for k in kalimat_list:
        padding = lebar_bubble - len(k)
        print(C + "  ║  " + W + k + " " * padding + C + "  ║")
    print(C + "  ╚" + "═" * (lebar_bubble + 2) + "╝")
    print()


# ==============================================================
# USER BERBICARA
# ==============================================================
def tampilkan_user_bicara(teks: str):
    print()
    print(G + "  ▶  ANDA : " + RST + W + teks)
    print()


# ==============================================================
# DIVIDER
# ==============================================================
def tampilkan_divider():
    print(C + DIM + "  " + "─" * 54)


# ==============================================================
# MENDENGARKAN — pulse indicator
# ==============================================================
def tampilkan_mendengarkan():
    print()
    print(G + "  ╔" + "═" * 52 + "╗")
    print(G + "  ║" + W + "        ◉  MENDENGARKAN — bicara sekarang      " + " " * 5 + G + "║")
    print(G + "  ╚" + "═" * 52 + "╝")
    print()


# ==============================================================
# MEMPROSES — Gemini
# ==============================================================
def tampilkan_memproses():
    print(M + "  ⟳  Memproses via Gemini AI..." + RST)


# ==============================================================
# BERITA — panel pop-up
# ==============================================================
def pop_up_berita(daftar_berita: list):
    if not daftar_berita:
        return
    print()
    print(Y + "  ╔══ " + W + "📡 BERITA TERKINI" + Y + " " + "═" * 33 + "╗")
    for i, berita in enumerate(daftar_berita, 1):
        pendek  = (berita[:50] + "..") if len(berita) > 52 else berita
        padding = " " * (52 - len(pendek))
        print(Y + "  ║ " + W + f"{i}. {pendek}" + padding + Y + " ║")
    print(Y + "  ╚" + "═" * 54 + "╝")
    print()


# ==============================================================
# BROWSING — panel biru
# ==============================================================
def tampilkan_browsing(query: str):
    print()
    print(B + "  ╔══ " + W + "◎ BROWSING INTERNET" + B + " " + "═" * 30 + "╗")
    pendek  = (query[:50] + "..") if len(query) > 52 else query
    padding = " " * (52 - len(pendek))
    print(B + "  ║  " + Fore.CYAN + f"🔍  {pendek}" + " " * (52 - len(pendek) - 4) + B + " ║")
    print(B + "  ╚" + "═" * 54 + "╝")
    print()


# ==============================================================
# VISION — panel magenta
# ==============================================================
def tampilkan_vision():
    print()
    print(M + "  ╔══ " + W + "◑ FRIDAY VISION — ANALISIS GAMBAR" + M + " " * 15 + "╗")
    print(M + "  ║  " + W + "Kamera sedang diproses oleh Gemini Vision..." +
          " " * 9 + M + " ║")
    print(M + "  ╚" + "═" * 54 + "╝")
    print()


# ==============================================================
# APP DIBUKA — panel hijau
# ==============================================================
def tampilkan_app_dibuka(nama_app: str):
    print()
    print(G + "  ╔══ " + W + "▶ MEMBUKA APLIKASI" + G + " " + "═" * 31 + "╗")
    baris   = f"  Launching: {nama_app}"
    padding = " " * (52 - len(baris))
    print(G + "  ║" + W + baris + padding + G + " ║")
    print(G + "  ╚" + "═" * 54 + "╝")
    print()


# ==============================================================
# MUSIK — panel ungu
# ==============================================================
def tampilkan_musik(aksi: str, detail: str = ""):
    UNGU = Fore.MAGENTA + Style.BRIGHT
    print()
    print(UNGU + "  ╔══ " + W + "♪ MUSIK KONTROL" + UNGU + " " + "═" * 34 + "╗")
    baris = f"  {aksi}"
    if detail:
        baris += f": {detail}"
    pendek  = (baris[:50] + "..") if len(baris) > 52 else baris
    padding = " " * (52 - len(pendek))
    print(UNGU + "  ║" + W + pendek + padding + UNGU + " ║")
    print(UNGU + "  ╚" + "═" * 54 + "╝")
    print()


# ==============================================================
# STATISTIK
# ==============================================================
def tampilkan_statistik(stats: dict):
    print()
    print(G + "  ╔══ " + W + "📊 STATISTIK HARI INI" + G + " " + "═" * 29 + "╗")
    items = [
        ("Total Interaksi",   stats.get("interaksi", 0)),
        ("Browsing Internet", stats.get("browsing",  0)),
        ("Skill Lokal",       stats.get("skill",     0)),
        ("Riset Mendalam",    stats.get("riset",     0)),
        ("Deteksi Wajah",     stats.get("wajah",     0)),
    ]
    for label, nilai in items:
        baris   = f"  • {label:<24} {nilai}"
        padding = " " * (52 - len(baris))
        print(G + "  ║" + W + baris + padding + G + " ║")
    print(G + "  ╚" + "═" * 54 + "╝")
    print()
