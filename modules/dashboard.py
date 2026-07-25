# ==============================================================
# modules/dashboard.py — Project Friday | Web Dashboard JARVIS
# Versi : 2.0.0 — Dukungan logo & animasi custom (folder assets/)
# ==============================================================
"""
Cara kerja:
  1. Friday jalankan mini HTTP server di background thread (port 8765)
  2. Setiap request → kirim HTML terbaru
  3. Browser default dibuka ke http://localhost:8765
  4. HTML auto-refresh setiap 15 detik → selalu data terbaru

Logo & animasi custom (opsional):
  Taruh file berikut di folder assets/ (folder ini di root project,
  sejajar dengan main.py) — dashboard OTOMATIS memakainya kalau ada,
  dan tetap pakai tampilan arc-reactor bawaan kalau belum ada:

    assets/logo.(png|jpg|jpeg|svg|webp)
        → logo statis, ditampilkan saat status Standby.

    assets/logo_animasi.(gif|webp|mp4|webm)
        → ditampilkan menggantikan logo statis saat Friday aktif
          (Mendengarkan / Memproses / Berbicara / Browsing / Riset / Vision).

  Tidak perlu ubah kode apa pun — cukup taruh file dengan nama itu,
  lalu refresh/buka ulang dashboard.
"""

import os
import html as _html_lib
import mimetypes
import threading
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8765
_TMPDIR = os.environ.get("TMPDIR") or "/tmp"

# Folder assets/ di root project (satu level di atas folder modules/)
ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
)
os.makedirs(ASSETS_DIR, exist_ok=True)

_LOGO_EXT      = ("png", "jpg", "jpeg", "svg", "webp")
_ANIMASI_EXT   = ("gif", "webp", "mp4", "webm")


def _cari_asset(basename: str, ekstensi: tuple) -> str | None:
    """Cari file assets/<basename>.<ext> — return nama file relatif jika ketemu."""
    for ext in ekstensi:
        fname = f"{basename}.{ext}"
        if os.path.isfile(os.path.join(ASSETS_DIR, fname)):
            return fname
    return None

_data = {
    "nama"       : "Angga",
    "waktu"      : "",
    "cuaca"      : "",        # string untuk diucapkan
    "cuaca_data" : {},        # dict: suhu, kondisi, kelembaban, ikon, nama
    "berita"     : [],
    "status"     : "Standby",
    "aktivitas"  : "",
}
_server_started = False
_server_lock    = threading.Lock()


def update_data(nama="", waktu="", cuaca="", cuaca_data=None,
                berita=None, status="", aktivitas=""):
    """Perbarui data dashboard."""
    if nama:                    _data["nama"]       = nama
    if waktu:                   _data["waktu"]      = waktu
    if cuaca:                   _data["cuaca"]      = cuaca
    if cuaca_data is not None:  _data["cuaca_data"] = cuaca_data
    if berita is not None:      _data["berita"]     = berita
    if status:                  _data["status"]     = status
    if aktivitas:               _data["aktivitas"]  = aktivitas


