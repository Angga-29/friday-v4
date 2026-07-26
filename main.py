#!/usr/bin/env python3
# ==============================================================
#
#   ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗
#   ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝
#   █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝
#   ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝
#   ██║     ██║  ██║██║██████╔╝██║  ██║   ██║
#   ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝
#
#   Project Friday — AI Personal Assistant
#   Versi    : 5.0.0 — Powered by OpenJarvis Concepts
#   Platform : Windows Desktop (ASUS TUF) + USB Webcam (eMeet C960)
#   Author   : Angga
#   Engine   : Claude (Anthropic) + Skills + Deep Research + Vision
#
#   FITUR BARU v5.0:
#   ✓ Otak utama Claude (Anthropic) — sebelumnya Gemini
#   ✓ Kamera USB lokal (eMeet C960) — sebelumnya IP Webcam Android
#   ✓ Berjalan native di Windows — sebelumnya Termux/Android
#
#   FITUR v4.0 (terinspirasi OpenJarvis):
#   ✓ Skills System — eksekusi lokal sebelum Gemini
#   ✓ Deep Research — riset 3-langkah multi-sumber
#   ✓ Morning Digest — ringkasan pagi otomatis
#   ✓ Friday Doctor — diagnostik sistem
#   ✓ Kalkulator, Timer, Musik — skills bawaan
#   ✓ Auto-prune memori SQLite
#
# ==============================================================

import time
import sys
import os
import socket
import threading

# ── Mode headless (dijalankan tanpa jendela terminal, mis. via
#    start_windows_silent.vbs + pythonw.exe) — semua print()/status
#    dialihkan ke friday.log supaya tetap bisa didiagnosis. ──
if os.environ.get("FRIDAY_HEADLESS") == "1":
    _log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "friday.log")
    _log_file = open(_log_path, "a", buffering=1, encoding="utf-8")
    sys.stdout = _log_file
    sys.stderr = _log_file

import config
from modules.tampilan    import (
    tampilkan_header, tampilkan_status, tampilkan_divider,
    pop_up_berita, tampilkan_browsing, tampilkan_vision,
    tampilkan_statistik, tampilkan_app_dibuka, tampilkan_musik,
    mulai_bubble_stream, stream_chunk, tutup_bubble_stream,
    stop_spinner,
)
from modules.suara       import bicara, stop_bicara, _sedang_bicara as _tts_event
from modules.pendengar   import dengarkan
from modules.tepuk       import DetektorTepuk
from modules.info        import dapatkan_waktu, dapatkan_cuaca, dapatkan_cuaca_data, dapatkan_berita

INTERVAL_REFRESH_DATA = 1800   # detik — refresh cuaca+berita otomatis setiap 30 menit
from modules.claude_ai   import ClaudeAI
from modules.browser     import perlu_browsing, cari_web, format_untuk_ai
from modules.memori      import MemoriFriday
from modules.wake_word   import WakeWordDetector
from modules.penglihatan import perlu_penglihatan, deskripsikan_pemandangan
from modules.proaktif    import ModeProaktif
from modules.riset       import perlu_riset, riset_mendalam
from modules.dashboard   import buka_dashboard, refresh_dashboard, update_data as dashboard_update, tutup_dashboard, set_stop_callback
from modules.lokal_ai   import LokalAI
from skills              import SkillManager

# Import modul kamera & wajah — opsional (tidak crash jika tidak tersedia)
try:
    from modules.kamera import ambil_frame, inisialisasi_kamera, ke_grayscale_blur, lepas_kamera
    _KAMERA_TERSEDIA = True
except ImportError as _e:
    tampilkan_status = None  # akan di-set ulang setelah import tampilkan
    _KAMERA_TERSEDIA = False
    _KAMERA_IMPORT_ERROR = str(_e)

try:
    from modules.wajah import PengenalWajah
    _WAJAH_TERSEDIA = True
except ImportError:
    _WAJAH_TERSEDIA = False

try:
    from modules.gerak import deteksi_gerakan
    _GERAK_TERSEDIA = True
except ImportError:
    _GERAK_TERSEDIA = False

