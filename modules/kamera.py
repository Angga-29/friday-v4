# ==============================================================
# modules/kamera.py — Project Friday | Modul Kamera (IP Webcam)
# Versi : 3.0.1 — Multi-endpoint IPWebcam + health check
# ==============================================================
"""
Kompatibel dengan aplikasi IPWebcam (Android).
Endpoint yang didukung secara otomatis:
  /shot.jpg    — snapshot JPEG (direkomendasikan, hemat baterai)
  /video       — stream MJPEG (cadangan)

Setup IPWebcam di Android:
  1. Install "IP Webcam" dari Play Store
  2. Buka aplikasi → Start server
  3. Catat IP:PORT yang muncul (contoh: 192.168.1.5:8080)
  4. Set URL_KAMERA di config.py atau .env
"""

import cv2
import requests
import numpy as np
import time
from modules.tampilan import tampilkan_status

# --- Konfigurasi ---
RESIZE_WIDTH    = 640
RESIZE_HEIGHT   = 480
REQUEST_TIMEOUT = 3       # detik
MAX_RETRY       = 5
RETRY_DELAY     = 2       # detik

# Endpoint alternatif IPWebcam yang dicoba secara berurutan
IPWEBCAM_ENDPOINTS = ["/shot.jpg", "/photo.jpg", "/jpeg"]


def _ekstrak_base_url(url: str) -> str:
    """
    Ekstrak base URL (tanpa endpoint) dari URL lengkap.
    Contoh: "http://192.168.1.5:8080/shot.jpg" → "http://192.168.1.5:8080"
    """
    for endpoint in IPWEBCAM_ENDPOINTS + ["/video", "/"]:
        if url.endswith(endpoint):
            return url[: -len(endpoint)]
    # Potong path terakhir jika ada
    bagian = url.rsplit("/", 1)
    return bagian[0] if len(bagian) > 1 else url


def temukan_endpoint_aktif(base_url: str) -> str | None:
    """
    Coba beberapa endpoint IPWebcam secara berurutan.
    Berguna jika versi IPWebcam berbeda menggunakan endpoint yang berbeda.

    Args:
        base_url: URL dasar, contoh "http://192.168.1.5:8080"

    Returns:
        URL endpoint yang aktif, atau None jika semua gagal.
    """
    for endpoint in IPWEBCAM_ENDPOINTS:
        url_coba = base_url.rstrip("/") + endpoint
        try:
            resp = requests.get(url_coba, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > 1000:
                tampilkan_status(f"Endpoint aktif: {endpoint}", "sukses")
                return url_coba
        except Exception:
            continue
    return None


def ambil_frame(url_kamera: str) -> np.ndarray | None:
    """
    Mengambil satu frame dari IP Webcam (snapshot JPEG).

    Args:
        url_kamera: URL endpoint kamera (contoh: http://192.168.x.x:8080/shot.jpg)

    Returns:
        Frame sebagai numpy array BGR (640×480), atau None jika gagal.
    """
    try:
        resp = requests.get(url_kamera, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        img_arr = np.frombuffer(resp.content, dtype=np.uint8)
        img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

        if img is None:
            tampilkan_status("Gagal decode gambar dari kamera.", "error")
            return None

        return cv2.resize(img, (RESIZE_WIDTH, RESIZE_HEIGHT))

    except requests.exceptions.Timeout:
        tampilkan_status("Timeout: Kamera tidak merespons.", "error")
        return None
    except requests.exceptions.ConnectionError:
        tampilkan_status("Koneksi ke kamera terputus.", "error")
        return None
    except Exception as e:
        tampilkan_status(f"Error kamera: {e}", "error")
        return None


def inisialisasi_kamera(url_kamera: str) -> np.ndarray | None:
    """
    Menghubungkan ke kamera dengan retry otomatis.
    Jika URL utama gagal, coba endpoint IPWebcam lainnya + multi base URL.
    """
    tampilkan_status(f"Menghubungkan ke kamera: {url_kamera}", "info")

    # Coba URL yang diberikan terlebih dahulu
    for percobaan in range(1, MAX_RETRY + 1):
        frame = ambil_frame(url_kamera)
        if frame is not None:
            tampilkan_status(
                f"Kamera terhubung! (percobaan ke-{percobaan})", "sukses"
            )
            return frame

        tampilkan_status(
            f"Percobaan {percobaan}/{MAX_RETRY} gagal. Tunggu {RETRY_DELAY}s...",
            "peringatan"
        )
        time.sleep(RETRY_DELAY)

    # Fallback 1: coba endpoint alternatif di base URL yang sama
    tampilkan_status("Mencoba endpoint IPWebcam alternatif...", "info")
    base_url = _ekstrak_base_url(url_kamera)
    url_aktif = temukan_endpoint_aktif(base_url)

    if url_aktif:
        tampilkan_status(
            f"Gunakan URL ini di config.py:\n  URL_KAMERA = \"{url_aktif}\"",
            "peringatan"
        )
        return ambil_frame(url_aktif)

    # Fallback 2: jika user pakai 127.0.0.1, coba juga IP umum lainnya
    if "127.0.0.1" in url_kamera or "localhost" in url_kamera:
        tampilkan_status(
            "URL pakai localhost — coba juga IP WiFi tablet...", "info"
        )
        ip_alternatif = ["192.168.1.1", "192.168.0.1", "10.0.0.1"]
        for ip in ip_alternatif:
            url_coba = f"http://{ip}:8080/shot.jpg"
            try:
                resp = requests.get(url_coba, timeout=2)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    tampilkan_status(
                        f"Endpoint aktif: {url_coba}\n"
                        f"  Update config.py: URL_KAMERA = \"{url_coba}\"",
                        "sukses"
                    )
                    return ambil_frame(url_coba)
            except Exception:
                continue

    tampilkan_status(
        "Tidak dapat terhubung ke kamera.\n"
        "Cek poin berikut:\n"
        "  1. Aplikasi IP Webcam sudah Start server (lampu hijau aktif)\n"
        "  2. URL_KAMERA di config.py sesuai dengan yang ditampilkan IP Webcam\n"
        "  3. Jika IP Webcam di tablet sama → coba: http://127.0.0.1:8080/shot.jpg\n"
        "  4. Jika IP Webcam di HP lain → pastikan WiFi sama + isi IP HP\n"
        "  5. Coba buka URL di browser dulu untuk test\n"
        "Friday akan jalan dalam mode SUARA SAJA.",
        "error"
    )
    return None


def ke_grayscale_blur(frame: np.ndarray) -> np.ndarray:
    """
    Ubah frame BGR ke grayscale + Gaussian blur untuk deteksi gerakan & wajah.

    Args:
        frame: Frame BGR dari kamera.

    Returns:
        Frame grayscale yang sudah di-blur.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (21, 21), 0)