def _generate_html() -> str:
    """Return HTML dashboard JARVIS Iron Man style — dipanggil tiap request HTTP."""
    nama    = _data.get("nama", "Angga")
    berita  = _data.get("berita", [])
    status  = _data.get("status", "Standby")
    updated = datetime.now().strftime("%H:%M:%S")

    # Cuaca: pakai cuaca_data jika tersedia, fallback ke text
    cd      = _data.get("cuaca_data", {})
    c_suhu  = cd.get("suhu", "--")
    c_rasa  = cd.get("rasa", "--")
    c_lembab= cd.get("kelembaban", "--")
    c_kond  = cd.get("kondisi", _data.get("cuaca", "Memuat..."))
    c_ikon  = cd.get("ikon", "🌡️")
    c_kota  = cd.get("nama", "")

    def _esc(s):
        return _html_lib.escape(str(s or ""), quote=True)

    berita_items = ""
    for i, b in enumerate(berita[:6], 1):
        # Backwards compatible: terima dict ATAU string
        if isinstance(b, dict):
            judul    = b.get("judul", "")
            sumber   = b.get("sumber", "")
            waktu_b  = b.get("waktu", "")
            ringkas  = b.get("ringkasan", "")
            url_b    = b.get("url", "")
        else:
            judul, sumber, waktu_b, ringkas, url_b = str(b), "", "", "", ""

        # Tentukan warna berdasarkan sumber
        gabung_chk = f"{sumber} {judul}"
        if "🇮🇩" in gabung_chk:
            dot_color = "#00ff88"   # hijau = Indonesia
        elif any(f in gabung_chk for f in ("🌍","🇺🇸","🇬🇧","🇶🇦","💻")):
            dot_color = "#00e5ff"   # cyan = internasional
        else:
            dot_color = "#ff9800"   # orange = newsapi / lainnya

        nomor = f"0{i}" if i < 10 else str(i)
        link_html = (
            f'<a class="n-link" href="{_esc(url_b)}" target="_blank" '
            f'rel="noopener noreferrer">Buka →</a>'
            if url_b else
            '<span class="n-link" style="opacity:0.3;cursor:default;">— offline</span>'
        )
        berita_items += (
            f'<div class="news-card">'
            f'  <div class="news-head">'
            f'    <span class="n-idx" style="color:{dot_color};">{nomor}</span>'
            f'    <span class="n-src" style="color:{dot_color};">{_esc(sumber)}</span>'
            f'    <span class="n-time">{_esc(waktu_b)}</span>'
            f'  </div>'
            f'  <div class="n-title">{_esc(judul)}</div>'
            f'  <div class="n-summary">{_esc(ringkas)}</div>'
            f'  <div class="n-foot">{link_html}</div>'
            f'</div>'
        )
    if not berita_items:
        berita_items = (
            '<div class="news-card"><div class="n-title" style="color:rgba(0,229,255,0.5);">'
            'Menghubungi server berita...</div></div>'
        )

    status_color = {"Standby":"#00e5ff","Mendengarkan":"#00ff88","Memproses":"#ff9800","Berbicara":"#c850ff"}.get(status,"#00e5ff")

    # ── Logo/animasi custom (assets/logo.*, assets/logo_animasi.*) ──
    # Fallback otomatis ke arc-reactor CSS bawaan kalau belum ada aset.
    logo_file    = _cari_asset("logo", _LOGO_EXT)
    animasi_file = _cari_asset("logo_animasi", _ANIMASI_EXT)

    if logo_file:
        if animasi_file and animasi_file.rsplit(".", 1)[1] in ("mp4", "webm"):
            animasi_tag = (
                f'<video id="logoAnim" src="/assets/{animasi_file}" '
                f'autoplay loop muted playsinline style="display:none;" '
                f'class="logo-custom"></video>'
            )
        elif animasi_file:
            animasi_tag = (
                f'<img id="logoAnim" src="/assets/{animasi_file}" '
                f'style="display:none;" class="logo-custom" alt="Friday">'
            )
        else:
            animasi_tag = ""

        # Ring animasi ala JARVIS (berputar + glow berdenyut) dibungkus
        # DI BELAKANG logo custom — logo & tulisannya tetap tegak/jelas,
        # tidak ikut berputar seperti gambar aslinya.
        logo_html = (
            '<div class="reactor-wrap">'
            '  <div class="hud-wrap">'
            '    <div class="hud-ring hud-ring-out"></div>'
            '    <div class="hud-ring hud-ring-in"></div>'
            f'    <img id="logoStatic" src="/assets/{logo_file}" class="logo-custom" alt="Friday">'
            f'    {animasi_tag}'
            '  </div>'
            '</div>'
        )
    else:
        # Fallback: arc-reactor CSS bawaan (tidak ada aset custom)
        logo_html = (
            '<div class="reactor-wrap">'
            '  <div class="reactor">'
            '    <div class="ring r1"></div><div class="ring r2"></div>'
            '    <div class="ring r3"></div><div class="ring r4"></div>'
            '  </div>'
            '</div>'
        )

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta http-equiv="refresh" content="15">
<title>FRIDAY — JARVIS INTERFACE</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
body{{background:#000;color:#00e5ff;font-family:'Share Tech Mono',monospace;min-height:100vh;overflow-x:hidden;}}
canvas#bg{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;}}
.wrap{{position:relative;z-index:2;padding:12px;}}

/* ── Scan line ── */
.scanline{{position:fixed;top:0;left:0;width:100%;height:3px;background:linear-gradient(90deg,transparent,rgba(0,229,255,0.6),transparent);animation:scan 4s linear infinite;z-index:10;pointer-events:none;}}
@keyframes scan{{0%{{top:-4px;}}100%{{top:100vh;}}}}

/* ── CRT overlay ── */
body::after{{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,229,255,0.012) 2px,rgba(0,229,255,0.012) 4px);pointer-events:none;z-index:5;}}