# Re-import tampilkan_status karena mungkin ditimpa sementara
from modules.tampilan import tampilkan_status


# ==============================================================
# KONFIGURASI
# ==============================================================
DELAY_UTAMA       = 0.5
DELAY_TANPA_ORANG = 2.0
COOLDOWN_SAPAAN   = 300
COOLDOWN_GERAK    = 30


# ==============================================================
# STATE GLOBAL — diakses dari thread wake word
# ==============================================================
state = {
    "wake_triggered"  : False,
    "ai"              : None,
    "lokal_ai"        : None,   # Ollama — aktif saat offline
    "memori"          : None,
    "skill_manager"   : None,
    "status_sistem"   : "Standby",
    "frame_terakhir"  : None,
    "kamera_cap"      : None,   # cv2.VideoCapture webcam USB
    "cache_waktu"     : "",
    "cache_cuaca"     : "",
    "cache_berita"    : [],
    "tanpa_kamera"    : False,
}

# Cache hasil cek internet — agar tidak cek setiap request
_internet_cache = {"ok": True, "ts": 0.0}

def _cek_internet() -> bool:
    """Cek koneksi internet via socket ke DNS Google. Cache 20 detik."""
    now = time.time()
    if now - _internet_cache["ts"] < 20:
        return _internet_cache["ok"]
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=2)
        sock.close()
        _internet_cache["ok"] = True
    except OSError:
        _internet_cache["ok"] = False
    _internet_cache["ts"] = now
    return _internet_cache["ok"]


def _pilih_ai():
    """
    Return AI yang dipakai untuk sesi ini.
    Urutan: Claude (online) → Ollama (offline) → Claude anyway (no choice)
    """
    if _cek_internet():
        return state["ai"], False   # (ai_object, is_offline)
    lokal = state["lokal_ai"]
    if lokal and lokal.terhubung:
        return lokal, True
    return state["ai"], False


# ==============================================================
# CALLBACK WAKE WORD
# ==============================================================
def on_wake_word(teks_terdeteksi=None):
    state["wake_triggered"] = True


# ==============================================================
# HELPER STATUS — update dashboard + Termux display sekaligus
# ==============================================================
def set_status(status: str):
    """Update status sistem di dashboard Chrome dan state global."""
    state["status_sistem"] = status
    try:
        from modules.dashboard import update_data as _du
        _du(status=status)
    except Exception:
        pass


# ==============================================================
# REFRESH PERIODIK — background thread, setiap 30 menit
# ==============================================================
def _mulai_refresh_periodik():
    def _loop():
        while True:
            time.sleep(INTERVAL_REFRESH_DATA)
            tampilkan_status("Refresh data otomatis (30 menit)...", "info")
            try:
                update_cache_data()
            except Exception as e:
                tampilkan_status(f"Refresh periodik gagal: {e}", "peringatan")
    t = threading.Thread(target=_loop, daemon=True, name="PeriodicRefresh")
    t.start()


