# ==============================================================
# modules/suara.py — Project Friday | Modul TTS Premium
# Versi : 4.1.0 — Fix echo: flag sedang_bicara + buffer audio
# ==============================================================
"""
Urutan fallback TTS:
  1. Edge-TTS  (Microsoft Neural, online, suara terbaik)
  2. Termux TTS (termux-tts-speak, offline, native Android)
  3. gTTS       (Google TTS, online)

Urutan fallback audio player:
  mpv → ffplay → termux-media-player → play (sox)

Anti-echo:
  _sedang_bicara (threading.Event) di-set saat audio diputar.
  wake_word.py dan pendengar.py membaca ini agar tidak merekam
  saat Friday sedang berbicara.
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

# ── Flag anti-echo — dibaca oleh wake_word.py dan pendengar.py ──
_sedang_bicara      = threading.Event()
_mpv_missing_logged = False
_teks_terakhir      = ""   # teks terakhir yang diucapkan Friday


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
    global _mpv_missing_logged
    players = [
        ("mpv",                ["mpv", "--no-video", "--volume=100",
                                "--quiet", "--really-quiet", file_path]),
        ("ffplay",             ["ffplay", "-nodisp", "-autoexit",
                                "-volume", "100", "-loglevel", "quiet", file_path]),
        ("termux-media-player",["termux-media-player", "play", file_path]),
        ("play/sox",           ["play", "-q", file_path]),
    ]
    for nama, cmd in players:
        try:
            ret = subprocess.run(cmd, capture_output=True, timeout=60)
            if ret.returncode == 0:
                return True
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            continue

    if not _mpv_missing_logged:
        _mpv_missing_logged = True
        tampilkan_status("Tidak ada audio player! Jalankan: pkg install mpv", "error")
    return False


def bicara(teks: str) -> None:
    """Friday berbicara — set flag anti-echo sebelum dan setelah audio."""
    global _teks_terakhir
    tampilkan_friday_bicara(teks)
    teks_bersih = _bersihkan_teks(teks)
    if not teks_bersih:
        return

    # Simpan teks untuk deteksi echo nanti di pendengar
    _teks_terakhir = teks_bersih.lower()

    # ── Aktifkan flag: mikrofon tidak boleh merekam ─────────
    _sedang_bicara.set()

    try:
        _bicara_internal(teks_bersih)
    finally:
        # ── Jeda lebih panjang setelah audio selesai ───────
        # Memberi waktu gema/reverb di ruangan untuk hilang
        time.sleep(2.0)
        _sedang_bicara.clear()


def _bicara_internal(teks_bersih: str) -> None:
    """Logika TTS internal — dipanggil dari bicara()."""

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

    # ── PRIORITAS 2: Termux TTS ────────────────────────────
    try:
        ret = subprocess.run(
            ["termux-tts-speak", teks_bersih],
            capture_output=True, timeout=30
        )
        if ret.returncode == 0:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # ── PRIORITAS 3: gTTS ──────────────────────────────────
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
"""
Urutan fallback TTS:
  1. Edge-TTS  (Microsoft Neural, online, suara terbaik)
  2. Termux TTS (termux-tts-speak, offline, native Android)
  3. gTTS       (Google TTS, online)

Urutan fallback audio player:
  mpv → ffplay → termux-media-player → play (sox) → am startservice
"""

import os
import re
import asyncio
import subprocess
from modules.tampilan import tampilkan_friday_bicara, tampilkan_status

EDGE_VOICE = "id-ID-GadisNeural"   # Alternatif pria: id-ID-ArdiNeural

_TMPDIR    = os.environ.get("TMPDIR") or os.path.dirname(os.path.abspath(__file__))
TEMP_AUDIO = os.path.join(_TMPDIR, "friday_voice.mp3")

# Catat sekali saja agar tidak spam
_mpv_missing_logged = False


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
    Coba putar file audio dengan urutan player yang tersedia.
    Menampilkan peringatan jelas jika semua player gagal.
    """
    global _mpv_missing_logged

    players = [
        # format: (nama_display, [perintah...])
        ("mpv",                ["mpv", "--no-video", "--volume=100",
                                "--quiet", "--really-quiet", file_path]),
        ("ffplay",             ["ffplay", "-nodisp", "-autoexit",
                                "-volume", "100", "-loglevel", "quiet", file_path]),
        ("termux-media-player",["termux-media-player", "play", file_path]),
        ("play/sox",           ["play", "-q", file_path]),
    ]

    for nama, cmd in players:
        try:
            ret = subprocess.run(cmd, capture_output=True, timeout=60)
            if ret.returncode == 0:
                return True
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            continue

    # Semua player gagal — tampilkan pesan jelas SATU KALI
    if not _mpv_missing_logged:
        _mpv_missing_logged = True
        tampilkan_status(
            "Tidak ada audio player! Install mpv agar suara keluar:", "error"
        )
        tampilkan_status("  pkg install mpv", "info")
        tampilkan_status(
            "Atau install Termux:API dari Play Store → pkg install termux-api",
            "info"
        )
    return False


def bicara(teks: str) -> None:
    """Friday berbicara — Edge-TTS → Termux TTS → gTTS."""
    tampilkan_friday_bicara(teks)
    teks_bersih = _bersihkan_teks(teks)
    if not teks_bersih:
        return

    # ── PRIORITAS 1: Edge-TTS ──────────────────────────────────
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
            # Audio file ada tapi tidak bisa diputar
            try:
                os.remove(TEMP_AUDIO)
            except OSError:
                pass

    # ── PRIORITAS 2: Termux TTS (offline, native) ─────────────
    try:
        ret = subprocess.run(
            ["termux-tts-speak", teks_bersih],
            capture_output=True, timeout=30
        )
        if ret.returncode == 0:
            return
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        tampilkan_status("Termux TTS timeout.", "peringatan")

    # ── PRIORITAS 3: gTTS + audio player ──────────────────────
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

    # Semua gagal — pesan hanya ditampilkan oleh _putar_audio()
