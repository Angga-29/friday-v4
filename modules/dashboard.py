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
    "nama"     : "Angga",
    "waktu"    : "",
    "cuaca"    : "",
    "berita"   : [],
    "status"   : "Standby",
    "aktivitas": "",
}
_server_started = False
_server_lock    = threading.Lock()


def update_data(nama="", waktu="", cuaca="", berita=None,
                status="", aktivitas=""):
    """Perbarui data dashboard dan regenerate HTML."""
    if nama:      _data["nama"]      = nama
    if waktu:     _data["waktu"]     = waktu
    if cuaca:     _data["cuaca"]     = cuaca
    if berita is not None: _data["berita"] = berita
    if status:    _data["status"]    = status
    if aktivitas: _data["aktivitas"] = aktivitas
    _generate_html()


def _generate_html() -> str:
    """Return HTML dashboard terbaru — dipanggil tiap request HTTP."""
    nama     = _data.get("nama", "Angga")
    waktu    = _data.get("waktu", datetime.now().strftime("%H:%M"))
    cuaca    = _data.get("cuaca", "—")
    berita   = _data.get("berita", [])
    status   = _data.get("status", "Standby")
    aktv     = _data.get("aktivitas", "")
    updated  = datetime.now().strftime("%H:%M:%S")

    # Berita jadi list item HTML
    berita_html = ""
    for i, b in enumerate(berita[:5], 1):
        berita_html += f'<div class="news-item"><span class="news-num">{i}</span>{b}</div>\n'
    if not berita_html:
        berita_html = '<div class="news-item">Memuat berita...</div>'

    # Status dot color
    dot_color = {
        "Standby": "#00bcd4",
        "Mendengarkan": "#4caf50",
        "Memproses": "#ff9800",
        "Berbicara": "#9c27b0",
    }.get(status, "#00bcd4")

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="60">
<title>FRIDAY — AI Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    background: #000;
    color: #00e5ff;
    font-family: 'Share Tech Mono', monospace;
    min-height: 100vh;
    overflow-x: hidden;
    background-image:
      radial-gradient(ellipse at 20% 50%, rgba(0,80,120,0.15) 0%, transparent 60%),
      radial-gradient(ellipse at 80% 20%, rgba(0,40,80,0.2) 0%, transparent 50%);
  }}

  /* Grid scan line efek */
  body::before {{
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0, 229, 255, 0.015) 2px,
      rgba(0, 229, 255, 0.015) 4px
    );
    pointer-events: none;
    z-index: 1;
  }}

  .container {{
    position: relative;
    z-index: 2;
    padding: 16px;
    max-width: 100%;
  }}

  /* ── Header ── */
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(0,229,255,0.3);
    padding-bottom: 12px;
    margin-bottom: 16px;
  }}

  .logo {{
    font-family: 'Orbitron', monospace;
    font-size: 28px;
    font-weight: 900;
    color: #00e5ff;
    text-shadow: 0 0 20px #00e5ff, 0 0 40px rgba(0,229,255,0.5);
    letter-spacing: 6px;
  }}

  .logo span {{ color: #fff; }}

  .header-right {{
    text-align: right;
    font-size: 11px;
    color: rgba(0,229,255,0.6);
    line-height: 1.6;
  }}

  /* ── Status bar ── */
  .status-bar {{
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(0,229,255,0.05);
    border: 1px solid rgba(0,229,255,0.2);
    border-radius: 4px;
    padding: 8px 14px;
    margin-bottom: 16px;
    font-size: 12px;
  }}

  .status-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: {dot_color};
    box-shadow: 0 0 8px {dot_color};
    animation: pulse 2s infinite;
  }}

  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.4; }}
  }}

  .status-label {{ color: rgba(0,229,255,0.5); }}
  .status-value {{ color: #fff; font-weight: bold; }}
  .status-activity {{ color: rgba(0,229,255,0.7); margin-left: auto; }}

  /* ── Grid cards ── */
  .grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
  }}

  .card {{
    background: rgba(0,10,20,0.8);
    border: 1px solid rgba(0,229,255,0.25);
    border-radius: 6px;
    padding: 14px;
    position: relative;
    overflow: hidden;
  }}

  .card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #00e5ff, transparent);
  }}

  .card-title {{
    font-family: 'Orbitron', monospace;
    font-size: 9px;
    letter-spacing: 3px;
    color: rgba(0,229,255,0.5);
    text-transform: uppercase;
    margin-bottom: 10px;
  }}

  /* Jam */
  .time-big {{
    font-family: 'Orbitron', monospace;
    font-size: 44px;
    font-weight: 700;
    color: #fff;
    text-shadow: 0 0 30px rgba(0,229,255,0.8);
    line-height: 1;
    letter-spacing: 2px;
  }}

  .date-sub {{
    font-size: 12px;
    color: rgba(0,229,255,0.6);
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}

  /* Cuaca */
  .weather-val {{
    font-size: 16px;
    color: #fff;
    line-height: 1.5;
    margin-top: 4px;
  }}

  /* Sistem status */
  .sys-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    border-bottom: 1px solid rgba(0,229,255,0.08);
    font-size: 11px;
  }}
  .sys-row:last-child {{ border-bottom: none; }}
  .sys-name {{ color: rgba(0,229,255,0.6); }}
  .sys-on {{
    color: #4caf50;
    font-size: 10px;
    background: rgba(76,175,80,0.1);
    padding: 1px 6px;
    border-radius: 10px;
    border: 1px solid rgba(76,175,80,0.3);
  }}

  /* Sapa */
  .greet-card {{
    background: linear-gradient(135deg, rgba(0,40,60,0.9), rgba(0,10,20,0.9));
    border: 1px solid rgba(0,229,255,0.4);
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 12px;
    text-align: center;
  }}

  .greet-text {{
    font-family: 'Orbitron', monospace;
    font-size: 15px;
    color: #fff;
    text-shadow: 0 0 15px rgba(0,229,255,0.6);
    letter-spacing: 2px;
  }}

  .greet-sub {{
    font-size: 11px;
    color: rgba(0,229,255,0.5);
    margin-top: 4px;
  }}

  /* Berita */
  .news-card {{
    background: rgba(0,10,20,0.8);
    border: 1px solid rgba(0,229,255,0.25);
    border-radius: 6px;
    padding: 14px;
    position: relative;
    overflow: hidden;
  }}

  .news-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #ff9800, transparent);
  }}

  .news-item {{
    display: flex;
    gap: 10px;
    padding: 7px 0;
    border-bottom: 1px solid rgba(0,229,255,0.08);
    font-size: 12px;
    color: rgba(255,255,255,0.85);
    line-height: 1.4;
    align-items: flex-start;
  }}
  .news-item:last-child {{ border-bottom: none; }}

  .news-num {{
    color: #ff9800;
    font-weight: bold;
    min-width: 16px;
    font-size: 11px;
    margin-top: 1px;
  }}

  /* Footer */
  .footer {{
    text-align: center;
    font-size: 9px;
    color: rgba(0,229,255,0.2);
    padding-top: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
  }}

  /* Live clock via JS */
  #live-clock {{ cursor: default; }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <div class="logo">FRI<span>DAY</span></div>
    <div class="header-right">
      AI PERSONAL ASSISTANT v4.0<br>
      POWERED BY GEMINI 2.5 FLASH<br>
      Updated: {updated}
    </div>
  </div>

  <!-- Status bar -->
  <div class="status-bar">
    <div class="status-dot"></div>
    <span class="status-label">STATUS&nbsp;&nbsp;</span>
    <span class="status-value">{status.upper()}</span>
    <span class="status-activity">{aktv}</span>
  </div>

  <!-- Sapa -->
  <div class="greet-card">
    <div class="greet-text">SELAMAT DATANG, BOS {nama.upper()}</div>
    <div class="greet-sub">Sistem Friday aktif dan siap membantu</div>
  </div>

  <!-- Grid atas -->
  <div class="grid">

    <!-- Jam -->
    <div class="card">
      <div class="card-title">◷ Waktu Sekarang</div>
      <div class="time-big" id="live-clock">{datetime.now().strftime("%H:%M")}</div>
      <div class="date-sub">{datetime.now().strftime("%A, %d %B %Y")}</div>
    </div>

    <!-- Cuaca -->
    <div class="card">
      <div class="card-title">◈ Kondisi Cuaca</div>
      <div class="weather-val">{cuaca if cuaca else "Memuat data cuaca..."}</div>
    </div>

  </div>

  <!-- Sistem status -->
  <div class="card" style="margin-bottom:12px">
    <div class="card-title">⬡ Status Sistem</div>
    <div class="sys-row"><span class="sys-name">Gemini AI 2.5</span><span class="sys-on">ONLINE</span></div>
    <div class="sys-row"><span class="sys-name">Wake Word</span><span class="sys-on">AKTIF</span></div>
    <div class="sys-row"><span class="sys-name">Kamera & Vision</span><span class="sys-on">ONLINE</span></div>
    <div class="sys-row"><span class="sys-name">Browsing Internet</span><span class="sys-on">AKTIF</span></div>
    <div class="sys-row"><span class="sys-name">Memori Permanen</span><span class="sys-on">AKTIF</span></div>
    <div class="sys-row"><span class="sys-name">Edge-TTS Premium</span><span class="sys-on">AKTIF</span></div>
  </div>

  <!-- Berita -->
  <div class="news-card">
    <div class="card-title" style="margin-bottom:8px">📡 Berita Terkini</div>
    {berita_html}
  </div>

  <div class="footer">
    FRIDAY AI &nbsp;•&nbsp; PROJECT ANGGA &nbsp;•&nbsp;
    AUTO-REFRESH 60s &nbsp;•&nbsp; {updated}
  </div>

</div>

<script>
  // Live clock — update setiap detik tanpa reload halaman
  function updateClock() {{
    const now = new Date();
    const h = String(now.getHours()).padStart(2,'0');
    const m = String(now.getMinutes()).padStart(2,'0');
    const el = document.getElementById('live-clock');
    if (el) el.textContent = h + ':' + m;
  }}
  setInterval(updateClock, 1000);
  updateClock();
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


def refresh_dashboard(waktu="", cuaca="", berita=None, status="", aktivitas=""):
    """Update data — server otomatis sajikan HTML terbaru di request berikutnya."""
    update_data(waktu=waktu, cuaca=cuaca, berita=berita,
                status=status, aktivitas=aktivitas)
