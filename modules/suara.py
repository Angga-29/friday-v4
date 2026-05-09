# ==============================================================
# modules/suara.py — Project Friday | Modul TTS Premium
# Versi : 3.0.1 — Triple fallback: Edge-TTS → Termux → gTTS
# ==============================================================
"""
Sistem suara dengan 3 tingkat fallback:

PRIORITAS 1: Microsoft Edge-TTS (suara premium, natural, gratis, online)
PRIORITAS 2: Termux TTS (offline, robotik, native Android)
PRIORITAS 3: Google gTTS (online, cukup natural)
"""

import os
import re
import asyncio
import subprocess
from modules.tampilan import tampilkan_friday_bicara, tampilkan_status

# Suara Edge-TTS Bahasa Indonesia (suara wanita natural)
EDGE_VOICE = "id-ID-GadisNeural"   # Alternatif: id-ID-ArdiNeural (pria)

# Gunakan $TMPDIR dari Termux agar tidak Permission Denied di Android.
# Fallback ke folder modules jika TMPDIR tidak tersedia.
_TMPDIR = os.environ.get("TMPDIR") or os.path.dirname(os.path.abspath(__file__))
TEMP_AUDIO = os.path.join(_TMPDIR, "friday_voice.mp3")


def _bersihkan_teks(teks: str) -> str:
    """Bersihkan karakter pengganggu TTS."""
    teks = teks.replace("*", "").replace("#", "").replace("`", "")
    teks = teks.replace('"', "").replace("'", "")
    teks = re.sub(r'[\x00-\x1f\x7f]', '', teks)
    return teks.strip()


def _edge_tts_tersedia() -> bool:
    """Cek apakah edge-tts terinstall."""
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


async def _generate_edge_tts(teks: str) -> bool:
    """Generate audio dengan Edge-TTS, simpan ke file."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(teks, EDGE_VOICE)
        await communicate.save(TEMP_AUDIO)
        return True
    except ImportError:
        # Sudah dicek di _edge_tts_tersedia(), tidak perlu log lagi
        return False
    except Exception as e:
        tampilkan_status(f"Edge-TTS error: {e}", "peringatan")
        return False


def _putar_audio(file_path: str) -> bool:
    """
    Putar file audio menggunakan mpv, ffplay, atau play (sox).
    Menggunakan subprocess.run() agar aman dari shell injection.
    """
    players = [
        ["mpv", "--no-video", "--volume=100", "--quiet", "--really-quiet", file_path],
        ["ffplay", "-nodisp", "-autoexit", "-volume", "100", "-loglevel", "quiet", file_path],
        ["play", "-q", file_path],
    ]
    for cmd in players:
        try:
            ret = subprocess.run(cmd, capture_output=True, timeout=60)
            if ret.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False


def bicara(teks: str) -> None:
    """
    Friday berbicara dengan triple fallback:
    Edge-TTS → Termux TTS → gTTS
    """
    tampilkan_friday_bicara(teks)
    teks_bersih = _bersihkan_teks(teks)
    if not teks_bersih:
        return

    # ── PRIORITAS 1: Edge-TTS (suara premium Microsoft) ──
    if _edge_tts_tersedia():
        try:
            sukses = asyncio.run(_generate_edge_tts(teks_bersih))
            if sukses and os.path.exists(TEMP_AUDIO):
                if _putar_audio(TEMP_AUDIO):
                    try:
                        os.remove(TEMP_AUDIO)
                    except OSError:
                        pass
                    return
                tampilkan_status("Audio gagal diputar, fallback...", "peringatan")
        except RuntimeError:
            # asyncio.run() gagal jika ada event loop aktif
            try:
                loop = asyncio.new_event_loop()
                sukses = loop.run_until_complete(_generate_edge_tts(teks_bersih))
                loop.close()
                if sukses and os.path.exists(TEMP_AUDIO):
                    if _putar_audio(TEMP_AUDIO):
                        try:
                            os.remove(TEMP_AUDIO)
                        except OSError:
                            pass
                        return
            except Exception:
                pass
        except Exception as e:
            tampilkan_status(f"Edge-TTS gagal: {e}", "peringatan")

    # ── PRIORITAS 2: Termux TTS (cepat, offline) ──
    try:
        ret = subprocess.run(
            ["termux-tts-speak", teks_bersih],
            capture_output=True,
            timeout=30
        )
        if ret.returncode == 0:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # Termux TTS tidak tersedia

    # ── PRIORITAS 3: gTTS (Google TTS) ──
    tampilkan_status("Termux TTS tidak tersedia, mencoba gTTS...", "peringatan")
    try:
        from gtts import gTTS
        tts = gTTS(text=teks_bersih, lang='id', slow=False)
        tts.save(TEMP_AUDIO)
        _putar_audio(TEMP_AUDIO)
        try:
            if os.path.exists(TEMP_AUDIO):
                os.remove(TEMP_AUDIO)
        except OSError:
            pass
    except ImportError:
        tampilkan_status("Tidak ada engine TTS yang tersedia!", "error")
    except Exception as e:
        tampilkan_status(f"Error TTS final: {e}", "error")
