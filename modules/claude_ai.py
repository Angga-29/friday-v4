# ==============================================================
# modules/claude_ai.py — Project Friday | Claude AI v5.0
# Versi : 5.0.0 — Otak utama Claude (Anthropic), pengganti Gemini
# ==============================================================

from modules.tampilan import tampilkan_status, tampilkan_memproses

MODEL_UTAMA      = "claude-sonnet-5"
MODEL_FALLBACK   = "claude-haiku-4-5-20251001"
MAX_TOKENS       = 600    # chat & browsing
MAX_TOKENS_RISET = 1200   # riset mendalam — butuh lebih banyak ruang

try:
    import anthropic
    _SDK_TERSEDIA = True
except ImportError:
    anthropic = None
    _SDK_TERSEDIA = False


class ClaudeAI:
    """
    Wrapper Claude (Anthropic) dengan interface sama seperti GeminiAI lama:
      - terhubung              → bool
      - tanya(perintah)        → str
      - tanya_stream(perintah) → generator[str]
      - tanya_dengan_web(...)  → str
      - tanya_riset(perintah)  → str (token limit lebih besar)
      - reset_sesi()
      - bangun_konteks(...)    → str

    History percakapan dikelola manual di self._history (Claude tidak
    punya sesi chat server-side seperti Gemini start_chat), mengikuti
    pola yang sama dengan modules/lokal_ai.py (Ollama).
    """

    def __init__(self, api_key: str, system_prompt: str, memori=None):
        self._terhubung    = False
        self._client       = None
        self._model_name   = MODEL_UTAMA
        self.system_prompt = system_prompt
        self.memori        = memori
        self._history      = []   # [{"role": "user"/"assistant", "content": str}, ...]

        if not _SDK_TERSEDIA:
            tampilkan_status(
                "Package 'anthropic' tidak terinstall!\n"
                "Jalankan: pip install anthropic",
                "error"
            )
            return

        if not api_key or "MASUKKAN" in api_key.upper():
            tampilkan_status(
                "API key Claude belum diisi. Set ANTHROPIC_API_KEY di .env atau config.py.",
                "error"
            )
            return

        try:
            self._client  = anthropic.Anthropic(api_key=api_key)
            self._system  = self._bangun_system_prompt(system_prompt)
            self._terhubung = True
            tampilkan_status(f"Claude AI siap (model: {self._model_name}).", "sukses")
        except Exception as e:
            tampilkan_status(f"Gagal init Claude AI: {e}", "error")

    # ----------------------------------------------------------
    # INIT & KONTEKS MEMORI
    # ----------------------------------------------------------
    def _model_tidak_ditemukan(self, err: str) -> bool:
        err = err.lower()
        return "not_found" in err or "model:" in err and "invalid" in err

    def _turunkan_ke_fallback(self):
        """Dipanggil saat model utama gagal (mis. belum tersedia di akun) — turun ke fallback."""
        if self._model_name != MODEL_FALLBACK:
            tampilkan_status(
                f"Model {self._model_name} gagal, beralih ke {MODEL_FALLBACK}...", "peringatan"
            )
            self._model_name = MODEL_FALLBACK

    def _bangun_system_prompt(self, base: str) -> str:
        if not self.memori:
            return base
        konteks = self._bangun_konteks_memori()
        return base + ("\n\n" + konteks if konteks else "")

    def _bangun_konteks_memori(self) -> str:
        if not self.memori:
            return ""
        bagian = []
        try:
            cur = self.memori.koneksi.cursor()
            cur.execute("SELECT kunci, nilai FROM preferensi LIMIT 10")
            prefs = cur.fetchall()
            if prefs:
                bagian.append("[YANG SAYA INGAT TENTANG PENGGUNA]")
                for k, v in prefs:
                    bagian.append(f"- {k}: {v}")
        except Exception:
            pass

        riwayat = self.memori.ambil_percakapan_terakhir(5)
        if riwayat:
            bagian.append("\n[PERCAKAPAN TERAKHIR — UNTUK KONTEKS]")
            for user, friday in riwayat:
                bagian.append(f"User  : {user}")
                bagian.append(f"Friday: {friday}")

        return "\n".join(bagian) if bagian else ""

    @property
    def terhubung(self) -> bool:
        return self._terhubung

    def _bersihkan(self, teks: str) -> str:
        teks = teks.replace("**", "").replace("*", "")
        teks = teks.replace("##", "").replace("#", "").replace("`", "")
        return teks.strip()

    def _simpan_history(self, perintah: str, jawaban: str):
        self._history.append({"role": "user", "content": perintah})
        self._history.append({"role": "assistant", "content": jawaban})
        if len(self._history) > 20:
            self._history = self._history[-20:]

    # ----------------------------------------------------------
    # TANYA — blocking
    # ----------------------------------------------------------
    def tanya(self, perintah: str) -> str:
        if not self._terhubung:
            return "Maaf, koneksi ke AI sedang bermasalah."
        tampilkan_memproses()
        try:
            resp = self._client.messages.create(
                model=self._model_name,
                max_tokens=MAX_TOKENS,
                system=self._system,
                temperature=0.75,
                messages=self._history[-10:] + [{"role": "user", "content": perintah}],
            )
            jawaban = self._bersihkan("".join(
                blok.text for blok in resp.content if blok.type == "text"
            ))
            self._simpan_history(perintah, jawaban)
            return jawaban
        except Exception as e:
            err = str(e)
            if "api_key" in err.lower() or "authentication" in err.lower():
                return "API key Claude tidak valid. Periksa config.py."
            if "rate_limit" in err.lower() or "429" in err:
                return "Kuota/rate limit Claude tercapai. Coba lagi nanti."
            if self._model_tidak_ditemukan(err):
                self._turunkan_ke_fallback()
                try:
                    resp = self._client.messages.create(
                        model=self._model_name,
                        max_tokens=MAX_TOKENS,
                        system=self._system,
                        temperature=0.75,
                        messages=self._history[-10:] + [{"role": "user", "content": perintah}],
                    )
                    jawaban = self._bersihkan("".join(
                        blok.text for blok in resp.content if blok.type == "text"
                    ))
                    self._simpan_history(perintah, jawaban)
                    return jawaban
                except Exception:
                    pass
            tampilkan_status(f"Error Claude: {err}", "error")
            return "Maaf, saya sedang mengalami gangguan."

    # ----------------------------------------------------------
    # TANYA STREAM — generator
    # ----------------------------------------------------------
    def tanya_stream(self, perintah: str):
        """
        Generator: yield potongan teks saat Claude streaming.

        Usage:
            teks = ""
            for chunk in ai.tanya_stream(prompt):
                display(chunk)
                teks += chunk
        """
        if not self._terhubung:
            yield "Maaf, koneksi ke AI bermasalah."
            return

        teks_total = []
        try:
            with self._client.messages.stream(
                model=self._model_name,
                max_tokens=MAX_TOKENS,
                system=self._system,
                temperature=0.75,
                messages=self._history[-10:] + [{"role": "user", "content": perintah}],
            ) as stream:
                for bagian in stream.text_stream:
                    bagian = bagian.replace("**", "").replace("*", "")
                    bagian = bagian.replace("##", "").replace("#", "").replace("`", "")
                    teks_total.append(bagian)
                    yield bagian
        except Exception as e:
            tampilkan_status(f"Stream error: {str(e)[:80]}", "peringatan")
            try:
                jawaban = self.tanya(perintah)
                yield jawaban
            except Exception:
                yield "Maaf, ada gangguan saat menghasilkan jawaban."
            return
        finally:
            teks_penuh = "".join(teks_total).strip()
            if teks_penuh:
                self._simpan_history(perintah, teks_penuh)

    def tanya_dengan_web(self, pertanyaan: str, konteks_web: str) -> str:
        if not self._terhubung:
            return "Maaf, koneksi ke AI bermasalah."
        return self.tanya(konteks_web)

    def tanya_riset(self, perintah: str) -> str:
        """Sama seperti tanya() tapi dengan token limit lebih besar untuk riset mendalam."""
        if not self._terhubung:
            return "Maaf, koneksi ke AI bermasalah."
        tampilkan_memproses()
        try:
            resp = self._client.messages.create(
                model=self._model_name,
                max_tokens=MAX_TOKENS_RISET,
                system=self.system_prompt,
                temperature=0.7,
                messages=[{"role": "user", "content": perintah}],
            )
            return self._bersihkan("".join(
                blok.text for blok in resp.content if blok.type == "text"
            ))
        except Exception as e:
            tampilkan_status(f"Error riset Claude: {e}", "error")
            return self.tanya(perintah)   # fallback ke tanya biasa

    def reset_sesi(self) -> None:
        self._history = []
        tampilkan_status("Sesi percakapan direset.", "info")

    def bangun_konteks(self, suara_user, waktu, cuaca, berita):
        # berita bisa list[dict] (format baru) atau list[str] (lama)
        if berita:
            judul_list = []
            for b in berita:
                if isinstance(b, dict):
                    sumber = b.get("sumber", "").strip()
                    judul = b.get("judul", "").strip()
                    judul_list.append(f"{sumber}: {judul}" if sumber else judul)
                else:
                    judul_list.append(str(b))
            berita_str = " | ".join(judul_list)
        else:
            berita_str = "tidak tersedia"
        return (
            f"[KONTEKS REAL-TIME]\n"
            f"Waktu  : {waktu}\n"
            f"Cuaca  : {cuaca}\n"
            f"Berita : {berita_str}\n\n"
            f"[PERINTAH PENGGUNA]\n{suara_user}"
        )
