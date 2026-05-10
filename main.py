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
#   Versi    : 4.0.0 — Powered by OpenJarvis Concepts
#   Platform : Termux (Android) + IP Webcam + Xiaomi Pad 7
#   Author   : Angga
#   Engine   : Gemini 2.5 Flash + Skills + Deep Research + Vision
#
#   FITUR BARU v4.0 (terinspirasi OpenJarvis):
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
import threading

import config
from modules.tampilan    import (
    tampilkan_header, tampilkan_status, tampilkan_divider,
    pop_up_berita, tampilkan_browsing, tampilkan_vision,
    tampilkan_statistik, tampilkan_app_dibuka, tampilkan_musik
)
from modules.suara       import bicara
from modules.pendengar   import dengarkan
from modules.info        import dapatkan_waktu, dapatkan_cuaca, dapatkan_berita
from modules.gemini_ai   import GeminiAI
from modules.browser     import perlu_browsing, cari_web, format_untuk_gemini
from modules.memori      import MemoriFriday
from modules.wake_word   import WakeWordDetector
from modules.penglihatan import perlu_penglihatan, deskripsikan_pemandangan
from modules.proaktif    import ModeProaktif
from modules.riset       import perlu_riset, riset_mendalam
from skills              import SkillManager

# Import modul kamera & wajah — opsional (tidak crash jika tidak tersedia)
try:
    from modules.kamera import ambil_frame, inisialisasi_kamera, ke_grayscale_blur
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
    "memori"          : None,
    "skill_manager"   : None,
    "frame_terakhir"  : None,
    "cache_waktu"     : "",
    "cache_cuaca"     : "",
    "cache_berita"    : [],
    "tanpa_kamera"    : False,   # True = mode suara saja
}


# ==============================================================
# CALLBACK WAKE WORD
# ==============================================================
def on_wake_word(teks_terdeteksi):
    state["wake_triggered"] = True


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
        tampilkan_status("Pastikan OpenCV terinstall: pkg install python-opencv", "info")
        if kamera_wajib:
            sys.exit(1)
        state["tanpa_kamera"] = True
    else:
        frame_awal = inisialisasi_kamera(config.URL_KAMERA)
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

    # 4. Gemini AI dengan memori
    ai = GeminiAI(
        api_key=config.API_KEY_GEMINI,
        system_prompt=config.SYSTEM_PROMPT_FRIDAY,
        memori=memori
    )
    if not ai.terhubung:
        sys.exit(1)
    state["ai"] = ai

    # 5. Skills System (OpenJarvis-inspired)
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

    return ai, pengenal, memori, wake_detector, proaktif, skill_manager


