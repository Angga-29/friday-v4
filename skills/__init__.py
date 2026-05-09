# ==============================================================
# skills/__init__.py — Project Friday v4.0 | Skill Manager
# Terinspirasi dari OpenJarvis Skills Ecosystem
# ==============================================================
"""
Skills dieksekusi SEBELUM Gemini — lebih cepat untuk perintah lokal.

Setiap skill module harus punya:
  NAMA          : str   — Nama tampilan
  PRIORITAS     : int   — Makin kecil = dicek lebih awal
  TRIGGER_WORDS : list  — Kata kunci pemicu
  jalankan(teks, **context) -> Optional[str]
"""

import importlib
import os
from typing import Optional


class SkillManager:
    """Memuat semua skill dari folder skills/ secara dinamis."""

    def __init__(self):
        self._skills = []
        self._muat_semua()

    def _muat_semua(self):
        skills_dir = os.path.dirname(os.path.abspath(__file__))
        for fname in sorted(os.listdir(skills_dir)):
            if fname.startswith('_') or not fname.endswith('.py'):
                continue
            nama_modul = fname[:-3]
            try:
                modul = importlib.import_module(f"skills.{nama_modul}")
                if hasattr(modul, 'TRIGGER_WORDS') and hasattr(modul, 'jalankan'):
                    self._skills.append(modul)
            except Exception:
                pass
        self._skills.sort(key=lambda m: getattr(m, 'PRIORITAS', 50))

    def cari_dan_jalankan(self, teks: str, **context) -> Optional[str]:
        """
        Cocokkan teks ke trigger words skill dan jalankan jika ketemu.
        Return string jawaban, atau None jika tidak ada skill yang cocok.
        """
        teks_lower = teks.lower()
        for skill in self._skills:
            if any(t in teks_lower for t in skill.TRIGGER_WORDS):
                try:
                    hasil = skill.jalankan(teks, **context)
                    if hasil is not None:
                        return hasil
                except Exception:
                    pass
        return None

    def daftar_skill(self) -> list:
        return [getattr(m, 'NAMA', m.__name__) for m in self._skills]
