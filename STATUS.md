# Friday v5.0 — Status & Panduan Setup

> Dokumen ini ditulis untuk sesi Claude Code yang jalan LOKAL di komputer
> user (Windows, ASUS TUF). Baca ini dulu, lalu langsung eksekusi bagian
> "TUGAS SESI INI" — user sudah tahu rencananya, tidak perlu banyak
> bertanya ulang, cukup konfirmasi hal yang memang butuh input user
> (API key, pilihan device kamera, dll).

## Ringkasan Project

**Friday** — asisten AI personal berbasis suara (terinspirasi F.R.I.D.A.Y.
dari Iron Man). Awalnya dibangun untuk Termux/Android (Xiaomi Pad 7) dengan
Gemini sebagai otak dan IP Webcam sebagai kamera. Repo ini baru saja
dimigrasi total ke:

- **OS**: Windows Desktop native (ASUS TUF, GPU RTX 5050)
- **Otak AI utama**: Claude (Anthropic) — bukan Gemini lagi
- **Fallback offline**: Ollama, model `qwen2.5:7b`
- **Kamera**: webcam USB eMeet C960 (lokal, via OpenCV `VideoCapture`) —
  bukan IP Webcam Android lagi
- **UI**: dashboard web JARVIS-style (`http://localhost:8765`, buka
  otomatis di browser default), mendukung logo & animasi custom
- **Suara**: Edge-TTS `id-ID-GadisNeural` (Bahasa Indonesia, wanita),
  fallback `pyttsx3` (SAPI5 offline) lalu `gTTS`

Semua perubahan migrasi ada di branch **`claude/repository-data-analysis-3r209c`**
(bukan `main`). Pastikan repo di-checkout ke branch ini.

## Yang Sudah Selesai Dikerjakan

| Area | Status |
|---|---|
| `modules/claude_ai.py` — wrapper Claude AI (streaming, riset, vision) | ✅ Selesai |
| `modules/penglihatan.py` — Claude Vision (ganti Gemini Vision) | ✅ Selesai |
| `modules/kamera.py` — USB webcam via `cv2.VideoCapture` | ✅ Selesai |
| `modules/suara.py` — TTS Windows (Edge-TTS → pyttsx3 → gTTS) | ✅ Selesai |
| `modules/dashboard.py` — dashboard browser + dukungan logo/animasi custom (folder `assets/`) | ✅ Selesai |
| `skills/aplikasi.py`, `skills/musik.py` — target Windows (bukan Android) | ✅ Selesai |
| `skills/cek_sistem.py` — "Friday Doctor" diagnostik, cross-platform | ✅ Selesai |
| `requirements.txt` — dependency Windows (anthropic, pyttsx3, opencv-contrib-python, dll) | ✅ Selesai |
| `setup_windows.ps1`, `start_windows.bat`, `start_windows_silent.vbs` | ✅ Selesai |
| Semua kode sudah lolos `py_compile` + smoke test (di sandbox Linux, BELUM pernah dites di Windows asli) | ✅ Verifikasi statis |

**Yang BELUM dilakukan (baru bisa dilakukan di komputer user, hardware asli):**
- Instalasi dependency Python sungguhan di Windows
- Isi API key Claude (`ANTHROPIC_API_KEY`)
- Sambungkan & tes webcam eMeet C960
- Taruh logo custom (`assets/logo.png`) — user sudah punya gambar HUD F.R.I.D.A.Y. yang mau dipakai, tapi belum disimpan ke file
- Test end-to-end run pertama (voice loop, wake word, TTS ke speaker, dll)

## TUGAS SESI INI (jalankan langsung, minim tanya balik)

1. **Pastikan branch benar**: `git status` / `git branch` — kalau bukan
   di `claude/repository-data-analysis-3r209c`, checkout dulu.

