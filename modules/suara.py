# ==============================================================
# modules/suara.py — Project Friday | Modul TTS
# Versi : 5.0.0 — Port ke Windows: pyttsx3 (SAPI5) ganti Termux TTS
# ==============================================================
"""
Urutan fallback TTS:
  1. Edge-TTS  (Microsoft Neural, online, suara terbaik)
  2. pyttsx3   (SAPI5 Windows, offline, native — pengganti termux-tts-speak)
  3. gTTS      (Google TTS, online)

Urutan fallback audio player (semua BLOCKING):
  mpv → ffplay

Anti-echo:
  _sedang_bicara (threading.Event) di-set SEBELUM audio diputar
  dan di-clear SETELAH audio + jeda reverb selesai.
  pendengar.py dan wake_word.py membaca flag ini.
"""

import os
import re
import time
import threading
import subprocess
from modules.tampilan import tampilkan_friday_bicara, tampilkan_status

EDGE_VOICE = "en-GB-RyanNeural"   # British male — paling mirip JARVIS

_TMPDIR    = os.environ.get("TMPDIR") or os.path.dirname(os.path.abspath(__file__))
TEMP_AUDIO = os.path.join(_TMPDIR, "friday_voice.mp3")

# ── Flag anti-echo — dibaca oleh pendengar.py dan wake_word.py ──
_sedang_bicara      = threading.Event()
_interrupt_event    = threading.Event()   # barge-in: set → potong audio
_proses_audio       = None                # subprocess player yang sedang berjalan
_teks_terakhir      = ""
_mpv_missing_logged = False


def sedang_bicara() -> bool:
    return _sedang_bicara.is_set()


def teks_terakhir_diucapkan() -> str:
    return _teks_terakhir


def stop_bicara():
    """Interrupt Friday di tengah bicara (barge-in). Aman dipanggil dari thread manapun."""
    global _proses_audio
    _interrupt_event.set()
    proc = _proses_audio
    if proc and proc.poll() is None:
        try:
            proc.terminate()
        except Exception:
            pass
    tampilkan_status("⏹ Dihentikan (barge-in).", "info")


def _bersihkan_teks(teks: str) -> str:
    teks = teks.replace("*", "").replace("#", "").replace("`", "")
    teks = teks.replace('"', "").replace("'", "")
    teks = re.sub(r'[\x00-\x1f\x7f]', '', teks)
    return teks.strip()


def _edge_tts_tersedia() -> bool:
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


def _generate_edge_tts_sync(teks: str) -> bool:
    """
    Generate MP3 Edge-TTS di thread terpisah dengan event loop baru.
    Cara ini menghindari konflik dengan event loop asyncio yang mungkin
    sudah jalan di thread utama (wake word, proaktif, dll).
    """
    hasil = [False]

    def _run():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            import edge_tts
            communicate = edge_tts.Communicate(teks, EDGE_VOICE)
            loop.run_until_complete(communicate.save(TEMP_AUDIO))
            hasil[0] = True
        except ImportError:
            pass
        except Exception as e:
            tampilkan_status(f"Edge-TTS error: {e}", "peringatan")
        finally:
            loop.close()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=30)
    return hasil[0]


def _putar_audio(file_path: str) -> bool:
    """
    Putar audio dengan Popen + polling — mendukung barge-in (interrupt).
    Jika _interrupt_event di-set saat audio berjalan, player langsung dimatikan.
    """
    global _mpv_missing_logged, _proses_audio

    try:
        ukuran = os.path.getsize(file_path)
        if ukuran < 512:
            tampilkan_status(f"File audio terlalu kecil ({ukuran}b) — skip.", "peringatan")
            return False
    except OSError:
        return False

    players = [
        ("mpv",    ["mpv", "--no-video", "--volume=100",
                    "--quiet", "--really-quiet", file_path]),
        ("ffplay", ["ffplay", "-nodisp", "-autoexit",
                    "-volume", "100", "-loglevel", "quiet", file_path]),
    ]

    for nama, cmd in players:
        try:
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.PIPE)
            _proses_audio = proc

            # Poll setiap 50ms — cek interrupt
            while proc.poll() is None:
                if _interrupt_event.is_set():
                    proc.terminate()
                    try:
                        proc.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    _proses_audio = None
                    return True   # dianggap selesai (diinterrupt)
                time.sleep(0.05)

            _proses_audio = None
            rc = proc.returncode
            if rc == 0:
                tampilkan_status(f"Audio selesai via {nama}.", "info")
                return True
            err = proc.stderr.read().decode(errors="ignore").strip()
            if err:
                tampilkan_status(f"{nama} gagal: {err[:120]}", "peringatan")
        except FileNotFoundError:
            continue
        except Exception as e:
            tampilkan_status(f"{nama} error: {e}", "peringatan")
            continue

    if not _mpv_missing_logged:
        _mpv_missing_logged = True
        tampilkan_status(
            "mpv/ffplay tidak bisa memutar audio → pakai pyttsx3 sebagai fallback.",
            "peringatan"
        )
    return False


