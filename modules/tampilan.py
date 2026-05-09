# ==============================================================
# modules/tampilan.py — Project Friday | Tampilan Terminal
# Versi : 3.0.0 — Tambah indikator wake word, vision, proaktif
# ==============================================================

import os
from colorama import Fore, Back, Style, init
from datetime import datetime

init(autoreset=True)

VERSION   = "4.0.0"
LEBAR_BOX = 54


def bersihkan_layar():
    os.system('clear')


def tampilkan_header():
    bersihkan_layar()
    sekarang = datetime.now().strftime("%d %B %Y  |  %H:%M:%S")

    print(Fore.CYAN + Style.BRIGHT + "╔" + "═" * LEBAR_BOX + "╗")
    print(Fore.CYAN + Style.BRIGHT + "║" + Fore.WHITE + Style.BRIGHT +
          "   ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗   " + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "║" + Fore.CYAN + Style.BRIGHT +
          "   ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝   " + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "║" + Fore.WHITE + Style.BRIGHT +
          "   █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝    " + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "║" + Fore.CYAN + Style.BRIGHT +
          "   ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝     " + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "║" + Fore.WHITE + Style.BRIGHT +
          "   ██║     ██║  ██║██║██████╔╝██║  ██║   ██║       " + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "╠" + "═" * LEBAR_BOX + "╣")
    print(Fore.CYAN + Style.BRIGHT + "║" + Fore.GREEN +
          f"   AI Personal Assistant  •  v{VERSION}  PREMIUM    " + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "║" + Fore.YELLOW +
          f"   {sekarang:<50}" + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "╠" + "═" * LEBAR_BOX + "╣")

    fitur = [
        ("Kamera & Vision", "ONLINE"),
        ("Gemini AI 2.5",   "ONLINE"),
        ("Wake Word",       "AKTIF"),
        ("Pengenalan Wajah","AKTIF"),
        ("Browsing Internet","AKTIF"),
        ("Mode Proaktif",   "AKTIF"),
        ("Memori Permanen", "AKTIF"),
        ("Edge-TTS Premium","AKTIF"),
    ]
    for nama, status in fitur:
        nama_pad   = nama.ljust(18)
        status_pad = status.ljust(7)
        print(Fore.CYAN + Style.BRIGHT + "║" +
              Fore.GREEN + "  [●] " + Fore.WHITE + nama_pad + ": " +
              Fore.GREEN + status_pad + " " * 16 + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "╚" + "═" * LEBAR_BOX + "╝")
    print()


def tampilkan_status(pesan: str, tipe: str = "info"):
    waktu = datetime.now().strftime("%H:%M:%S")
    prefix_map = {
        "info":      (Fore.CYAN,    "[•]"),
        "sukses":    (Fore.GREEN,   "[✓]"),
        "peringatan":(Fore.YELLOW,  "[!]"),
        "error":     (Fore.RED,     "[✗]"),
        "ai":        (Fore.MAGENTA, "[AI]"),
        "deteksi":   (Fore.YELLOW,  "[👁]"),
        "browsing":  (Fore.BLUE,    "[🌐]"),
        "wake":      (Fore.CYAN,    "[🎯]"),
        "vision":    (Fore.MAGENTA, "[📷]"),
        "memori":    (Fore.GREEN,   "[💾]"),
    }
    warna, simbol = prefix_map.get(tipe, (Fore.WHITE, "[?]"))
    print(f"{Fore.CYAN}[{waktu}] {warna}{Style.BRIGHT}{simbol} {Style.RESET_ALL}{pesan}")


def tampilkan_friday_bicara(teks: str):
    print()
    print(Fore.CYAN + Style.BRIGHT + "  ┌─ FRIDAY ──────────────────────────────────")
    for baris in teks.split('. '):
        if baris.strip():
            print(Fore.CYAN + Style.BRIGHT + "  │ " + Style.RESET_ALL + Fore.WHITE + baris.strip())
    print(Fore.CYAN + Style.BRIGHT + "  └───────────────────────────────────────────")
    print()


