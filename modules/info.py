# ==============================================================
# modules/info.py — Project Friday | Modul Data Kontekstual
# Versi : 2.1.0 — Fix dual fallback cuaca, error handling lengkap
# ==============================================================

import requests
from datetime import datetime
from modules.tampilan import tampilkan_status

# --- Konfigurasi ---
TIMEOUT_API = 5   # detik


# ==============================================================
# WAKTU & SAPAAN
# ==============================================================

def dapatkan_waktu() -> str:
    """Mengembalikan sapaan + waktu saat ini dalam Bahasa Indonesia."""
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
# CUACA — Dual Fallback (Fix HTTP 404)
# ==============================================================

def dapatkan_cuaca(api_key: str, kota: str) -> str:
    """
    Mengambil data cuaca dari OpenWeatherMap.
    Menggunakan dua metode fallback agar andal:
      1. Format lengkap  : "Tokyo,JP"
      2. Nama kota saja  : "Tokyo"

    Args:
        api_key : API key OpenWeatherMap.
        kota    : Format "NamaKota,KodeNegara" (contoh: "Tokyo,JP")
    """
    nama_kota_saja = kota.split(",")[0].strip()

    daftar_url = [
        f"http://api.openweathermap.org/data/2.5/weather?q={kota}&appid={api_key}&units=metric&lang=id",
        f"http://api.openweathermap.org/data/2.5/weather?q={nama_kota_saja}&appid={api_key}&units=metric&lang=id",
    ]

    for i, url in enumerate(daftar_url):
        try:
            response = requests.get(url, timeout=TIMEOUT_API)

            # 404 = kota tidak ditemukan, coba format berikutnya
            if response.status_code == 404:
                label = kota if i == 0 else nama_kota_saja
                tampilkan_status(
                    f"Kota '{label}' tidak ditemukan, mencoba format lain...",
                    "peringatan"
                )
                continue

            # 401 = API key salah
            if response.status_code == 401:
                tampilkan_status(
                    "API key OpenWeatherMap tidak valid! Cek config.py.", "error"
                )
                return "API key cuaca tidak valid. Periksa konfigurasi."

            response.raise_for_status()
            data = response.json()

            suhu       = round(data['main']['temp'])
            suhu_rasa  = round(data['main']['feels_like'])
            kondisi    = data['weather'][0]['description']
            kelembaban = data['main']['humidity']
            nama       = data['name']

            tampilkan_status(f"Data cuaca '{nama}' berhasil diambil.", "sukses")
            return (
                f"Cuaca di {nama} saat ini {kondisi}, "
                f"suhu {suhu} derajat Celsius, "
                f"terasa seperti {suhu_rasa} derajat, "
                f"kelembaban {kelembaban} persen."
            )

        except requests.exceptions.Timeout:
            tampilkan_status("Timeout koneksi cuaca.", "peringatan")
            return "Data cuaca timeout. Cek koneksi internet."
        except requests.exceptions.ConnectionError:
            tampilkan_status("Tidak ada koneksi internet.", "peringatan")
            return "Data cuaca tidak tersedia, periksa koneksi WiFi."
        except (KeyError, ValueError):
            tampilkan_status("Format respons cuaca tidak dikenali.", "peringatan")
            continue
        except Exception as e:
            tampilkan_status(f"Error cuaca tidak terduga: {e}", "error")
            continue

    tampilkan_status(
        f"Gagal mendapatkan cuaca. Pastikan KOTA_CUACA di config.py "
        f"format: NamaKota,KODENEGARA (contoh: Tokyo,JP)", "error"
    )
    return "Info cuaca tidak tersedia. Periksa nama kota di config."


# ==============================================================
# BERITA
# ==============================================================

def dapatkan_berita(api_key: str, jumlah: int = 3) -> list:
    """
    Mengambil berita teknologi terkini dari NewsAPI.

    Args:
        api_key : API key NewsAPI.
        jumlah  : Jumlah berita yang diambil (default: 3).
    """
    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?category=technology&language=en&pageSize={jumlah}&apiKey={api_key}"
    )

    try:
        response = requests.get(url, timeout=TIMEOUT_API)
        response.raise_for_status()
        data = response.json()

        artikel = data.get("articles", [])
        if not artikel:
            return ["Tidak ada berita teknologi terbaru saat ini."]

        return [
            f"{i + 1}. {a['title']}"
            for i, a in enumerate(artikel[:jumlah])
            if a.get("title") and a["title"] != "[Removed]"
        ]

    except requests.exceptions.Timeout:
        tampilkan_status("Timeout mengambil data berita.", "peringatan")
        return ["Layanan berita tidak merespons."]
    except requests.exceptions.HTTPError as e:
        tampilkan_status(f"Error berita (HTTP {e.response.status_code}).", "peringatan")
        return ["Gagal mengakses layanan berita."]
    except Exception as e:
        tampilkan_status(f"Error berita: {e}", "error")
        return ["Berita tidak tersedia saat ini."]
