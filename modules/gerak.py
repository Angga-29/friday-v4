# ==============================================================
# modules/gerak.py — Project Friday | Modul Deteksi Gerakan
# ==============================================================

import cv2
import numpy as np
from modules.tampilan import tampilkan_status

# --- Konfigurasi ---
THRESHOLD_VALUE  = 25      # Sensitivitas perbedaan pixel
MIN_AREA_GERAK   = 1500    # Luas minimum kontur (filter noise kecil)
DILATE_ITERASI   = 2       # Iterasi dilasi (perbesar area gerakan)


def deteksi_gerakan(
    frame_lama: np.ndarray,
    frame_baru: np.ndarray
) -> tuple[bool, list[tuple[int, int, int, int]]]:
    """
    Membandingkan dua frame untuk mendeteksi gerakan.

    Args:
        frame_lama: Frame grayscale+blur sebelumnya (acuan).
        frame_baru: Frame grayscale+blur terkini.

    Returns:
        Tuple (ada_gerakan: bool, daftar_kontur: list[(x, y, w, h)])
    """
    # Hitung selisih absolut antar frame
    selisih = cv2.absdiff(frame_lama, frame_baru)

    # Threshold: ubah ke hitam-putih
    _, thresh = cv2.threshold(
        selisih, THRESHOLD_VALUE, 255, cv2.THRESH_BINARY
    )
    thresh = cv2.dilate(thresh, None, iterations=DILATE_ITERASI)

    # Cari kontur objek bergerak
    kontur, _ = cv2.findContours(
        thresh.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    area_gerakan = []
    for k in kontur:
        if cv2.contourArea(k) < MIN_AREA_GERAK:
            continue  # Abaikan noise kecil
        area_gerakan.append(tuple(cv2.boundingRect(k)))

    ada_gerakan = len(area_gerakan) > 0
    return ada_gerakan, area_gerakan


def gambar_kotak_gerakan(
    frame: np.ndarray,
    area_gerakan: list[tuple[int, int, int, int]]
) -> np.ndarray:
    """
    Menggambar kotak merah di sekitar area yang bergerak.

    Args:
        frame: Frame BGR dari kamera.
        area_gerakan: List koordinat area gerakan [(x, y, w, h), ...].

    Returns:
        Frame dengan anotasi gerakan.
    """
    frame_hasil = frame.copy()
    for (x, y, w, h) in area_gerakan:
        cv2.rectangle(
            frame_hasil,
            (x, y), (x + w, y + h),
            (0, 0, 255), 2
        )
        cv2.putText(
            frame_hasil, "GERAKAN",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5, (0, 0, 255), 1
        )
    return frame_hasil
