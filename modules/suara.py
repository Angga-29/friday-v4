# ==============================================================
# modules/suara.py — Project Friday | Modul TTS
# Versi : 4.2.0 — Fix kritis: hapus duplikasi bicara(), anti-echo benar
# ==============================================================
"""
Urutan fallback TTS:
  1. Edge-TTS  (Microsoft Neural, online, suara terbaik)
  2. Termux TTS (termux-tts-speak, offline, native Android)
  3. gTTS       (Google TTS, online)

Urutan fallback audio player (semua BLOCKING):
  mpv → ffplay → play (sox)

CATATAN: termux-media-player SENGAJA tidak dipakai karena
perintah 'play' bersifat non-blocking — audio masih berjalan
di background sementara subprocess sudah return, sehingga
_sedang_bicara di-clear terlalu cepat dan menyebabkan
Friday mendengar suaranya sendiri.

Anti-echo:
  _sedang_bicara (threading.Event) di-set SEBELUM audio diputar
  dan di-clear SETELAH audio + jeda reverb selesai.
  pendengar.py dan wake_word.py membaca flag ini.
"""

import os
import re
import time
import asyncio
import threading
import subprocess
from modules.tampilan import tampilkan_friday_bicara, tampilkan_status

EDGE_VOICE = "id-ID-GadisNeural"

_TMPDIR    = os.environ.get("TMPDIR") or os.path.dirname(os.path.abspath(__file__))
TEMP_AUDIO = os.path.join(_TMPDIR, "friday_voice.mp3")

# ── Flag anti-echo — dibaca oleh pendengar.py dan wake_word.py ──
_sedang_bicara      = threading.Event()
_teks_terakhir      = ""
_mpv_missing_logged = False


def sedang_bicara() -> bool:
    """Return True saat Friday sedang memutar audio TTS."""
    return _sedang_bicara.is_set()


def teks_terakhir_diucapkan() -> str:
    """Return teks terakhir yang diucapkan Friday — untuk deteksi echo."""
    return _teks_terakhir


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


async def _generate_edge_tts(teks: str) -> bool:
    try:
        import edge_tts
        communicate = edge_tts.Communicate(teks, EDGE_VOICE)
        await communicate.save(TEMP_AUDIO)
        return True
    except ImportError:
        return False
    except Exception as e:
        tampilkan_status(f"Edge-TTS error: {e}", "peringatan")
        return False


def _putar_audio(file_path: str) -> bool:
    """
    Putar audio dengan player yang tersedia — semua BLOCKING.
    termux-media-player TIDAK dipakai karena non-blocking.
    """
    global _mpv_missing_logged

    # Cek ukuran file — MP3 kosong/corrupt tidak perlu diputar
    try:
        ukuran = os.path.getsize(file_path)
        if ukuran < 512:
            tampilkan_status(f"File audio terlalu kecil ({ukuran} bytes) — skip.", "peringatan")
            return False
    except OSError:
        return False

    players = [
        ("mpv",    ["mpv", "--no-video", "--volume=100",
                    "--quiet", "--really-quiet", file_path]),
        ("ffplay", ["ffplay", "-nodisp", "-autoexit",
                    "-volume", "100", "-loglevel", "quiet", file_path]),
        ("play",   ["play", "-q", file_path]),
    ]

    for nama, cmd in players:
        try:
            ret = subprocess.run(cmd, capture_output=True, timeout=120)
            if ret.returncode == 0:
                tampilkan_status(f"Audio diputar via {nama}.", "info")
                return True
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            tampilkan_status(f"{nama} timeout saat memutar audio.", "peringatan")
            continue

    if not _mpv_missing_logged:
        _mpv_missing_logged = True
        tampilkan_status(
            "Tidak ada audio player! Suara tidak keluar.\n"
            "  Install: pkg install mpv",
            "error"
        )
    return False


def bicara(teks: str) -> None:
    """
    Friday berbicara.
    Set _sedang_bicara SEBELUM audio → clear SETELAH audio + jeda reverb.
    Ini mencegah pendengar.py merekam saat Friday masih berbicara.
    """
    global _teks_terakhir

    tampilkan_friday_bicara(teks)
    teks_bersih = _bersihkan_teks(teks)
    if not teks_bersih:
        return

    _teks_terakhir = teks_bersih.lower()
    _sedang_bicara.set()

    try:
        _bicara_internal(teks_bersih)
    finally:
        time.sleep(2.0)
        _sedang_bicara.clear()


def _bicara_internal(teks_bersih: str) -> None:
    """TTS internal — dipanggil dari bicara() saat flag sudah di-set."""

    # ── PRIORITAS 1: Edge-TTS ──────────────────────────────
    if _edge_tts_tersedia():
        try:
            sukses = asyncio.run(_generate_edge_tts(teks_bersih))
        except RuntimeError:
            try:
                loop = asyncio.new_event_loop()
                sukses = loop.run_until_complete(_generate_edge_tts(teks_bersih))
                loop.close()
            except Exception:
                sukses = False
        except Exception as e:
            tampilkan_status(f"Edge-TTS gagal: {e}", "peringatan")
            sukses = False

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

    # ── PRIORITAS 2: Termux TTS (blocking, offline) ────────
    try:
        ret = subprocess.run(
            ["termux-tts-speak", teks_bersih],
            capture_output=True, timeout=60
        )
        if ret.returncode == 0:
            return
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        tampilkan_status("Termux TTS timeout.", "peringatan")

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
