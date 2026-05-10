# ==============================================================
# modules/dashboard.py — Project Friday | Web Dashboard JARVIS
# Versi : 1.1.0 — HTTP server lokal (fix Chrome blokir file://)
# ==============================================================
"""
Cara kerja:
  1. Friday jalankan mini HTTP server di background thread (port 8765)
  2. Setiap request → kirim HTML terbaru
  3. Chrome dibuka ke http://localhost:8765
  4. HTML auto-refresh setiap 30 detik → selalu data terbaru
"""

import os
import threading
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8765
_TMPDIR = os.environ.get("TMPDIR") or "/tmp"

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

    berita_items = ""
    for i, b in enumerate(berita[:6], 1):
        judul = (b[:90] + "…") if len(b) > 90 else b
        # Tentukan warna berdasarkan sumber
        if "🇮🇩" in b:
            dot_color = "#00ff88"   # hijau = Indonesia
        elif any(f in b for f in ("🌍","🇺🇸","🇬🇧","🇶🇦","💻")):
            dot_color = "#00e5ff"   # cyan = internasional
        else:
            dot_color = "#ff9800"   # orange = newsapi / lainnya
        nomor = f"0{i}" if i < 10 else str(i)
        berita_items += (
            f'<div class="news-row">'
            f'<span class="n-idx" style="color:{dot_color};">{nomor}</span>'
            f'<span class="n-txt">{judul}</span>'
            f'</div>'
        )
    if not berita_items:
        berita_items = '<div class="news-row"><span class="n-idx">--</span><span class="n-txt">Menghubungi server berita...</span></div>'

    status_color = {"Standby":"#00e5ff","Mendengarkan":"#00ff88","Memproses":"#ff9800","Berbicara":"#c850ff"}.get(status,"#00e5ff")

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta http-equiv="refresh" content="30">
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
.news-row{{display:flex;gap:10px;padding:6px 0;border-bottom:1px solid rgba(0,229,255,0.06);font-size:11px;color:rgba(255,255,255,0.8);align-items:flex-start;}}
.news-row:last-child{{border:none;}}
.n-idx{{color:#ff9800;font-weight:bold;min-width:18px;font-size:10px;margin-top:1px;}}
.n-txt{{line-height:1.4;}}

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

  <!-- Arc Reactor + Logo -->
  <div class="reactor-wrap">
    <div class="reactor">
      <div class="ring r1"></div><div class="ring r2"></div>
      <div class="ring r3"></div><div class="ring r4"></div>
    </div>
  </div>
  <div class="logo-wrap"><span class="logo">FRIDAY</span></div>
  <div class="logo-sub">AI PERSONAL ASSISTANT &nbsp;·&nbsp; v4.0 PREMIUM</div>

  <!-- Status -->
  <div class="status-bar">
    <div class="sdot"></div>
    <span class="slabel">SYS&nbsp;</span>
    <span class="sval">{status.upper()}</span>
    <span style="margin-left:auto;color:rgba(0,229,255,0.4);font-size:10px;">BOS {nama.upper()}</span>
  </div>

  <!-- Ticker -->
  <div class="ticker-wrap">
    <span class="ticker">◈ FRIDAY AI AKTIF &nbsp;&nbsp; ◈ GEMINI 2.5 FLASH &nbsp;&nbsp; ◈ EDGE-TTS PREMIUM &nbsp;&nbsp; ◈ SISTEM NORMAL &nbsp;&nbsp; ◈ SELAMAT DATANG BOS {nama.upper()} &nbsp;&nbsp; ◈ {updated} &nbsp;&nbsp;</span>
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
    <div class="sys-row"><span class="sn">Gemini AI 2.5</span><span class="son">ONLINE</span></div>
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


class _Handler(BaseHTTPRequestHandler):
    """Serve HTML dashboard untuk setiap request GET."""
    def do_GET(self):
        html = _generate_html().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, *args):
        pass   # Matikan log bawaan HTTPServer agar tidak spam terminal


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
    """Start HTTP server lalu buka http://localhost:PORT di Chrome."""
    _start_server()

    import time
    time.sleep(0.5)   # beri server waktu bind

    url = f"http://localhost:{PORT}"

    cmds = [
        # Chrome — package name yang umum di Android
        ["am", "start", "-a", "android.intent.action.VIEW",
         "-d", url, "-p", "com.android.chrome"],
        ["am", "start", "-a", "android.intent.action.VIEW",
         "-d", url, "-p", "com.google.android.apps.chrome"],
        # Browser default via termux-open-url
        ["termux-open-url", url],
        # xdg-open fallback
        ["xdg-open", url],
    ]

    for cmd in cmds:
        try:
            subprocess.Popen(cmd,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue

    return False


def refresh_dashboard(waktu="", cuaca="", cuaca_data=None,
                      berita=None, status="", aktivitas=""):
    """Update data — server otomatis sajikan HTML terbaru di request berikutnya."""
    update_data(waktu=waktu, cuaca=cuaca, cuaca_data=cuaca_data,
                berita=berita, status=status, aktivitas=aktivitas)


def tutup_dashboard():
    """Tutup Chrome dan hentikan HTTP server saat Friday dimatikan."""
    # Tutup Chrome (coba kedua package name)
    for pkg in ("com.android.chrome", "com.google.android.apps.chrome"):
        try:
            subprocess.run(["am", "force-stop", pkg],
                           capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