# ==============================================================
# INISIALISASI
# ==============================================================
def inisialisasi_semua():
    tampilkan_header()
    tampilkan_status("Memulai inisialisasi v4.0...", "info")
    tampilkan_divider()

    # 1. Memori
    memori = MemoriFriday()
    state["memori"] = memori

    # 2. Kamera (opsional — tidak crash jika tidak tersedia)
    kamera_wajib = getattr(config, 'KAMERA_WAJIB', False)
    pengenal     = None

    if not _KAMERA_TERSEDIA:
        tampilkan_status(
            f"Modul kamera tidak dapat dimuat: {_KAMERA_IMPORT_ERROR if not _KAMERA_TERSEDIA else ''}",
            "peringatan"
        )
        tampilkan_status("Pastikan OpenCV terinstall: pip install opencv-python", "info")
        if kamera_wajib:
            sys.exit(1)
        state["tanpa_kamera"] = True
    else:
        cap, frame_awal = inisialisasi_kamera(config.CAMERA_INDEX)
        state["kamera_cap"] = cap
        if frame_awal is None:
            if kamera_wajib:
                tampilkan_status(
                    "Kamera tidak terhubung! Set KAMERA_WAJIB=False di config.py "
                    "untuk mode suara saja.", "error"
                )
                sys.exit(1)
            tampilkan_status("Kamera tidak tersedia → MODE SUARA SAJA aktif.", "peringatan")
            state["tanpa_kamera"] = True
        else:
            state["tanpa_kamera"] = False

    # 3. Pengenal Wajah (opsional)
    if not state["tanpa_kamera"] and _WAJAH_TERSEDIA:
        try:
            pengenal = PengenalWajah()
        except Exception as e:
            tampilkan_status(f"Pengenalan wajah: {e}", "peringatan")
            tampilkan_status("Berjalan tanpa pengenalan wajah (deteksi wajah tetap aktif).", "info")
            pengenal = None
    elif not _WAJAH_TERSEDIA:
        tampilkan_status("Modul wajah tidak tersedia (install opencv-contrib).", "peringatan")

    # 4. Claude AI dengan memori
    ai = ClaudeAI(
        api_key=config.API_KEY_CLAUDE,
        system_prompt=config.SYSTEM_PROMPT_FRIDAY,
        memori=memori
    )
    if not ai.terhubung:
        sys.exit(1)
    state["ai"] = ai

    # 5. Ollama Local AI (opsional — hanya aktif jika Ollama jalan)
    lokal_ai = LokalAI(
        host=config.OLLAMA_HOST,
        model=config.OLLAMA_MODEL,
        system_prompt=config.SYSTEM_PROMPT_FRIDAY,
    )
    state["lokal_ai"] = lokal_ai

    # 6. Skills System (OpenJarvis-inspired)
    skill_manager = SkillManager()
    state["skill_manager"] = skill_manager
    daftar = skill_manager.daftar_skill()
    tampilkan_status(f"Skills dimuat: {', '.join(daftar)}", "sukses")

    # 6. Browser (cek ketersediaan)
    try:
        from ddgs import DDGS  # noqa: F401
        tampilkan_status("DuckDuckGo (ddgs) siap.", "sukses")
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # noqa: F401
            tampilkan_status("DuckDuckGo siap (duckduckgo_search).", "sukses")
        except ImportError:
            tampilkan_status("ddgs tidak terinstall — pakai: pip install ddgs", "peringatan")

    # 7. Wake Word Detector (background thread)
    wake_detector = WakeWordDetector(callback_terdeteksi=on_wake_word)
    wake_detector.mulai()

    # 7b. Double Clap Detector + barge-in (background thread)
    clap_detector = DetektorTepuk(
        callback=on_wake_word,
        sedang_bicara=_tts_event,
    )
    clap_detector.mulai()

    # 8. Mode Proaktif + Morning Digest (OpenJarvis Morning Digest Agent)
    proaktif = ModeProaktif(
        callback_bicara=bicara,
        nama_pengguna=f"Bos {config.NAMA_PENGGUNA}",
        callback_cuaca=lambda: dapatkan_cuaca(config.API_KEY_CUACA, config.KOTA_CUACA),
        callback_berita=lambda: dapatkan_berita(config.API_KEY_BERITA, jumlah=3),
    )
    proaktif.mulai()

    tampilkan_divider()
    tampilkan_status("Friday v4.0 siap bertugas!", "sukses")
    time.sleep(1)

    if state["tanpa_kamera"]:
        tampilkan_status(
            "MODE SUARA SAJA: Panggil 'Hai Friday' untuk mulai berbicara.", "info"
        )

    # Buka web dashboard di Chrome
    dashboard_update(nama=config.NAMA_PENGGUNA)
    set_stop_callback(stop_bicara)
    tampilkan_status("Membuka dashboard JARVIS di browser...", "info")
    buka_dashboard()

    # Mulai refresh data otomatis setiap 30 menit
    _mulai_refresh_periodik()
    tampilkan_status("Refresh data otomatis setiap 30 menit aktif.", "info")

    return ai, pengenal, memori, wake_detector, proaktif, skill_manager, clap_detector


