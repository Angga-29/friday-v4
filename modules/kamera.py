# ==============================================================
# modules/kamera.py — Project Friday | Modul Kamera (USB Webcam)
# Versi : 4.0.0 — Pindah dari IP Webcam (HTTP) ke USB webcam lokal
# ==============================================================
"""
Kompatibel dengan webcam USB apa pun yang dikenali Windows sebagai
device video (mis. eMeet C960). Kamera dibuka SEKALI saat startup
(cv2.VideoCapture) dan dibaca ulang tiap frame lewat cap.read() —
bukan request HTTP baru seperti versi IP Webcam sebelumnya.

Setup:
  1. Colokkan webcam USB ke desktop.
  2. Cari index device yang benar (biasanya 0 jika cuma 1 kamera):
       python -c "from modules.kamera import daftar_kamera_tersedia; daftar_kamera_tersedia()"
  3. Set CAMERA_INDEX di config.py atau .env sesuai hasil di atas.
"""

import cv2
import platform
from modules.tampilan import tampilkan_status

# --- Konfigurasi ---
RESIZE_WIDTH    = 640
RESIZE_HEIGHT   = 480
MAX_RETRY       = 5
RETRY_DELAY     = 2       # detik


def _backend_kamera():
    """DirectShow paling stabil untuk USB webcam di Windows; default di OS lain."""
    if platform.system() == "Windows":
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY


def inisialisasi_kamera(index: int):
    """
    Membuka koneksi ke webcam USB dengan retry otomatis.

    Args:
        index: Index device webcam (mis. 0, 1, 2 ...).

    Returns:
        Tuple (cap, frame_pertama) — cap adalah cv2.VideoCapture yang
        harus disimpan & dipakai ulang oleh ambil_frame(). Jika gagal,
        return (None, None).
    """
    tampilkan_status(f"Menghubungkan ke kamera (index {index})...", "info")

    for percobaan in range(1, MAX_RETRY + 1):
        cap = cv2.VideoCapture(index, _backend_kamera())
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESIZE_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESIZE_HEIGHT)
            ok, frame = cap.read()
            if ok and frame is not None:
                tampilkan_status(
                    f"Kamera terhubung! (percobaan ke-{percobaan})", "sukses"
                )
                return cap, cv2.resize(frame, (RESIZE_WIDTH, RESIZE_HEIGHT))
            cap.release()

        tampilkan_status(
            f"Percobaan {percobaan}/{MAX_RETRY} gagal. Tunggu {RETRY_DELAY}s...",
            "peringatan"
        )
        import time
        time.sleep(RETRY_DELAY)

    tampilkan_status(
        f"Tidak dapat terhubung ke kamera index {index}.\n"
        "Cek poin berikut:\n"
        "  1. Webcam USB (eMeet C960) sudah tercolok & terdeteksi Windows\n"
        "  2. CAMERA_INDEX di config.py sesuai — cek dengan:\n"
        "     python -c \"from modules.kamera import daftar_kamera_tersedia; "
        "daftar_kamera_tersedia()\"\n"
        "  3. Tidak ada aplikasi lain (Zoom/Teams/Camera app) yang sedang "
        "memakai kamera\n"
        "Friday akan jalan dalam mode SUARA SAJA.",
        "error"
    )
    return None, None


def ambil_frame(cap) -> "cv2.typing.MatLike | None":
    """
    Mengambil satu frame terbaru dari webcam yang sudah terbuka.

    Args:
        cap: Objek cv2.VideoCapture dari inisialisasi_kamera().

    Returns:
        Frame BGR (640×480), atau None jika gagal/cap tidak valid.
    """
    if cap is None or not cap.isOpened():
        return None
    try:
        ok, frame = cap.read()
        if not ok or frame is None:
            return None
        return cv2.resize(frame, (RESIZE_WIDTH, RESIZE_HEIGHT))
    except Exception as e:
        tampilkan_status(f"Error kamera: {e}", "error")
        return None


def lepas_kamera(cap):
    """Tutup koneksi kamera dengan aman saat Friday berhenti."""
    if cap is not None:
        try:
            cap.release()
        except Exception:
            pass


def daftar_kamera_tersedia(maks_index: int = 5):
    """
    Bantu user menemukan index kamera yang benar — coba buka index
    0..maks_index-1 satu per satu dan laporkan mana yang aktif.

    Usage:
        python -c "from modules.kamera import daftar_kamera_tersedia; daftar_kamera_tersedia()"
    """
    backend = _backend_kamera()
    ditemukan = []
    for i in range(maks_index):
        cap = cv2.VideoCapture(i, backend)
        if cap.isOpened():
            ok, frame = cap.read()
            lebar  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            tinggi = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            status = "OK, dapat frame" if ok and frame is not None else "terbuka tapi tidak ada frame"
            print(f"  [index {i}] {status} — resolusi default {lebar}x{tinggi}")
            ditemukan.append(i)
            cap.release()
        else:
            print(f"  [index {i}] tidak tersedia")
    if ditemukan:
        print(f"\nIndex yang terdeteksi: {ditemukan}. "
              f"Set CAMERA_INDEX={ditemukan[0]} di config.py/.env jika itu eMeet C960.")
    else:
        print("\nTidak ada kamera terdeteksi sama sekali. Cek koneksi USB & driver.")
    return ditemukan


def ke_grayscale_blur(frame):
    """
    Ubah frame BGR ke grayscale + Gaussian blur untuk deteksi gerakan & wajah.

    Args:
        frame: Frame BGR dari kamera.

    Returns:
        Frame grayscale yang sudah di-blur.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (21, 21), 0)
