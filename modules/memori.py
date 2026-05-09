# ==============================================================
# modules/memori.py — Project Friday v4.0 | Memori Permanen
# Engine : SQLite (built-in Python)
# Update : Auto-prune + kolom tipe + statistik skill/riset
#          Terinspirasi OpenJarvis Session Auto-Decay Management
# ==============================================================
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from modules.tampilan import tampilkan_status

DB_DIR  = Path.home() / ".friday_memory"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "friday.db"

MAX_PERCAKAPAN = 200   # Prune otomatis jika melebihi ini


class MemoriFriday:
    def __init__(self):
        self.koneksi = None
        self._init_db()

    def _init_db(self):
        try:
            self.koneksi = sqlite3.connect(str(DB_PATH))
            cur = self.koneksi.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS percakapan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                waktu TEXT, teks_user TEXT, teks_friday TEXT,
                pakai_web INTEGER DEFAULT 0, tipe TEXT DEFAULT 'chat'
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS preferensi (
                kunci TEXT PRIMARY KEY, nilai TEXT, terakhir_update TEXT
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS statistik (
                tanggal TEXT PRIMARY KEY,
                jumlah_interaksi INTEGER DEFAULT 0,
                jumlah_browsing INTEGER DEFAULT 0,
                jumlah_deteksi_wajah INTEGER DEFAULT 0,
                jumlah_skill INTEGER DEFAULT 0,
                jumlah_riset INTEGER DEFAULT 0
            )""")
            self.koneksi.commit()
            self._migrasi_schema(cur)
            tampilkan_status(f"Memori termuat: {DB_PATH}", "sukses")
        except Exception as e:
            tampilkan_status(f"Error memori: {e}", "error")

    def _migrasi_schema(self, cur):
        """Tambah kolom baru tanpa merusak data lama (upgrade dari v3)."""
        upgrade = {
            "percakapan": [("tipe", "TEXT DEFAULT 'chat'")],
            "statistik":  [("jumlah_skill", "INTEGER DEFAULT 0"),
                           ("jumlah_riset", "INTEGER DEFAULT 0")],
        }
        for tabel, kolom_list in upgrade.items():
            for kolom, definisi in kolom_list:
                try:
                    cur.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {definisi}")
                    self.koneksi.commit()
                except sqlite3.OperationalError:
                    pass  # Kolom sudah ada — normal saat re-run

    def simpan_percakapan(self, teks_user, teks_friday, pakai_web=False, tipe="chat"):
        try:
            cur = self.koneksi.cursor()
            cur.execute(
                """INSERT INTO percakapan (waktu, teks_user, teks_friday, pakai_web, tipe)
                   VALUES (?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), teks_user, teks_friday,
                 1 if pakai_web else 0, tipe)
            )
            self.koneksi.commit()
            self._prune_otomatis(cur)
        except Exception:
            pass

    def _prune_otomatis(self, cur):
        """
        Hapus percakapan tertua jika melebihi MAX_PERCAKAPAN.
        Terinspirasi OpenJarvis Session Auto-Decay: jaga DB tetap ringan.
        """
        try:
            cur.execute("SELECT COUNT(*) FROM percakapan")
            total = cur.fetchone()[0]
            if total > MAX_PERCAKAPAN:
                hapus = total - int(MAX_PERCAKAPAN * 0.75)
                cur.execute(
                    "DELETE FROM percakapan WHERE id IN "
                    "(SELECT id FROM percakapan ORDER BY id ASC LIMIT ?)",
                    (hapus,)
                )
                self.koneksi.commit()
        except Exception:
            pass

    def ambil_percakapan_terakhir(self, jumlah=5):
        try:
            cur = self.koneksi.cursor()
            cur.execute(
                "SELECT teks_user, teks_friday FROM percakapan ORDER BY id DESC LIMIT ?",
                (jumlah,)
            )
            return list(reversed(cur.fetchall()))
        except Exception:
            return []

    def simpan_preferensi(self, kunci, nilai):
        try:
            if isinstance(nilai, (dict, list)):
                nilai = json.dumps(nilai, ensure_ascii=False)
            cur = self.koneksi.cursor()
            cur.execute(
                """INSERT OR REPLACE INTO preferensi (kunci, nilai, terakhir_update)
                   VALUES (?, ?, ?)""",
                (kunci, str(nilai), datetime.now().isoformat())
            )
            self.koneksi.commit()
        except Exception:
            pass

    def ambil_preferensi(self, kunci, default=None):
        try:
            cur = self.koneksi.cursor()
            cur.execute("SELECT nilai FROM preferensi WHERE kunci = ?", (kunci,))
            row = cur.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return row[0]
            return default
        except Exception:
            return default

    def catat_interaksi(self, tipe="interaksi"):
        try:
            tgl = datetime.now().strftime("%Y-%m-%d")
            kolom_map = {
                "interaksi": "jumlah_interaksi",
                "browsing":  "jumlah_browsing",
                "wajah":     "jumlah_deteksi_wajah",
                "skill":     "jumlah_skill",
                "riset":     "jumlah_riset",
            }
            kolom = kolom_map.get(tipe, "jumlah_interaksi")
            cur = self.koneksi.cursor()
            cur.execute(
                "INSERT INTO statistik (tanggal) VALUES (?) ON CONFLICT(tanggal) DO NOTHING",
                (tgl,)
            )
            cur.execute(
                f"UPDATE statistik SET {kolom} = {kolom} + 1 WHERE tanggal = ?", (tgl,)
            )
            self.koneksi.commit()
        except Exception:
            pass

    def statistik_hari_ini(self):
        try:
            tgl = datetime.now().strftime("%Y-%m-%d")
            cur = self.koneksi.cursor()
            cur.execute("SELECT * FROM statistik WHERE tanggal = ?", (tgl,))
            row = cur.fetchone()
            if row:
                return {
                    "interaksi": row[1], "browsing": row[2], "wajah": row[3],
                    "skill": row[4] if len(row) > 4 else 0,
                    "riset": row[5] if len(row) > 5 else 0,
                }
            return {"interaksi": 0, "browsing": 0, "wajah": 0, "skill": 0, "riset": 0}
        except Exception:
            return {"interaksi": 0, "browsing": 0, "wajah": 0, "skill": 0, "riset": 0}

    def tutup(self):
        if self.koneksi:
            self.koneksi.close()
