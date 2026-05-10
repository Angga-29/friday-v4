# ==============================================================
# modules/info.py — Project Friday | Modul Data Kontekstual
# Versi : 3.0.0 — Triple fallback: OWM → wttr.in (cuaca) | NewsAPI → RSS (berita)
# ==============================================================

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from modules.tampilan import tampilkan_status

TIMEOUT_API = 8   # detik

# Ikon cuaca berdasarkan weatherCode wttr.in
_IKON_CUACA = {
    range(113, 114): "☀️",   # Clear/Sunny
    range(116, 117): "⛅",   # Partly Cloudy
    range(119, 123): "☁️",   # Cloudy / Overcast
    range(143, 148): "🌫️",   # Mist / Fog
    range(176, 200): "🌦️",   # Light rain / Drizzle
    range(200, 227): "⛈️",   # Thunder
    range(227, 263): "❄️",   # Snow
    range(263, 300): "🌧️",   # Rain
    range(300, 400): "🌧️",   # Heavy rain
}

def _kode_ke_ikon(kode: int) -> str:
    for r, ikon in _IKON_CUACA.items():
        if kode in r:
            return ikon
    return "🌡️"


# ==============================================================
# WAKTU & SAPAAN
# ==============================================================

def dapatkan_waktu() -> str:
    sekarang = datetime.now()
    jam      = sekarang.hour
    menit    = sekarang.minute
    hari     = sekarang.strftime("%A")
    tgl      = sekarang.strftime("%d %B %Y")

    hari_id = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat",
        "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    hari_indo = hari_id.get(hari, hari)

    if 4 <= jam < 11:
        sapaan = "Selamat pagi"
    elif 11 <= jam < 15:
        sapaan = "Selamat siang"
    elif 15 <= jam < 18:
        sapaan = "Selamat sore"
    else:
        sapaan = "Selamat malam"

    return (
        f"{sapaan}. Hari ini {hari_indo}, {tgl}. "
        f"Sekarang pukul {jam}:{menit:02d}."
    )


# ==============================================================
# CUACA — Fallback: OpenWeatherMap → wttr.in
# ==============================================================

def _cuaca_owm(api_key: str, kota: str) -> dict | None:
    """Ambil cuaca dari OpenWeatherMap. Return dict atau None jika gagal."""
    nama_kota_saja = kota.split(",")[0].strip()
    for q in [kota, nama_kota_saja]:
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={q}&appid={api_key}&units=metric&lang=id"
            )
            r = requests.get(url, timeout=TIMEOUT_API)
            if r.status_code == 401:
                tampilkan_status("API key OWM tidak valid, beralih ke wttr.in.", "peringatan")
                return None
            if r.status_code == 404:
                continue
            r.raise_for_status()
            d = r.json()
            return {
                "nama"      : d["name"],
                "suhu"      : round(d["main"]["temp"]),
                "rasa"      : round(d["main"]["feels_like"]),
                "kelembaban": d["main"]["humidity"],
                "kondisi"   : d["weather"][0]["description"],
                "ikon"      : "🌡️",
                "sumber"    : "OWM",
            }
        except requests.exceptions.ConnectionError:
            tampilkan_status("Tidak ada internet, beralih ke wttr.in.", "peringatan")
            return None
        except Exception:
            continue
    return None


def _cuaca_wttr(kota: str) -> dict | None:
    """Ambil cuaca dari wttr.in (gratis, tanpa API key)."""
    nama_kota = kota.split(",")[0].strip().replace(" ", "+")
    try:
        url = f"https://wttr.in/{nama_kota}?format=j1"
        r = requests.get(url, timeout=TIMEOUT_API,
                         headers={"User-Agent": "Friday/4.0 (Termux)"})
        r.raise_for_status()
        d = r.json()
        cc   = d["current_condition"][0]
        kode = int(cc.get("weatherCode", 113))
        return {
            "nama"      : nama_kota.replace("+", " "),
            "suhu"      : int(cc["temp_C"]),
            "rasa"      : int(cc["FeelsLikeC"]),
            "kelembaban": int(cc["humidity"]),
            "kondisi"   : cc["weatherDesc"][0]["value"],
            "ikon"      : _kode_ke_ikon(kode),
            "sumber"    : "wttr.in",
        }
    except Exception as e:
        tampilkan_status(f"wttr.in gagal: {e}", "peringatan")
        return None


def dapatkan_cuaca_data(api_key: str, kota: str) -> dict:
    """
    Return dict cuaca {nama, suhu, rasa, kelembaban, kondisi, ikon}.
    Fallback: OWM → wttr.in → data kosong.
    """
    data = None
    if api_key and "your_" not in api_key:
        data = _cuaca_owm(api_key, kota)
    if data is None:
        data = _cuaca_wttr(kota)
    if data is None:
        return {"nama": kota, "suhu": "--", "rasa": "--",
                "kelembaban": "--", "kondisi": "Tidak tersedia", "ikon": "❓"}
    tampilkan_status(
        f"Cuaca {data['nama']}: {data['suhu']}°C {data['kondisi']} [{data['sumber']}]",
        "sukses"
    )
    return data


