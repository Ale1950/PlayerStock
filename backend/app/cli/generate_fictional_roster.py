"""CLI: (ri)genera il file seed statico del roster fittizio Serie A.

Output deterministico (seed fisso) → committato nel repo in
`app/data/serie_a_roster_fittizio.json`. Il `seed_roster` lo legge da lì.

Uso (dalla cartella backend/):
    python -m app.cli.generate_fictional_roster
    python -m app.cli.generate_fictional_roster --seed 12345
"""
from __future__ import annotations

import argparse
import json

from app.data_providers.fictional_roster import (
    DEFAULT_SEED,
    ROSTER_JSON_PATH,
    generate_roster,
)


def main(seed: int) -> int:
    roster = generate_roster(seed)
    ROSTER_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROSTER_JSON_PATH.write_text(
        json.dumps(roster, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Scritti {len(roster)} giocatori fittizi -> {ROSTER_JSON_PATH}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    raise SystemExit(main(args.seed))
