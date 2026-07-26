# ==============================================================
# modules/overlay.py — Project Friday | Widget Logo Mengambang
# ==============================================================
"""
Window kecil frameless, transparan, always-on-top, bisa di-drag ke
mana saja -- menampilkan logo Friday + ring animasi (konten sama
dengan dashboard.py lewat endpoint /widget), posisi default di
tengah-atas layar.

WAJIB dijalankan di MAIN THREAD (batasan GUI toolkit di Windows) --
lihat main.py: loop asisten (jalankan()) berjalan di background thread,
overlay ini yang pegang thread utama lewat mulai_overlay() (blocking).

Overlay ini OPSIONAL -- kalau package 'pywebview' belum terinstall,
atau GUI gagal jalan (mis. tidak ada WebView2/display), Friday tetap
jalan normal tanpa widget visual (fallback ke dashboard browser saja).
"""

WIDGET_WIDTH  = 160
WIDGET_HEIGHT = 160
WIDGET_Y      = 20   # jarak dari tepi atas layar (px)


def tersedia() -> bool:
    """Cek apakah pywebview terinstall -- overlay bersifat opsional."""
    try:
        import webview  # noqa: F401
        return True
    except ImportError:
        return False


def _lebar_layar() -> int:
    """Lebar layar utama Windows (untuk posisi tengah-atas). Fallback 1920 di OS lain."""
    try:
        import ctypes
        return ctypes.windll.user32.GetSystemMetrics(0)
    except (AttributeError, OSError):
        return 1920


def mulai_overlay():
    """
    Jalankan widget mengambang. BLOCKING -- menjalankan event loop GUI,
    wajib dipanggil dari main thread. Return begitu window ditutup
    (lewat tutup_overlay(), atau user menutup Friday).
    """
    try:
        import webview
    except ImportError:
        from modules.tampilan import tampilkan_status
        tampilkan_status(
            "pywebview tidak terinstall — widget mengambang dilewati "
            "(Friday tetap jalan normal). Install: pip install pywebview",
            "peringatan"
        )
        return

    from modules.dashboard import PORT
    lebar_layar = _lebar_layar()
    x = max(0, (lebar_layar - WIDGET_WIDTH) // 2)

    try:
        webview.create_window(
            title="Friday",
            url=f"http://localhost:{PORT}/widget",
            width=WIDGET_WIDTH,
            height=WIDGET_HEIGHT,
            x=x,
            y=WIDGET_Y,
            frameless=True,
            easy_drag=True,
            on_top=True,
            transparent=True,
            resizable=False,
        )
        webview.start()
    except Exception as e:
        try:
            from modules.tampilan import tampilkan_status
            tampilkan_status(f"Widget mengambang gagal jalan: {e}", "peringatan")
        except Exception:
            pass


def tutup_overlay():
    """Tutup semua window overlay -- dipanggil saat Friday dimatikan."""
    try:
        import webview
        for w in list(webview.windows):
            try:
                w.destroy()
            except Exception:
                pass
    except ImportError:
        pass