def tampilkan_user_bicara(teks: str):
    print(Fore.GREEN + Style.BRIGHT + "  ► USER : " + Style.RESET_ALL + teks)


def tampilkan_divider():
    print(Fore.CYAN + Style.DIM + "  " + "─" * 50)


def pop_up_berita(daftar_berita: list):
    print()
    print(Fore.CYAN + Style.BRIGHT + "  ╔" + "═" * 50 + "╗")
    print(Fore.CYAN + Style.BRIGHT + "  ║" + Fore.YELLOW + Style.BRIGHT +
          "    📡  GLOBAL TECHNOLOGY NEWS FEED          " + Fore.CYAN + "║")
    print(Fore.CYAN + Style.BRIGHT + "  ╠" + "═" * 50 + "╣")
    for berita in daftar_berita:
        teks_singkat = (berita[:46] + "..") if len(berita) > 48 else berita
        padding = " " * (48 - len(teks_singkat))
        print(Fore.CYAN + Style.BRIGHT + "  ║ " + Fore.WHITE + teks_singkat + padding +
              Fore.CYAN + " ║")
    print(Fore.CYAN + Style.BRIGHT + "  ╚" + "═" * 50 + "╝")
    print()


def tampilkan_browsing(query: str):
    print()
    print(Fore.BLUE + Style.BRIGHT + "  ╔" + "═" * 50 + "╗")
    print(Fore.BLUE + Style.BRIGHT + "  ║" + Fore.WHITE + Style.BRIGHT +
          "    🌐  FRIDAY SEDANG BROWSING INTERNET       " + Fore.BLUE + "║")
    print(Fore.BLUE + Style.BRIGHT + "  ╠" + "═" * 50 + "╣")
    singkat = (query[:46] + "..") if len(query) > 48 else query
    padding = " " * (48 - len(singkat))
    print(Fore.BLUE + Style.BRIGHT + "  ║ " + Fore.CYAN + f"🔍 {singkat}" + padding +
          Fore.BLUE + " ║")
    print(Fore.BLUE + Style.BRIGHT + "  ╚" + "═" * 50 + "╝")
    print()


def tampilkan_vision():
    print()
    print(Fore.MAGENTA + Style.BRIGHT + "  ╔" + "═" * 50 + "╗")
    print(Fore.MAGENTA + Style.BRIGHT + "  ║" + Fore.WHITE + Style.BRIGHT +
          "    📷  FRIDAY VISION — MENGANALISIS GAMBAR   " + Fore.MAGENTA + "║")
    print(Fore.MAGENTA + Style.BRIGHT + "  ╚" + "═" * 50 + "╝")
    print()


def tampilkan_mendengarkan():
    print(Fore.GREEN + Style.BRIGHT + "\n  ◉  Mendengarkan... (bicara sekarang)\n")


def tampilkan_memproses():
    print(Fore.MAGENTA + Style.BRIGHT + "  ⟳  Menghubungi Gemini AI...\n")


def tampilkan_statistik(stats: dict):
    print()
    print(Fore.GREEN + Style.BRIGHT + "  ╔" + "═" * 50 + "╗")
    print(Fore.GREEN + Style.BRIGHT + "  ║" + Fore.WHITE + Style.BRIGHT +
          "    📊  STATISTIK FRIDAY HARI INI             " + Fore.GREEN + "║")
    print(Fore.GREEN + Style.BRIGHT + "  ╠" + "═" * 50 + "╣")
    items = [
        ("Total Interaksi", stats.get("interaksi", 0)),
        ("Browsing Internet", stats.get("browsing", 0)),
        ("Deteksi Wajah", stats.get("wajah", 0)),
    ]
    for label, nilai in items:
        line = f"  • {label:<25}: {nilai}"
        padding = " " * (50 - len(line))
        print(Fore.GREEN + Style.BRIGHT + "  ║" + Fore.WHITE + line + padding +
              Fore.GREEN + "║")
    print(Fore.GREEN + Style.BRIGHT + "  ╚" + "═" * 50 + "╝")
    print()
