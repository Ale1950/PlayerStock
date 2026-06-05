"""Estrattore driver di pricing dal modello del fondatore `Gioco 5.xls` (foglio "Serie 1").

NESSUN valore proprietario è hardcoded qui: lo script LEGGE il file esterno (fuori repo,
DECISIONS.md D0.3) e stampa i dict Python da incollare — verificati — in
`app/config/pricing_constants.py`. Il `test_gioco5_golden.py` rileggerà l'xls (se presente)
per garantire che le costanti committate restino allineate al modello.

Uso (dalla cartella backend/, con xlrd installato):
    python -m tools.extract_gioco5
    python -m tools.extract_gioco5 --xls "C:\\Gioco Calcio\\Gioco 5.xls" --json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_XLS = r"C:\Gioco Calcio\Gioco 5.xls"
SHEET = "Serie 1"

# Offset colonna iniziale per ruolo (3 bande consecutive ciascuno)
ROLE_COLS: dict[str, int] = {"DIF": 1, "CC": 4, "ATT": 7, "POR": 10}

# label (prefisso in col0) -> (chiave driver, etichette banda)
DRIVERS: list[tuple[str, str, tuple[str, str, str]]] = [
    ("minuti gioc",      "MINUTI_GIOCATI",   ("GT_60", "BETWEEN_45_60", "LE_45")),
    ("gol fatti",        "GOL_FATTI",        ("ONE", "GE_2", "ZERO")),
    ("gol subiti",       "GOL_SUBITI",       ("ONE", "GE_2", "ZERO")),
    ("ammonizione",      "AMMONIZIONE",      ("ONE", "TWO", "ZERO")),
    ("espulsione",       "ESPULSIONE",       ("ONE", None, None)),
    ("assist",           "ASSIST",           ("ONE", "GE_2", "ZERO")),
    ("rigori segna",     "RIGORI_SEGNATI",   ("ONE", "TWO", "THREE")),
    ("rigori sbagl",     "RIGORI_SBAGLIATI", ("ONE", "GE_2", "ZERO")),
    ("rigori parat",     "RIGORI_PARATI",    ("ONE", "TWO", "THREE")),
    ("voto solo po",     "VOTO_PORTIERE",    ("LT_6", "B6_7", "GE_8")),
    ("autorete",         "AUTORETE",         ("ONE", "TWO", "GE_3")),
]


def _num(v) -> float | None:
    if isinstance(v, (int, float)) and v != "":
        return round(float(v), 6)
    return None


def extract(xls_path: str) -> dict:
    import xlrd

    book = xlrd.open_workbook(xls_path)
    s = book.sheet_by_name(SHEET)

    # indicizza la riga della label per ogni driver (la riga coeff è quella successiva)
    label_row: dict[str, int] = {}
    clamp_row = None
    for r in range(s.nrows):
        c0 = str(s.cell_value(r, 0)).strip().lower()
        for prefix, key, _ in DRIVERS:
            if c0.startswith(prefix):
                label_row[key] = r
        if str(s.cell_value(r, 0)).strip() == "" and "Max" in [
            str(s.cell_value(r, ROLE_COLS["DIF"])).strip()
        ]:
            clamp_row = r  # riga con 'Max'/'Min'

    drivers: dict[str, dict[str, dict[str, float | None]]] = {}
    for prefix, key, bands in DRIVERS:
        row = label_row[key] + 1
        drivers[key] = {}
        for role, base in ROLE_COLS.items():
            drivers[key][role] = {
                bands[i]: _num(s.cell_value(row, base + i))
                for i in range(3) if bands[i] is not None
            }

    # clamp: riga 'Max | _ | Min' -> riga sotto con i valori
    clamp: dict[str, dict[str, float | None]] = {}
    if clamp_row is not None:
        vrow = clamp_row + 1
        for role, base in ROLE_COLS.items():
            clamp[role] = {
                "up": _num(s.cell_value(vrow, base)),
                "down": _num(s.cell_value(vrow, base + 2)),
            }

    return {"drivers": drivers, "clamp": clamp}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xls", default=DEFAULT_XLS)
    parser.add_argument("--json", action="store_true", help="output JSON invece di repr")
    args = parser.parse_args()

    if not Path(args.xls).exists():
        print(f"[ERR] xls non trovato: {args.xls}")
        return 1

    data = extract(args.xls)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("# ==== DRIVERS (da Gioco 5.xls / Serie 1) ====")
        for key, by_role in data["drivers"].items():
            print(f"{key} = {by_role!r}")
        print("\n# ==== CLAMP ====")
        print(f"RANGE_CLAMP = {data['clamp']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