2. **Jalankan setup**:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\setup_windows.ps1
   ```
   Script ini otomatis: buat venv, `pip install -r requirements.txt`,
   copy `config.example.py` → `config.py`, copy `.env.example` → `.env`,
   buat folder `data/wajah_dikenal` & `assets`.

3. **Minta API key Claude ke user** (kalau belum ada di `.env`):
   `ANTHROPIC_API_KEY` di https://console.anthropic.com/settings/keys.
   Isi ke `.env` (atau `config.py`, `API_KEY_CLAUDE`).

4. **Install `mpv`** (audio player wajib, tidak lewat pip):
   ```
   winget install mpv
   ```
   Kalau `winget` tidak ada, arahkan user download manual dari https://mpv.io.

5. **Deteksi index webcam eMeet C960** — minta user colokkan kameranya,
   lalu jalankan:
   ```
   python -c "from modules.kamera import daftar_kamera_tersedia; daftar_kamera_tersedia()"
   ```
   Set `CAMERA_INDEX` di `.env`/`config.py` sesuai hasilnya.

6. **Logo custom**: user punya gambar HUD "F.R.I.D.A.Y." (lingkaran
   orange/teal ala Iron Man) yang mau dipakai sebagai logo dashboard.
   Minta dia simpan sebagai `assets/logo.png` — sistem sudah otomatis
   mendeteksi & memakainya (lihat `assets/README.txt` untuk detail
   konvensi nama file, termasuk opsi `assets/logo_animasi.gif`).

7. **Jalankan Friday**:
   ```
   .\start_windows.bat
   ```
   (Pakai versi ini dulu, BUKAN `start_windows_silent.vbs`, supaya kalau
   ada error masih kelihatan di terminal.) Setelah dipastikan jalan lancar
   beberapa kali, baru user bisa pindah ke versi silent (`start_windows_silent.vbs`)
   untuk pemakaian harian tanpa jendela terminal.

8. **Verifikasi jalan dengan benar**:
   - Terminal menampilkan status inisialisasi tanpa error fatal
   - Tab browser terbuka otomatis ke `http://localhost:8765` (dashboard)
   - Ucapkan "Hai Friday" → Friday merespons via suara
   - Kalau ada masalah, `skills/cek_sistem.py` bisa dipanggil via suara
     ("cek sistem" / "friday doctor") untuk diagnostik cepat

9. **Kalau ada error saat instalasi/run**, ini beberapa yang sudah
   diketahui berpotensi muncul (lihat bagian "Known Gotchas" di bawah)
   — cek itu dulu sebelum minta bantuan ke luar sesi ini.

## Known Gotchas (sudah diantisipasi, tapi belum pernah diuji di Windows asli)

- **PyAudio gagal install via pip**: jalankan
  `pip install pipwin && pipwin install pyaudio`
- **JANGAN install `opencv-python` DAN `opencv-contrib-python` bersamaan**
  — keduanya menyediakan modul `cv2` yang sama dan akan saling menimpa.
  `requirements.txt` sudah benar hanya mencantumkan `opencv-contrib-python`
  (mencakup semua fitur + `cv2.face` untuk pengenalan wajah).
- **Webcam tidak terdeteksi**: pastikan tidak ada app lain (Zoom/Teams/
  Camera Windows) yang sedang memakai kamera; coba index 0-4 lewat
  `daftar_kamera_tersedia()`.
- **pyttsx3 pakai voice bahasa Inggris meski sudah id-ID**: itu fallback
  offline saja (dipakai kalau Edge-TTS gagal/tidak ada internet) — voice
  utama (`id-ID-GadisNeural` via Edge-TTS) butuh koneksi internet. pyttsx3
  akan coba cari voice Indonesia di SAPI5 Windows tapi tidak semua Windows
  punya voice pack itu terinstall.
- **Ollama bersifat opsional** — kalau tidak diinstall, Friday tetap
  jalan normal (fallback offline cuma tidak aktif, akan ada warning saat
  startup, itu wajar bukan error fatal).
- **`config.py` dan `.env` sengaja di-gitignore** — jangan pernah commit
  file itu (berisi API key asli).

## Referensi Config

Variabel penting di `config.py`/`.env`:
- `ANTHROPIC_API_KEY` — wajib, API key Claude
- `CAMERA_INDEX` — index webcam USB (default `0`)
- `KAMERA_WAJIB` — `false` = tetap jalan mode suara saja kalau kamera gagal
- `WEATHER_API_KEY`, `NEWS_API_KEY` — opsional, ada fallback kalau kosong
- `USER_NAME` — nama panggilan user, dipakai Friday untuk menyapa
- `WEATHER_CITY` — format `"Kota,KODENEGARA"` mis. `"Jakarta,ID"`
- `OLLAMA_HOST`, `OLLAMA_MODEL` — default `http://localhost:11434`, `qwen2.5:7b`