def dapatkan_cuaca(api_key: str, kota: str) -> str:
    """Return string cuaca untuk diucapkan Friday. Sama interface seperti sebelumnya."""
    d = dapatkan_cuaca_data(api_key, kota)
    if d["suhu"] == "--":
        return "Info cuaca tidak tersedia saat ini."
    return (
        f"Cuaca di {d['nama']} saat ini {d['kondisi']}, "
        f"suhu {d['suhu']} derajat Celsius, "
        f"terasa seperti {d['rasa']} derajat, "
        f"kelembaban {d['kelembaban']} persen."
    )


# ==============================================================
# BERITA — Fallback: NewsAPI → RSS campuran Indonesia + Internasional
# ==============================================================

# Feed Indonesia
_FEEDS_ID = [
    ("🇮🇩 Kompas",   "https://rss.kompas.com/nasional/feed"),
    ("🇮🇩 CNN-ID",   "https://www.cnnindonesia.com/rss"),
    ("🇮🇩 Detik",    "https://rss.detik.com/index.php/detikcom"),
    ("🇮🇩 Tempo",    "https://rss.tempo.co/"),
    ("🇮🇩 Liputan6", "https://rss.liputan6.com/rss/tag/berita-terkini"),
]

# Feed Internasional
_FEEDS_INTL = [
    ("🌍 BBC",       "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("🌍 Reuters",   "https://feeds.reuters.com/reuters/topNews"),
    ("🌍 Al Jazeera","https://www.aljazeera.com/xml/rss/all.xml"),
    ("🇺🇸 CNN",      "http://rss.cnn.com/rss/edition_world.rss"),
    ("🇬🇧 Guardian", "https://www.theguardian.com/world/rss"),
    ("💻 TechCrunch","https://techcrunch.com/feed/"),
]


def _ambil_rss(feeds: list, maks: int) -> list:
    """Ambil judul dari daftar RSS feed, beri label sumber."""
    hasil = []
    for label, url in feeds:
        if len(hasil) >= maks:
            break
        try:
            r = requests.get(url, timeout=TIMEOUT_API,
                             headers={"User-Agent": "Friday/4.0 (Termux)"})
            r.raise_for_status()
            root = ET.fromstring(r.content)
            per_feed = 0
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                if title and len(title) > 10 and "<" not in title:
                    hasil.append(f"{label}: {title}")
                    per_feed += 1
                if per_feed >= 2 or len(hasil) >= maks:   # maks 2 per feed
                    break
            tampilkan_status(f"Berita {label} OK ({per_feed} item).", "sukses")
        except Exception as e:
            tampilkan_status(f"RSS {label} gagal: {e}", "peringatan")
            continue
    return hasil


def _berita_newsapi(api_key: str, jumlah: int) -> list | None:
    """Ambil berita dari NewsAPI. Return list atau None jika gagal."""
    if not api_key or "your_" in api_key:
        return None
    try:
        url = (
            f"https://newsapi.org/v2/top-headlines"
            f"?country=id&pageSize={jumlah}&apiKey={api_key}"
        )
        r = requests.get(url, timeout=TIMEOUT_API)
        if r.status_code in (401, 426, 429):
            tampilkan_status(f"NewsAPI error {r.status_code}, beralih ke RSS.", "peringatan")
            return None
        r.raise_for_status()
        d = r.json()
        if d.get("status") != "ok":
            return None
        hasil = [
            a["title"]
            for a in d.get("articles", [])[:jumlah]
            if a.get("title") and a["title"] != "[Removed]"
        ]
        return hasil or None
    except Exception as e:
        tampilkan_status(f"NewsAPI gagal: {e}", "peringatan")
        return None


def dapatkan_berita(api_key: str, jumlah: int = 6) -> list:
    """
    Return list judul berita campuran Indonesia + internasional.
    Fallback: NewsAPI → RSS otomatis.
    """
    hasil = _berita_newsapi(api_key, jumlah)
    if hasil:
        return hasil

    tampilkan_status("Mengambil berita campuran Indonesia + Internasional...", "info")
    setengah = max(2, jumlah // 2)

    id_items   = _ambil_rss(_FEEDS_ID,   setengah)
    intl_items = _ambil_rss(_FEEDS_INTL, jumlah - len(id_items))

    # Campurkan: selang-seling lokal & internasional
    gabung = []
    i_id, i_intl = 0, 0
    while len(gabung) < jumlah:
        if i_id < len(id_items):
            gabung.append(id_items[i_id]); i_id += 1
        if i_intl < len(intl_items) and len(gabung) < jumlah:
            gabung.append(intl_items[i_intl]); i_intl += 1
        if i_id >= len(id_items) and i_intl >= len(intl_items):
            break

    return gabung[:jumlah] if gabung else ["Berita tidak tersedia saat ini."]
