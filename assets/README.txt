═══════════════════════════════════════════════
CARA MENAMBAHKAN LOGO & ANIMASI CUSTOM KE DASHBOARD
═══════════════════════════════════════════════

Taruh file di folder ini (assets/) dengan nama PERSIS seperti di bawah.
Dashboard (http://localhost:8765) otomatis memakainya — TIDAK perlu
ubah kode apa pun. Kalau file belum ada, dashboard tetap tampil normal
pakai animasi arc-reactor bawaan.

1. LOGO STATIS (ditampilkan saat status Standby):
   assets/logo.png   (atau .jpg / .jpeg / .svg / .webp)

2. ANIMASI (ditampilkan saat Friday aktif — Mendengarkan / Memproses /
   Berbicara / Browsing / Riset / Vision), opsional:
   assets/logo_animasi.gif   (atau .webp / .mp4 / .webm)

CONTOH STRUKTUR:
   assets/
   ├── logo.png
   └── logo_animasi.gif

Rekomendasi ukuran: persegi, minimal 300x300px, background transparan
(PNG/WEBP/GIF) supaya menyatu dengan tema gelap dashboard.

Setelah menaruh file, cukup refresh tab dashboard di browser — tidak
perlu restart Friday.
