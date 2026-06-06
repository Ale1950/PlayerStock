"""CLI: rinomina IN-PLACE i giocatori il cui nome echeggia un calciatore reale noto.

Guardrail IP (Opzione 2): i pool sono stati ripuliti dai token distintivi dei big
attuali. Questo script trova i nomi pre-esistenti che usano ancora uno di quei token
e li rigenera dal pool ripulito — deterministico per-ID (`source_external_id`),
SENZA ri-seedare: tocca SOLO {internal_full_name, display_*, updated_at}. Ruolo,
nazionalità, squadra, statistiche, valori, prezzi, holdings e storico restano intatti.

Aggiorna anche il file seed statico (`app/data/serie_a_roster_fittizio.json`) sulle
stesse voci, così un futuro re-seed non reintroduce i nomi rimossi.

Uso (dalla cartella backend/):
    python -m app.cli.rename_real_player_echoes          # applica
    python -m app.cli.rename_real_player_echoes --dry    # solo anteprima
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys

from app.core.db import close_db, get_db, init_db
from app.data_providers.anonymization import anonymize_name
from app.data_providers.fictional_roster import (
    BANNED_REAL_PLAYER_TOKENS,
    ROSTER_JSON_PATH,
    regenerate_name,
)
from app.models.common import utc_now

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rename_echoes")


def _echoes_real_player(full_name: str) -> bool:
    return bool(set(full_name.split()) & BANNED_REAL_PLAYER_TOKENS)


async def rename_real_player_echoes(db, *, dry_run: bool = False) -> list[dict]:
    """Rinomina i nomi che echeggiano big reali. Ritorna la lista dei cambi effettuati."""
    athletes = await db.athletes.find({}).to_list(length=100_000)

    # nomi in uso per squadra (per garantire unicità entro la rosa)
    names_by_team: dict[str, set[str]] = {}
    for a in athletes:
        names_by_team.setdefault(a.get("team_fantasy_id"), set()).add(a.get("internal_full_name", ""))

    now = utc_now()
    changes: list[dict] = []
    for a in athletes:
        old = a.get("internal_full_name", "")
        if not _echoes_real_player(old):
            continue
        team = a.get("team_fantasy_id")
        nat = a["nationality_iso3"]
        key = a["source_external_id"]
        # evita collisioni con gli ALTRI nomi della squadra (escludi il proprio)
        used = names_by_team[team] - {old}
        new = regenerate_name(nat, key, used_names=used)
        names_by_team[team].discard(old)
        names_by_team[team].add(new)
        initial, lastname, label = anonymize_name(new)
        changes.append({"ext": key, "nat": nat, "old": old, "new": new, "label": label})
        if not dry_run:
            await db.athletes.update_one(
                {"_id": a["_id"]},
                {"$set": {"internal_full_name": new, "display_initial": initial,
                          "display_lastname": lastname, "display_label": label,
                          "updated_at": now}},
            )
    return changes


def _patch_static_json(changes: list[dict]) -> int:
    """Allinea il file seed: rinomina le stesse voci per external_id. Ritorna i patchati."""
    by_ext = {c["ext"]: c["new"] for c in changes}
    roster = json.loads(ROSTER_JSON_PATH.read_text(encoding="utf-8"))
    n = 0
    for row in roster:
        new = by_ext.get(row.get("external_id"))
        if new:
            row["internal_full_name"] = new
            n += 1
    ROSTER_JSON_PATH.write_text(
        json.dumps(roster, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


async def main(dry_run: bool = False) -> int:
    init_db()
    db = get_db()
    changes = await rename_real_player_echoes(db, dry_run=dry_run)
    for c in changes:
        logger.info("%s [%s]  %-22s -> %-22s (%s)",
                    c["ext"], c["nat"], c["old"], c["new"], c["label"])
    logger.info("%s: %d giocatori%s", "ANTEPRIMA" if dry_run else "Rinominati",
                len(changes), " (dry-run, nessuna scrittura)" if dry_run else "")
    if not dry_run and changes:
        n = _patch_static_json(changes)
        logger.info("Seed JSON allineato: %d voci", n)
    close_db()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(dry_run="--dry" in sys.argv)))
