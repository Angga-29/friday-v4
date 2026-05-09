# ==============================================================
# modules/wajah.py — Project Friday | Pengenalan Wajah Personal
# Versi : 3.0.1 — Mengenali wajah spesifik (tidak hanya deteksi)
# ==============================================================
"""
Modul ini SEBELUMNYA hanya bisa: "Apakah ini wajah?"
SEKARANG bisa: "Wajah siapa ini?"

Cara kerja:
1. Foto referensi disimpan di folder data/wajah_dikenal/
2. Saat startup, semua foto referensi di-training (LBPH algorithm)
3. Wajah dari kamera dibandingkan dengan database — match terdekat = orang itu

Threshold LBPH: Nilai confidence SEMAKIN KECIL = SEMAKIN MIRIP
  - 0     = sempurna (identik)
  - < 80  = dianggap cocok / dikenal
  - >= 80 = tidak dikenal
"""

import cv2
import os
import numpy as np
from pathlib import Path
from modules.tampilan import tampilkan_status

# --- Konfigurasi deteksi ---
SCALE_FACTOR    = 1.2
MIN_NEIGHBORS   = 3
MIN_WAJAH_SIZE  = (40, 40)
HAAR_PATH       = "haarcascade_frontalface_default.xml"

# Folder berisi foto wajah yang dikenal
DIR_WAJAH_DIKENAL = Path("data/wajah_dikenal")
DIR_WAJAH_DIKENAL.mkdir(parents=True, exist_ok=True)

# LBPH threshold — confidence di bawah nilai ini dianggap "dikenal"
LBPH_THRESHOLD = 80

# Format foto yang didukung
FORMAT_FOTO = ("*.jpg", "*.jpeg", "*.png")


class PengenalWajah:
    """Class untuk deteksi DAN identifikasi wajah menggunakan LBPH."""

    def __init__(self):
        self.cascade        = None
        self.recognizer     = None
        self.label_to_nama  = {}
        self.tersedia_recog = False
        self._muat_model()
        self._latih_recognizer()

    def _muat_model(self):
        """Muat Haar Cascade untuk deteksi wajah."""
        if not os.path.exists(HAAR_PATH):
            raise FileNotFoundError(f"File '{HAAR_PATH}' tidak ditemukan!")
        self.cascade = cv2.CascadeClassifier(HAAR_PATH)
        if self.cascade.empty():
            raise ValueError(f"Gagal memuat '{HAAR_PATH}'.")
        tampilkan_status("Model deteksi wajah dimuat.", "sukses")

    def _latih_recognizer(self):
        """
        Latih LBPH Recognizer dari foto di folder data/wajah_dikenal/.
        Struktur folder: data/wajah_dikenal/<Nama>/foto1.jpg ...
        Mendukung format: .jpg, .jpeg, .png
        """
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        except AttributeError:
            tampilkan_status(
                "opencv-contrib-python belum terinstall. "
                "Install: pip install opencv-contrib-python",
                "peringatan"
            )
            return

        wajah_data = []
        label_data = []
        label_id   = 0

        for folder_orang in sorted(DIR_WAJAH_DIKENAL.iterdir()):
            if not folder_orang.is_dir():
                continue

            nama = folder_orang.name
            jumlah_foto = 0

            for pola in FORMAT_FOTO:
                for foto in folder_orang.glob(pola):
                    img = cv2.imread(str(foto), cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        continue
                    wajah = self.cascade.detectMultiScale(img, 1.2, 3, minSize=(40, 40))
                    for (x, y, w, h) in wajah:
                        wajah_data.append(img[y:y+h, x:x+w])
                        label_data.append(label_id)
                        jumlah_foto += 1

            if jumlah_foto > 0:
                self.label_to_nama[label_id] = nama
                tampilkan_status(
                    f"Wajah '{nama}' dilatih dari {jumlah_foto} foto.", "sukses"
                )
                label_id += 1

        if wajah_data:
            self.recognizer.train(wajah_data, np.array(label_data))
            self.tersedia_recog = True
            tampilkan_status(
                f"Pengenalan wajah aktif: {list(self.label_to_nama.values())}",
                "sukses"
            )
        else:
            tampilkan_status(
                "Belum ada wajah dilatih. Tambah foto di data/wajah_dikenal/<nama>/",
                "info"
            )

    def deteksi(self, frame: np.ndarray) -> list:
        """
        Deteksi semua wajah dalam frame dan coba identifikasi siapa.

        Returns:
            list of (x, y, w, h, nama, confidence)
            nama = "Tidak Dikenal" jika confidence >= LBPH_THRESHOLD
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Deteksi normal
        wajah_kotak = self.cascade.detectMultiScale(
            gray, SCALE_FACTOR, MIN_NEIGHBORS, minSize=MIN_WAJAH_SIZE
        )

        # Mode sensitif jika tidak ditemukan
        if len(wajah_kotak) == 0:
            wajah_kotak = self.cascade.detectMultiScale(
                gray, 1.1, 2, minSize=(30, 30)
            )

        hasil = []
        for (x, y, w, h) in wajah_kotak:
            nama       = "Tidak Dikenal"
            confidence = 999

            if self.tersedia_recog:
                roi = gray[y:y+h, x:x+w]
                try:
                    label, conf = self.recognizer.predict(roi)
                    # LBPH: confidence makin rendah = makin mirip (0 = identik)
                    if conf < LBPH_THRESHOLD:
                        nama = self.label_to_nama.get(label, "Tidak Dikenal")
                    confidence = conf
                except Exception:
                    pass

            hasil.append((x, y, w, h, nama, confidence))

        return hasil


# ── Fungsi kompatibilitas (backward) ────────────────────────────
def muat_model_wajah() -> PengenalWajah:
    """Backward compatibility — return PengenalWajah."""
    return PengenalWajah()


def deteksi_wajah(frame: np.ndarray, pengenal: PengenalWajah) -> list:
    """Backward compatibility wrapper."""
    return pengenal.deteksi(frame)