def _bicara_pyttsx3(teks: str) -> bool:
    """
    TTS offline via pyttsx3 (membungkus SAPI5 di Windows).
    Dijalankan di thread terpisah supaya bisa diinterupsi (barge-in)
    lewat engine.stop() tanpa memblokir thread utama.
    """
    try:
        import pyttsx3
    except ImportError:
        return False

    try:
        engine = pyttsx3.init()
    except Exception as e:
        tampilkan_status(f"pyttsx3 gagal init: {e}", "peringatan")
        return False

    hasil = [False]

    def _run():
        try:
            engine.say(teks)
            engine.runAndWait()
            hasil[0] = True
        except Exception as e:
            tampilkan_status(f"pyttsx3 error: {e}", "peringatan")

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    while t.is_alive():
        if _interrupt_event.is_set():
            try:
                engine.stop()
            except Exception:
                pass
            t.join(timeout=1)
            return True   # dianggap selesai (diinterrupt)
        time.sleep(0.05)

    return hasil[0]


def bicara(teks: str) -> None:
    """
    Friday berbicara. Mendukung barge-in: jika stop_bicara() dipanggil
    dari thread lain saat audio berjalan, audio langsung berhenti.
    """
    global _teks_terakhir

    tampilkan_friday_bicara(teks)
    teks_bersih = _bersihkan_teks(teks)
    if not teks_bersih:
        return

    _teks_terakhir = teks_bersih.lower()
    _interrupt_event.clear()
    _sedang_bicara.set()

    # Update dashboard status → tombol STOP muncul di Chrome
    try:
        from modules.dashboard import update_data as _du
        _du(status="Berbicara")
    except Exception:
        pass

    try:
        _bicara_internal(teks_bersih)
    finally:
        jeda = 0.5 if _interrupt_event.is_set() else 2.0
        _interrupt_event.clear()
        time.sleep(jeda)
        _sedang_bicara.clear()
        # Kembalikan status dashboard ke Standby
        try:
            from modules.dashboard import update_data as _du
            _du(status="Standby")
        except Exception:
            pass


def _bicara_internal(teks_bersih: str) -> None:
    """TTS internal — dipanggil dari bicara() saat flag sudah di-set."""

    # ── PRIORITAS 1: Edge-TTS (jalan di thread sendiri, tidak bentrok asyncio) ──
    if _edge_tts_tersedia():
        sukses = _generate_edge_tts_sync(teks_bersih)

        if sukses and os.path.exists(TEMP_AUDIO):
            if _putar_audio(TEMP_AUDIO):
                try:
                    os.remove(TEMP_AUDIO)
                except OSError:
                    pass
                return
            try:
                os.remove(TEMP_AUDIO)
            except OSError:
                pass

    # ── PRIORITAS 2: pyttsx3 / SAPI5 Windows (offline, interruptible) ──
    tampilkan_status("Bicara via pyttsx3 (SAPI5)...", "info")
    if _bicara_pyttsx3(teks_bersih):
        tampilkan_status("Audio selesai via pyttsx3.", "info")
        return

    # ── PRIORITAS 3: gTTS + audio player ──────────────────
    try:
        from gtts import gTTS
        tts = gTTS(text=teks_bersih, lang='id', slow=False)
        tts.save(TEMP_AUDIO)
        if _putar_audio(TEMP_AUDIO):
            try:
                os.remove(TEMP_AUDIO)
            except OSError:
                pass
            return
        try:
            os.remove(TEMP_AUDIO)
        except OSError:
            pass
    except ImportError:
        pass
    except Exception as e:
        tampilkan_status(f"gTTS error: {e}", "peringatan")
