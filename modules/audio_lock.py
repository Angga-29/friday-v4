# ==============================================================
# modules/audio_lock.py — Project Friday | Lock global PyAudio
# ==============================================================
# PortAudio (dipakai lewat PyAudio) tidak aman dipanggil dari dua
# thread berbeda secara bersamaan saat inisialisasi host API di
# Windows — bisa crash (access violation) kalau wake_word.py dan
# tepuk.py sama-sama konstruksi pyaudio.PyAudio()/buka stream di
# waktu yang sama. Semua pemanggilan itu wajib lewat lock ini.

import threading

PYAUDIO_INIT_LOCK = threading.Lock()