# ==============================================================
# HANDLER PROSES JAWABAN
# ==============================================================
def proses_jawaban(suara_user, ai, memori, skill_manager):
    """Proses input user. Return True jika harus keluar."""
    teks_lower   = suara_user.lower()
    cache_waktu  = state["cache_waktu"]
    cache_cuaca  = state["cache_cuaca"]
    cache_berita = state["cache_berita"]

    set_status("Memproses")

    try:
        # ── 1. PERINTAH KELUAR ───────────────────────────────────────
        if any(k in teks_lower for k in ["keluar", "matikan friday", "istirahat friday"]):
            bicara(f"Baik, Bos {config.NAMA_PENGGUNA}. Sampai jumpa!")
            return True

        # ── 2. RESET SESI ────────────────────────────────────────────
        if "reset" in teks_lower and "sesi" in teks_lower:
            ai.reset_sesi()
            bicara("Sesi percakapan direset.")
            return False

        # ── 3. STATISTIK ─────────────────────────────────────────────
        if "statistik" in teks_lower:
            stats = memori.statistik_hari_ini()
            tampilkan_statistik(stats)
            bicara(
                f"Hari ini: {stats['interaksi']} interaksi, "
                f"{stats['browsing']} browsing, "
                f"{stats['skill']} skill, "
                f"{stats['riset']} riset mendalam."
            )
            return False

        # ── 4. SIMPAN PREFERENSI ─────────────────────────────────────
        if teks_lower.startswith(("ingat bahwa", "ingat kalau", "tolong ingat")):
            info = suara_user.split(maxsplit=2)[-1] if len(suara_user.split()) > 2 else suara_user
            memori.simpan_preferensi(f"catatan_{int(time.time())}", info)
            bicara(f"Saya catat: {info}")
            return False

        # ── 5. SKILLS (lokal — lebih cepat dari Claude) ──────────────
        hasil_skill = skill_manager.cari_dan_jalankan(
            suara_user,
            callback_bicara=bicara,
            berita=cache_berita,
        )
        if hasil_skill is not None:
            tampilkan_status("Dijawab oleh skill lokal.", "sukses")
            bicara(hasil_skill)
            memori.simpan_percakapan(suara_user, hasil_skill, tipe="skill")
            memori.catat_interaksi("skill")
            return False

        # ── 6. RISET MENDALAM ────────────────────────────────────────
        if perlu_riset(suara_user):
            if not _cek_internet():
                bicara("Riset butuh koneksi internet, Bos. Saya sedang offline.")
                return False
            set_status("Riset")
            tampilkan_status("Mode riset mendalam aktif.", "browsing")
            bicara("On it. Lakukan riset mendalam, mohon tunggu sebentar.")
            jawaban = riset_mendalam(suara_user, ai)
            bicara(jawaban)
            memori.simpan_percakapan(suara_user, jawaban, pakai_web=True, tipe="riset")
            memori.catat_interaksi("riset")
            return False

        # ── 7. VISION ────────────────────────────────────────────────
        if perlu_penglihatan(suara_user):
            set_status("Vision")
            tampilkan_vision()
            jawaban = deskripsikan_pemandangan(
                state["frame_terakhir"], suara_user, config.API_KEY_CLAUDE
            )
            bicara(jawaban)
            memori.simpan_percakapan(suara_user, jawaban, pakai_web=False, tipe="vision")
            return False

        # ── 8. BROWSING ──────────────────────────────────────────────
        if perlu_browsing(suara_user):
            if not _cek_internet():
                bicara("Browsing butuh internet, Bos. Koneksi sedang tidak tersedia.")
                return False
            set_status("Browsing")
            tampilkan_status("Pertanyaan perlu browsing.", "browsing")
            bicara("Baik, saya carikan dari internet.")
            tampilkan_browsing(suara_user)
            hasil_web    = cari_web(suara_user)
            konteks_web  = format_untuk_ai(suara_user, hasil_web)
            konteks_penuh = (
                f"[KONTEKS]\nWaktu: {cache_waktu}\nCuaca: {cache_cuaca}\n\n"
                + konteks_web
            )
            jawaban = ai.tanya_dengan_web(suara_user, konteks_penuh)
            bicara(jawaban)
            memori.simpan_percakapan(suara_user, jawaban, pakai_web=True, tipe="browsing")
            memori.catat_interaksi("browsing")
            return False

        # ── 9. CHAT — Claude (online) atau Ollama (offline) ──────────
        ai_aktif, mode_offline = _pilih_ai()

        if mode_offline:
            tampilkan_status(
                f"OFFLINE MODE — menggunakan {config.OLLAMA_MODEL} lokal.", "peringatan"
            )

        perintah = ai_aktif.bangun_konteks(
            suara_user=suara_user, waktu=cache_waktu,
            cuaca=cache_cuaca, berita=cache_berita
        )

        # Streaming: tampil kata per kata di terminal, TTS setelah selesai
        mulai_bubble_stream()
        teks_lengkap = ""
        try:
            for chunk in ai_aktif.tanya_stream(perintah):
                stream_chunk(chunk)
                teks_lengkap += chunk
        finally:
            tutup_bubble_stream()

        jawaban = teks_lengkap.strip() or "Maaf, tidak ada jawaban dari AI."
        bicara(jawaban)
        memori.simpan_percakapan(
            suara_user, jawaban,
            tipe="chat_offline" if mode_offline else "chat"
        )
        memori.catat_interaksi("interaksi")
        return False

    except Exception as e:
        tampilkan_status(f"Error proses jawaban: {e}", "error")
        bicara("Maaf, ada gangguan sebentar. Silakan ulangi.")
        return False
    finally:
        set_status("Standby")