/* ── Corner brackets ── */
.corner{{position:fixed;width:28px;height:28px;z-index:6;}}
.corner.tl{{top:8px;left:8px;border-top:2px solid #00e5ff;border-left:2px solid #00e5ff;animation:cblink 3s infinite;}}
.corner.tr{{top:8px;right:8px;border-top:2px solid #00e5ff;border-right:2px solid #00e5ff;animation:cblink 3s 0.75s infinite;}}
.corner.bl{{bottom:8px;left:8px;border-bottom:2px solid #00e5ff;border-left:2px solid #00e5ff;animation:cblink 3s 1.5s infinite;}}
.corner.br{{bottom:8px;right:8px;border-bottom:2px solid #00e5ff;border-right:2px solid #00e5ff;animation:cblink 3s 2.25s infinite;}}
@keyframes cblink{{0%,100%{{opacity:1;box-shadow:0 0 6px #00e5ff;}}50%{{opacity:0.4;box-shadow:none;}}}}

/* ── Arc Reactor ── */
.reactor-wrap{{display:flex;justify-content:center;margin:10px 0 14px;}}

/* ── HUD wrap: bungkus logo custom dengan ring animasi ala JARVIS ── */
.hud-wrap{{position:relative;width:150px;height:150px;display:flex;align-items:center;justify-content:center;}}
.logo-custom{{position:relative;z-index:2;max-width:120px;max-height:120px;width:auto;height:auto;object-fit:contain;
  filter:drop-shadow(0 0 10px rgba(255,140,0,0.55));
  animation:hud-pulse 2.4s ease-in-out infinite;}}
.hud-ring{{position:absolute;border-radius:50%;z-index:1;}}
.hud-ring-out{{inset:0;border:2px dashed rgba(255,140,0,0.55);
  animation:hud-spin 10s linear infinite;}}
.hud-ring-in{{inset:16px;border:2px solid transparent;border-top-color:rgba(0,229,255,0.6);
  border-right-color:rgba(0,229,255,0.6);
  animation:hud-spin 4s linear infinite reverse;}}
@keyframes hud-spin{{to{{transform:rotate(360deg);}}}}
@keyframes hud-pulse{{
  0%,100%{{filter:drop-shadow(0 0 10px rgba(255,140,0,0.55));transform:scale(1);}}
  50%{{filter:drop-shadow(0 0 20px rgba(255,140,0,0.85));transform:scale(1.03);}}
}}
/* Saat Friday aktif (bukan Standby) — ring berputar lebih cepat & glow lebih kuat */
.hud-wrap.aktif .hud-ring-out{{animation-duration:3s;border-color:rgba(255,140,0,0.9);}}
.hud-wrap.aktif .hud-ring-in{{animation-duration:1.3s;}}
.hud-wrap.aktif .logo-custom{{animation-duration:0.9s;}}
.reactor{{position:relative;width:88px;height:88px;}}
.ring{{position:absolute;border-radius:50%;border:2px solid transparent;}}
.r1{{inset:0;border-color:#00e5ff;animation:spin1 6s linear infinite;box-shadow:0 0 12px #00e5ff;}}
.r2{{inset:8px;border-color:rgba(0,229,255,0.5);border-style:dashed;animation:spin1 4s linear infinite reverse;}}
.r3{{inset:18px;border-color:#00bcd4;animation:spin1 3s linear infinite;}}
.r4{{inset:28px;border-radius:50%;background:radial-gradient(circle,#fff 0%,#00e5ff 40%,rgba(0,229,255,0.1) 70%,transparent 100%);animation:pulse-r 2s ease-in-out infinite;}}
@keyframes spin1{{to{{transform:rotate(360deg);}}}}
@keyframes pulse-r{{0%,100%{{box-shadow:0 0 20px #00e5ff,0 0 40px rgba(0,229,255,0.4);}}50%{{box-shadow:0 0 35px #00e5ff,0 0 60px rgba(0,229,255,0.7);}}}}

/* ── FRIDAY logo ── */
.logo-wrap{{text-align:center;margin-bottom:4px;}}
.logo{{font-family:'Orbitron',monospace;font-size:32px;font-weight:900;letter-spacing:10px;color:#fff;text-shadow:0 0 20px #00e5ff,0 0 40px rgba(0,229,255,0.5);display:inline-block;animation:glitch 8s infinite;}}
@keyframes glitch{{
  0%,94%,100%{{text-shadow:0 0 20px #00e5ff,0 0 40px rgba(0,229,255,0.5);transform:none;}}
  95%{{text-shadow:-2px 0 #ff003c,2px 0 #00e5ff;transform:skewX(-3deg);}}
  96%{{text-shadow:2px 0 #ff003c,-2px 0 #00e5ff;transform:skewX(3deg);}}
  97%{{text-shadow:0 0 20px #00e5ff;transform:none;}}
  98%{{text-shadow:-1px 0 #ff003c,1px 0 #00e5ff;transform:translateX(2px);}}
  99%{{text-shadow:0 0 20px #00e5ff;transform:none;}}
}}
.logo-sub{{font-size:9px;letter-spacing:5px;color:rgba(0,229,255,0.5);text-align:center;text-transform:uppercase;}}

/* ── Status ── */
.status-bar{{display:flex;align-items:center;gap:8px;background:rgba(0,229,255,0.04);border:1px solid rgba(0,229,255,0.2);padding:7px 12px;margin:10px 0;font-size:11px;position:relative;overflow:hidden;}}
.status-bar::after{{content:'';position:absolute;top:0;left:-100%;width:60%;height:100%;background:linear-gradient(90deg,transparent,rgba(0,229,255,0.07),transparent);animation:shimmer 3s infinite;}}
@keyframes shimmer{{to{{left:150%;}}}}
.sdot{{width:9px;height:9px;border-radius:50%;background:{status_color};box-shadow:0 0 10px {status_color};animation:pulse-s 1.5s ease-in-out infinite;flex-shrink:0;}}
@keyframes pulse-s{{0%,100%{{transform:scale(1);opacity:1;}}50%{{transform:scale(1.4);opacity:0.6;}}}}
.slabel{{color:rgba(0,229,255,0.45);font-size:10px;}}
.sval{{color:#fff;font-weight:bold;letter-spacing:2px;}}

/* ── Cards ── */
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;}}
.card{{background:rgba(0,8,16,0.85);border:1px solid rgba(0,229,255,0.2);padding:12px;position:relative;overflow:hidden;}}
.card::before{{content:'';position:absolute;top:0;left:0;width:2px;height:100%;background:linear-gradient(180deg,#00e5ff,transparent);}}
.card::after{{content:'';position:absolute;top:-100%;left:0;width:100%;height:100%;background:linear-gradient(180deg,transparent,rgba(0,229,255,0.04),transparent);animation:card-scan 5s linear infinite;}}
@keyframes card-scan{{to{{top:100%;}}}}
.ctitle{{font-family:'Orbitron',monospace;font-size:8px;letter-spacing:3px;color:rgba(0,229,255,0.4);text-transform:uppercase;margin-bottom:8px;}}
.time-big{{font-family:'Orbitron',monospace;font-size:40px;font-weight:700;color:#fff;text-shadow:0 0 25px rgba(0,229,255,0.9);line-height:1;}}
.date-s{{font-size:10px;color:rgba(0,229,255,0.55);margin-top:5px;text-transform:uppercase;letter-spacing:1px;}}
.weather-v{{font-size:13px;color:#e0f7fa;line-height:1.6;margin-top:4px;}}

/* ── Sys rows ── */
.sys-row{{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,229,255,0.06);font-size:10px;}}
.sys-row:last-child{{border:none;}}
.sn{{color:rgba(0,229,255,0.55);}}
.son{{color:#00ff88;font-size:9px;background:rgba(0,255,136,0.08);padding:1px 7px;border:1px solid rgba(0,255,136,0.25);letter-spacing:1px;}}

/* ── Progress bar ── */
.pbar-wrap{{margin-top:6px;}}
.pbar{{height:3px;background:rgba(0,229,255,0.1);margin:4px 0;position:relative;overflow:hidden;}}
.pbar-fill{{height:100%;background:linear-gradient(90deg,#00e5ff,#00ff88);animation:pload 3s ease-in-out infinite alternate;}}
@keyframes pload{{0%{{width:60%;}}100%{{width:95%;}}}}

/* ── News ── */
.news-wrap{{background:rgba(0,8,16,0.85);border:1px solid rgba(0,229,255,0.2);padding:12px;margin-bottom:10px;position:relative;overflow:hidden;}}
.news-wrap::before{{content:'';position:absolute;top:0;left:0;width:2px;height:100%;background:linear-gradient(180deg,#ff9800,transparent);}}
.news-card{{background:rgba(0,12,24,0.55);border:1px solid rgba(0,229,255,0.08);border-left:2px solid rgba(0,229,255,0.25);padding:8px 10px;margin:7px 0;transition:all .2s;}}
.news-card:hover{{background:rgba(0,18,32,0.75);border-left-color:#00e5ff;}}
.news-head{{display:flex;align-items:center;gap:8px;margin-bottom:4px;font-size:9px;letter-spacing:1px;}}
.n-idx{{font-weight:bold;font-family:'Orbitron',monospace;}}
.n-src{{font-weight:bold;text-transform:uppercase;font-size:9px;}}
.n-time{{margin-left:auto;color:rgba(0,229,255,0.4);font-size:9px;font-style:italic;}}
.n-title{{font-size:12px;color:#fff;font-weight:600;line-height:1.35;margin-bottom:4px;}}
.n-summary{{font-size:10px;color:rgba(255,255,255,0.55);line-height:1.4;margin-bottom:5px;}}
.n-foot{{text-align:right;}}
.n-link{{display:inline-block;font-size:9px;color:#00e5ff;text-decoration:none;letter-spacing:2px;padding:2px 8px;border:1px solid rgba(0,229,255,0.35);border-radius:2px;transition:all .2s;font-weight:bold;}}
.n-link:hover{{background:rgba(0,229,255,0.15);box-shadow:0 0 10px rgba(0,229,255,0.4);color:#fff;}}

/* ── Ticker ── */
.ticker-wrap{{overflow:hidden;background:rgba(0,229,255,0.04);border-top:1px solid rgba(0,229,255,0.15);border-bottom:1px solid rgba(0,229,255,0.15);padding:5px 0;margin-bottom:10px;}}
.ticker{{white-space:nowrap;display:inline-block;animation:tick 20s linear infinite;font-size:10px;color:rgba(0,229,255,0.6);letter-spacing:2px;}}
@keyframes tick{{0%{{transform:translateX(100vw);}}100%{{transform:translateX(-100%);}}}}

/* ── Radar ── */
.radar-wrap{{display:flex;justify-content:center;margin:4px 0 10px;}}
.radar{{width:70px;height:70px;position:relative;border-radius:50%;border:1px solid rgba(0,229,255,0.3);overflow:hidden;background:radial-gradient(circle,rgba(0,229,255,0.05) 0%,transparent 70%);}}
.radar::before,.radar::after{{content:'';position:absolute;}}
.radar::before{{inset:0;border-radius:50%;background:conic-gradient(from 0deg,rgba(0,255,136,0.35),transparent 60deg,transparent 360deg);animation:spin1 2.5s linear infinite;}}
.radar::after{{top:50%;left:0;width:100%;height:1px;background:rgba(0,229,255,0.2);}}
.radar-cross{{position:absolute;inset:0;}}
.radar-cross::before,.radar-cross::after{{content:'';position:absolute;background:rgba(0,229,255,0.15);}}
.radar-cross::before{{top:0;left:50%;width:1px;height:100%;}}
.radar-cross::after{{top:50%;left:0;width:100%;height:1px;}}

/* ── Footer ── */
.footer{{text-align:center;font-size:8px;color:rgba(0,229,255,0.2);padding:8px 0;letter-spacing:3px;text-transform:uppercase;}}
</style>
</head>
<body>
<canvas id="bg"></canvas>
<div class="scanline"></div>
<div class="corner tl"></div><div class="corner tr"></div>
<div class="corner bl"></div><div class="corner br"></div>

<div class="wrap">

  <!-- Arc Reactor / Logo custom -->
  {logo_html}
  <div class="logo-wrap"><span class="logo">FRIDAY</span></div>
  <div class="logo-sub">AI PERSONAL ASSISTANT &nbsp;·&nbsp; v5.0 PREMIUM</div>

  <!-- Status + Tombol STOP -->
  <div class="status-bar">
    <div class="sdot"></div>
    <span class="slabel">SYS&nbsp;</span>
    <span class="sval">{status.upper()}</span>
    <span style="margin-left:auto;display:flex;align-items:center;gap:10px;">
      <span style="color:rgba(0,229,255,0.4);font-size:10px;">BOS {nama.upper()}</span>
      <button id="stopBtn" onclick="stopFriday()"
        style="display:{"flex" if status=="Berbicara" else "none"};
        align-items:center;gap:5px;background:rgba(200,0,80,0.15);
        border:1px solid #c80050;color:#ff4488;padding:3px 10px;
        font-family:inherit;font-size:10px;letter-spacing:2px;cursor:pointer;
        animation:pulse-s 1s infinite;">
        ⏹ STOP
      </button>
    </span>
  </div>

  <!-- Ticker -->
  <div class="ticker-wrap">
    <span class="ticker">◈ FRIDAY AI AKTIF &nbsp;&nbsp; ◈ CLAUDE AI &nbsp;&nbsp; ◈ EDGE-TTS PREMIUM &nbsp;&nbsp; ◈ SISTEM NORMAL &nbsp;&nbsp; ◈ SELAMAT DATANG BOS {nama.upper()} &nbsp;&nbsp; ◈ {updated} &nbsp;&nbsp;</span>
  </div>

  <!-- Grid: Jam + Radar -->
  <div class="grid">
    <div class="card">
      <div class="ctitle">◷ WAKTU</div>
      <div class="time-big" id="clk">{datetime.now().strftime("%H:%M")}</div>
      <div class="date-s" id="dt">{datetime.now().strftime("%a, %d %b %Y")}</div>
    </div>
    <div class="card">
      <div class="ctitle">◎ RADAR</div>
      <div class="radar-wrap" style="margin:2px 0 6px;">
        <div class="radar"><div class="radar-cross"></div></div>
      </div>
      <div style="font-size:9px;color:rgba(0,229,255,0.4);text-align:center;">SCANNING AREA</div>
    </div>
  </div>

  <!-- Cuaca -->
  <div class="card" style="margin-bottom:10px;">
    <div class="ctitle">◈ KONDISI CUACA — {c_kota.upper() or "---"}</div>
    <div style="display:flex;align-items:center;gap:14px;margin:6px 0;">
      <div style="font-size:44px;line-height:1;">{c_ikon}</div>
      <div>
        <div style="font-family:'Orbitron',monospace;font-size:36px;font-weight:700;color:#fff;text-shadow:0 0 20px rgba(0,229,255,0.8);line-height:1;">{c_suhu}<span style="font-size:18px;">°C</span></div>
        <div style="font-size:10px;color:rgba(0,229,255,0.5);margin-top:2px;">TERASA {c_rasa}°C</div>
      </div>
    </div>
    <div style="font-size:11px;color:#e0f7fa;margin-bottom:6px;">{c_kond}</div>
    <div style="display:flex;gap:16px;font-size:9px;color:rgba(0,229,255,0.5);">
      <span>💧 KELEMBABAN {c_lembab}%</span>
    </div>
  </div>

  <!-- Sistem -->
  <div class="card" style="margin-bottom:10px;">
    <div class="ctitle">⬡ STATUS SISTEM</div>
    <div class="sys-row"><span class="sn">Claude AI</span><span class="son">ONLINE</span></div>
    <div class="sys-row"><span class="sn">Wake Word</span><span class="son">AKTIF</span></div>
    <div class="sys-row"><span class="sn">Kamera Vision</span><span class="son">ONLINE</span></div>
    <div class="sys-row"><span class="sn">Browsing Net</span><span class="son">AKTIF</span></div>
    <div class="sys-row"><span class="sn">Memori</span><span class="son">AKTIF</span></div>
    <div class="sys-row"><span class="sn">Edge-TTS</span><span class="son">AKTIF</span></div>
    <div class="pbar-wrap">
      <div class="pbar"><div class="pbar-fill" style="animation-delay:.5s"></div></div>
      <div class="pbar"><div class="pbar-fill" style="animation-delay:1s"></div></div>
    </div>
  </div>

  <!-- Berita -->
  <div class="news-wrap">
    <div class="ctitle" style="margin-bottom:6px;">
      📡 INTEL FEED &nbsp;
      <span style="color:#00ff88;font-size:8px;">🇮🇩 INDONESIA</span>
      &nbsp;+&nbsp;
      <span style="color:#00e5ff;font-size:8px;">🌍 INTERNASIONAL</span>
    </div>
    {berita_items}
  </div>

  <div class="footer">FRIDAY AI &nbsp;·&nbsp; ANGGA PROJECT &nbsp;·&nbsp; REFRESH 30s &nbsp;·&nbsp; {updated}</div>
</div>

<script>
// Live status polling setiap 4 detik — update status bar tanpa full reload
const STATUS_COLORS = {{
  'Standby'     :'#00e5ff',
  'Mendengarkan':'#00ff88',
  'Memproses'   :'#ff9800',
  'Berbicara'   :'#c850ff',
  'Browsing'    :'#2196f3',
  'Riset'       :'#ff9800',
  'Vision'      :'#c850ff',
}};
function pollStatus(){{
  fetch('/status').then(r=>r.json()).then(d=>{{
    const dot=document.querySelector('.sdot');
    const val=document.querySelector('.sval');
    const btn=document.getElementById('stopBtn');
    const col=STATUS_COLORS[d.status]||'#00e5ff';
    if(dot){{dot.style.background=col;dot.style.boxShadow='0 0 10px '+col;}}
    if(val)val.textContent=d.status.toUpperCase();
    if(btn)btn.style.display=d.status==='Berbicara'?'flex':'none';

    // Logo custom: tampilkan animasi selama Friday aktif, logo statis saat Standby
    const aktif = d.status !== 'Standby';
    const logoStatic=document.getElementById('logoStatic');
    const logoAnim=document.getElementById('logoAnim');
    if(logoStatic && logoAnim){{
      logoAnim.style.display   = aktif ? 'block' : 'none';
      logoStatic.style.display = aktif ? 'none'  : 'block';
      if(aktif && logoAnim.tagName==='VIDEO' && logoAnim.paused){{
        logoAnim.play().catch(()=>{{}});
      }}
    }}
    // Ring HUD ala JARVIS: berputar lebih cepat + glow lebih kuat saat aktif
    const hudWrap=document.querySelector('.hud-wrap');
    if(hudWrap) hudWrap.classList.toggle('aktif', aktif);
  }}).catch(()=>{{}});
}}
setInterval(pollStatus,4000);

// Barge-in: hentikan Friday
function stopFriday(){{
  fetch('/stop').then(()=>{{
    const btn=document.getElementById('stopBtn');
    if(btn){{btn.textContent='✓ DIHENTIKAN';btn.style.color='#00ff88';}}
    setTimeout(()=>location.reload(),1200);
  }}).catch(()=>{{}});
}}

// Live clock
function tick(){{
  const n=new Date();
  const c=document.getElementById('clk');
  const d=document.getElementById('dt');
  if(c)c.textContent=String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0');
  const days=['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'];
  const months=['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
  if(d)d.textContent=days[n.getDay()]+', '+n.getDate()+' '+months[n.getMonth()]+' '+n.getFullYear();
}}
setInterval(tick,1000);tick();

// Particle canvas background
(function(){{
  const cv=document.getElementById('bg');
  const ctx=cv.getContext('2d');
  let W,H,pts=[];
  function resize(){{W=cv.width=window.innerWidth;H=cv.height=window.innerHeight;}}
  resize();window.addEventListener('resize',resize);
  for(let i=0;i<55;i++)pts.push({{
    x:Math.random()*1200,y:Math.random()*2000,
    vx:(Math.random()-.5)*.4,vy:-Math.random()*.5-.1,
    r:Math.random()*1.5+.5,a:Math.random()
  }});
  function draw(){{
    ctx.clearRect(0,0,W,H);
    pts.forEach(p=>{{
      p.x+=p.vx;p.y+=p.vy;p.a+=.008;
      if(p.y<-5){{p.y=H+5;p.x=Math.random()*W;}}
      if(p.x<-5||p.x>W+5)p.vx*=-1;
      const op=(.4+.3*Math.sin(p.a));
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(0,229,255,${{op}})`;
      ctx.fill();
    }});
    // Hex grid subtle
    ctx.strokeStyle='rgba(0,229,255,0.03)';
    ctx.lineWidth=1;
    const s=40,h=s*Math.sqrt(3)/2;
    for(let row=-1;row<H/h+2;row++){{
      for(let col=-1;col<W/s+2;col++){{
        const ox=col*s*1.5,oy=row*h+(col%2?h/2:0);
        ctx.beginPath();
        for(let i=0;i<6;i++){{
          const a=Math.PI/3*i-Math.PI/6;
          i===0?ctx.moveTo(ox+s/2*Math.cos(a),oy+s/2*Math.sin(a))
               :ctx.lineTo(ox+s/2*Math.cos(a),oy+s/2*Math.sin(a));
        }}
        ctx.closePath();ctx.stroke();
      }}
    }}
    requestAnimationFrame(draw);
  }}
  draw();
}})();
</script>
</body>
</html>"""

    return html


# Callback untuk barge-in — di-set oleh main.py setelah import suara
_stop_callback = None

def set_stop_callback(fn):
    """Daftarkan fungsi stop_bicara() agar bisa dipanggil via endpoint /stop."""
    global _stop_callback
    _stop_callback = fn


class _Handler(BaseHTTPRequestHandler):
    """Serve HTML dashboard + endpoint /stop untuk barge-in."""

    def do_GET(self):
        if self.path == "/stop":
            if _stop_callback:
                try:
                    _stop_callback()
                except Exception:
                    pass
            self._json(b'{"ok":true}')
            return

        if self.path == "/status":
            import json
            from datetime import datetime
            payload = json.dumps({
                "status" : _data.get("status", "Standby"),
                "updated": datetime.now().strftime("%H:%M:%S"),
            }).encode("utf-8")
            self._json(payload)
            return

        if self.path.startswith("/assets/"):
            self._serve_asset(self.path[len("/assets/"):])
            return

        html = _generate_html().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def _serve_asset(self, nama_file: str):
        """Serve file statis dari folder assets/ (logo & animasi custom)."""
        # os.path.basename mencegah path traversal (mis. ../../secret.txt)
        nama_aman = os.path.basename(nama_file)
        path = os.path.join(ASSETS_DIR, nama_aman)

        if not os.path.isfile(path):
            self.send_response(404)
            self.end_headers()
            return

        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, payload: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


def _start_server():
    """Jalankan HTTP server di thread daemon — otomatis mati saat main.py berhenti."""
    global _server_started
    with _server_lock:
        if _server_started:
            return
        try:
            server = HTTPServer(("127.0.0.1", PORT), _Handler)
            _server_started = True
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
        except OSError:
            # Port sudah dipakai — server mungkin sudah jalan
            _server_started = True


def buka_dashboard():
    """Start HTTP server lalu buka http://localhost:PORT di browser default."""
    _start_server()

    import time
    time.sleep(0.5)   # beri server waktu bind

    url = f"http://localhost:{PORT}"

    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def refresh_dashboard(waktu="", cuaca="", cuaca_data=None,
                      berita=None, status="", aktivitas=""):
    """Update data — server otomatis sajikan HTML terbaru di request berikutnya."""
    update_data(waktu=waktu, cuaca=cuaca, cuaca_data=cuaca_data,
                berita=berita, status=status, aktivitas=aktivitas)


def tutup_dashboard():
    """
    Dipanggil saat Friday dimatikan. Tab dashboard di browser SENGAJA
    tidak ditutup paksa — di Windows itu berarti mematikan seluruh
    jendela/tab browser milik user, bukan cuma dashboard. HTTP server
    berhenti sendiri karena berjalan di daemon thread.
    """
    pass
