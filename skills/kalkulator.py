# ==============================================================
# skills/kalkulator.py — Skill Kalkulator Matematika
# ==============================================================
import ast
import operator as op
import re
from typing import Optional

NAMA = "Kalkulator"
PRIORITAS = 5
TRIGGER_WORDS = [
    "hitung", "berapa hasil", "kalkulator",
    "tambahkan", "kurangi", "kalikan",
    "plus", "minus",
    "persen dari", "akar dari", "akar kuadrat",
    "pangkat",
]

_OPS = {
    ast.Add: op.add, ast.Sub: op.sub,
    ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Mod: op.mod, ast.Pow: op.pow,
    ast.USub: op.neg,
}


def _eval_safe(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_safe(node.left), _eval_safe(node.right))
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_safe(node.operand))
    raise ValueError("Ekspresi tidak valid")


def _normalisasi(teks: str) -> str:
    teks = teks.lower()
    pengganti = [
        ("ditambah", "+"), ("tambahkan", "+"), ("tambah", "+"), ("plus", "+"),
        ("dikurangi", "-"), ("kurangi", "-"), ("minus", "-"),
        ("dikali", "*"), ("kalikan", "*"),
        ("dibagi", "/"),
        ("pangkat", "**"), ("dipangkat", "**"),
    ]
    for kata, simbol in pengganti:
        teks = teks.replace(kata, f" {simbol} ")
    for hapus in ["hitung", "berapa", "hasil", "dari", "adalah", "sama dengan", "kalkulator"]:
        teks = teks.replace(hapus, " ")
    return teks.strip()


def jalankan(teks: str, **ctx) -> Optional[str]:
    # Akar kuadrat
    m = re.search(r'akar\s+(?:kuadrat\s+)?(?:dari\s+)?(\d+(?:\.\d+)?)', teks.lower())
    if m:
        n = float(m.group(1))
        return f"Akar kuadrat dari {n:g} adalah {n**0.5:g}"

    # Persen: "X% dari Y" atau "X persen dari Y"
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:%|persen)\s*dari\s*(\d+(?:\.\d+)?)', teks.lower())
    if m:
        persen, total = float(m.group(1)), float(m.group(2))
        return f"{persen:g}% dari {total:g} adalah {(persen/100)*total:g}"

    # Ekspresi numerik umum
    expr = _normalisasi(teks)
    m = re.search(r'[\d\s\.\+\-\*\/\(\)\*]+', expr)
    if not m:
        return None
    expr_bersih = m.group().strip()
    if not re.search(r'[\+\-\*\/]', expr_bersih):
        return None

    try:
        tree = ast.parse(expr_bersih, mode='eval')
        hasil = _eval_safe(tree.body)
        if isinstance(hasil, float) and hasil == int(hasil):
            hasil = int(hasil)
        return f"Hasilnya adalah {hasil:g}"
    except Exception:
        return None