# ==============================================================
# HANDLER PROSES JAWABAN
# ==============================================================
def proses_jawaban(suara_user, ai, memori, skill_manager):
    """Proses input user. Return True jika harus keluar."""
    teks_lower   = suara_user.lower()
    cache_waktu  = state["cache_waktu"]
    cache_cuaca  = state["cache_cuaca"]
    cache_berita = state["cache_berita"]

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

    # ── 5. SKILLS (OpenJarvis-inspired lokal execution) ──────────
    hasil_skill = skill_manager.cari_dan_jalankan(
        suara_user,
        callback_bicara=bicara,
    )
    if hasil_skill is not None:
        tampilkan_status("Dijawab oleh skill lokal.", "sukses")
        bicara(hasil_skill)
        memori.simpan_percakapan(suara_user, hasil_skill, tipe="skill")
        memori.catat_interaksi("skill")
        return False

    # ── 6. RISET MENDALAM (OpenJarvis Research Agent) ────────────
    if perlu_riset(suara_user):
        tampilkan_status("Mode riset mendalam aktif.", "browsing")
        bicara("Baik, saya akan melakukan riset mendalam. Mohon tunggu sebentar.")
        jawaban = riset_mendalam(suara_user, ai)
        bicara(jawaban)
        memori.simpan_percakapan(suara_user, jawaban, pakai_web=True, tipe="riset")
        memori.catat_interaksi("riset")
        return False

    # ── 7. VISION (Gemini lihat kamera) ──────────────────────────
    if perlu_penglihatan(suara_user):
        tampilkan_vision()
        jawaban = deskripsikan_pemandangan(
            state["frame_terakhir"], suara_user, config.API_KEY_GEMINI
        )
        bicara(jawaban)
        memori.simpan_percakapan(suara_user, jawaban, pakai_web=False, tipe="vision")
        return False

    # ── 8. BROWSING (pencarian web cepat) ────────────────────────
    if perlu_browsing(suara_user):
        tampilkan_status("Pertanyaan perlu browsing.", "browsing")
        bicara("Baik, saya carikan dari internet.")
        tampilkan_browsing(suara_user)
        hasil_web    = cari_web(suara_user)
        konteks_web  = format_untuk_gemini(suara_user, hasil_web)
        konteks_penuh = (
            f"[KONTEKS]\nWaktu: {cache_waktu}\nCuaca: {cache_cuaca}\n\n"
            + konteks_web
        )
        jawaban = ai.tanya_dengan_web(suara_user, konteks_penuh)
        bicara(jawaban)
        memori.simpan_percakapan(suara_user, jawaban, pakai_web=True, tipe="browsing")
        memori.catat_interaksi("browsing")
        return False

    # ── 9. GEMINI CHAT (fallback utama) ──────────────────────────
    perintah = ai.bangun_konteks(
        suara_user=suara_user, waktu=cache_waktu,
        cuaca=cache_cuaca, berita=cache_berita
    )
    jawaban = ai.tanya(perintah)
    bicara(jawaban)
    memori.simpan_percakapan(suara_user, jawaban, tipe="chat")
    memori.catat_interaksi("interaksi")
    return False


# ==============================================================
# UPDATE CACHE DATA REAL-TIME
# ==============================================================
def update_cache_data():
    state["cache_waktu"]  = dapatkan_waktu()
    state["cache_cuaca"]  = dapatkan_cuaca(config.API_KEY_CUACA, config.KOTA_CUACA)
    state["cache_berita"] = dapatkan_berita(config.API_KEY_BERITA, jumlah=3)


# ==============================================================
# LOOP UTAMA
# ==============================================================
def jalankan():
    ai, pengenal, memori, wake_detector, proaktif, skill_manager = inisialisasi_semua()

    update_cache_data()

    sudah_menyapa         = False
    frame_lama_gray       = None
    waktu_terakhir_sapaan = 0
    waktu_terakhir_gerak  = 0
    waktu_gerak_terakhir  = 0

    bicara(
        f"Sistem siap, Bos {config.NAMA_PENGGUNA}. "
        "Versi empat aktif dengan skill system dan riset mendalam. "
        "Panggil saya dengan hai Friday kapan saja."
    )

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

                    suara_user = dengarkan(setelah_tts=True)
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
                frame = ambil_frame(config.URL_KAMERA)
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

                    suara_user = dengarkan(setelah_tts=True)
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
                            bicara(f"Halo, {nama_dikenal}! {state['cache_waktu']}")
                            memori.catat_interaksi("wajah")
                        else:
                            bicara(f"Halo, Bos {config.NAMA_PENGGUNA}! {state['cache_waktu']}")

                        time.sleep(0.4)
                        bicara(f"Laporan cuaca. {state['cache_cuaca']}")
                        time.sleep(0.4)
                        bicara(
                            "Saya siap membantu. Bisa bertanya apa saja, "
                            "atau panggil saya dengan hai Friday."
                        )

                    # ── 6. DENGARKAN ─────────────────────────────────
                    suara_user = dengarkan(setelah_tts=True)
                    if suara_user:
                        if proses_jawaban(suara_user, ai, memori, skill_manager):
                            break
                        time.sleep(1)
                    else:
                        bicara("Maaf, saya tidak mendengar. Silakan ulangi.")

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
        proaktif.hentikan()
        memori.tutup()
        tampilkan_divider()
        tampilkan_status("Friday berhasil dimatikan. Memori tersimpan.", "sukses")


# ==============================================================
if __name__ == "__main__":
    jalankan()