# ==============================================================
# UPDATE CACHE DATA REAL-TIME
# ==============================================================
def update_cache_data():
    state["cache_waktu"]     = dapatkan_waktu()
    cd = dapatkan_cuaca_data(config.API_KEY_CUACA, config.KOTA_CUACA)
    state["cache_cuaca"]     = dapatkan_cuaca(config.API_KEY_CUACA, config.KOTA_CUACA)
    state["cache_cuaca_data"] = cd
    state["cache_berita"]    = dapatkan_berita(config.API_KEY_BERITA, jumlah=6)
    refresh_dashboard(
        waktu=state["cache_waktu"],
        cuaca=state["cache_cuaca"],
        cuaca_data=cd,
        berita=state["cache_berita"],
    )


# ==============================================================
# LOOP UTAMA
# ==============================================================
def jalankan():
    ai, pengenal, memori, wake_detector, proaktif, skill_manager, clap_detector = inisialisasi_semua()

    update_cache_data()

    sudah_menyapa         = False
    frame_lama_gray       = None
    waktu_terakhir_sapaan = 0
    waktu_terakhir_gerak  = 0
    waktu_gerak_terakhir  = 0

    bicara(f"Sistem siap, Bos {config.NAMA_PENGGUNA}.")

    tampilkan_header()
    tampilkan_status("Loop utama aktif. Tekan Ctrl+C untuk keluar.", "sukses")

    try:
        if state["tanpa_kamera"]:
            # ══════════════════════════════════════════════════
            # LOOP MODE SUARA SAJA (tanpa kamera / IP Webcam)
            # ══════════════════════════════════════════════════
            tampilkan_status("Loop suara aktif. Panggil 'Hai Friday' kapan saja.", "sukses")
            while True:
                if state["wake_triggered"]:
                    state["wake_triggered"] = False
                    tampilkan_status("Wake word terpicu — masuk mode listen.", "wake")
                    bicara("Ya, Bos. Saya mendengarkan.")

                    if not state["cache_cuaca"]:
                        update_cache_data()

                    set_status("Mendengarkan")
                    suara_user = dengarkan(setelah_tts=True)
                    set_status("Standby")

                    if suara_user:
                        if proses_jawaban(suara_user, ai, memori, skill_manager):
                            break
                    else:
                        bicara("Maaf, saya tidak mendengar.")
                else:
                    time.sleep(DELAY_UTAMA)

        else:
            # ══════════════════════════════════════════════════
            # LOOP MODE PENUH (dengan kamera + deteksi wajah)
            # ══════════════════════════════════════════════════
            while True:

                # ── 1. AMBIL FRAME ───────────────────────────────────
                frame = ambil_frame(state["kamera_cap"])
                if frame is None:
                    time.sleep(1)
                    continue

                state["frame_terakhir"] = frame
                frame_gray = ke_grayscale_blur(frame) if _KAMERA_TERSEDIA else None
                waktu_kini = time.time()

                # ── 2. CEK WAKE WORD ─────────────────────────────────
                if state["wake_triggered"]:
                    state["wake_triggered"] = False
                    tampilkan_status("Wake word terpicu — masuk mode listen.", "wake")
                    bicara("Ya, Bos. Saya mendengarkan.")

                    if not state["cache_cuaca"]:
                        update_cache_data()

                    set_status("Mendengarkan")
                    suara_user = dengarkan(setelah_tts=True)
                    set_status("Standby")

                    if suara_user:
                        if proses_jawaban(suara_user, ai, memori, skill_manager):
                            break
                    else:
                        bicara("Maaf, saya tidak mendengar.")
                    continue

                # ── 3. DETEKSI GERAKAN ───────────────────────────────
                if _GERAK_TERSEDIA and frame_gray is not None and frame_lama_gray is not None:
                    ada_gerak, _ = deteksi_gerakan(frame_lama_gray, frame_gray)
                    if ada_gerak:
                        waktu_gerak_terakhir = waktu_kini
                        if waktu_kini - waktu_terakhir_gerak > COOLDOWN_GERAK:
                            tampilkan_status("⚡ Gerakan terdeteksi.", "deteksi")
                            waktu_terakhir_gerak = waktu_kini

                if frame_gray is not None:
                    frame_lama_gray = frame_gray

                # ── 4. DETEKSI & IDENTIFIKASI WAJAH ──────────────────
                wajah_list   = pengenal.deteksi(frame) if pengenal else []
                ada_orang    = len(wajah_list) > 0
                nama_dikenal = None

                for (x, y, w, h, nama, conf) in wajah_list:
                    if nama != "Tidak Dikenal":
                        nama_dikenal = nama
                        break

                if not ada_orang and waktu_gerak_terakhir > 0:
                    if waktu_kini - waktu_gerak_terakhir < 10:
                        ada_orang = True

                if ada_orang:
                    # ── 5. SAPAAN PERSONAL ───────────────────────────
                    if not sudah_menyapa or waktu_kini - waktu_terakhir_sapaan > COOLDOWN_SAPAAN:
                        sudah_menyapa         = True
                        waktu_terakhir_sapaan = waktu_kini

                        update_cache_data()
                        pop_up_berita(state["cache_berita"])

                        if nama_dikenal:
                            bicara(f"Halo, {nama_dikenal}.")
                            memori.catat_interaksi("wajah")
                        else:
                            bicara(f"Halo, Bos {config.NAMA_PENGGUNA}.")

                    # Catatan: Friday TIDAK otomatis mendengarkan cuma karena
                    # ada orang di depan kamera -- itu bikin dia salah dengar
                    # noise/obrolan latar terus-menerus lalu ngomong "saya
                    # tidak mendengar" berulang-ulang. Mendengarkan HANYA
                    # dipicu wake word "Hai Friday" (ditangani di step 2 di
                    # atas), sama seperti mode suara-saja.

                else:
                    if sudah_menyapa and waktu_kini - waktu_terakhir_sapaan > COOLDOWN_SAPAAN:
                        sudah_menyapa = False
                        tampilkan_status("Area kosong. Mode standby.", "info")
                    time.sleep(DELAY_TANPA_ORANG)
                    continue

                time.sleep(DELAY_UTAMA)

    except KeyboardInterrupt:
        tampilkan_divider()
        tampilkan_status("Ctrl+C diterima.", "info")
        bicara("Friday dinonaktifkan. Sampai jumpa!")

    finally:
        wake_detector.hentikan()
        clap_detector.hentikan()
        proaktif.hentikan()
        memori.tutup()
        if _KAMERA_TERSEDIA:
            lepas_kamera(state["kamera_cap"])
        tutup_dashboard()
        tampilkan_divider()
        tampilkan_status("Friday berhasil dimatikan. Memori tersimpan.", "sukses")


# ==============================================================
if __name__ == "__main__":
    jalankan()
