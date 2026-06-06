"""Sfide settimanali (Engage, Gruppo 3a) — competizione "miglior rendimento" sul periodo.

Standing legato alla classifica (rendimento 1S ricostruito). Si chiude a fine settimana:
premia i top-3 (Crediti via faucet-cap + NACKL placeholder), idempotente per (settimana, utente).
Premi = **APPROVATI** (definitivi, DECISIONS DE.3).
"""
from __future__ import annotations

import datetime as dt

from app.economy.credit_faucet import grant_fixed_credits
from app.economy.indices import choose_granularity, total_return_pct
from app.models.common import utc_now
from app.modules.engagement.reward_client import RewardClient
from app.modules.portfolio.service import anonymize_display_name
from app.modules.stats.analytics import reconstruct_equity

# premio per posizione (top-3). Migrazione € (D7): credits (=€) ×100; NACKL invariato.
PROPOSED_PRIZES: list[dict] = [
    {"credits": 2000, "nackl": 50},
    {"credits": 1000, "nackl": 30},
    {"credits": 500, "nackl": 20},
]


def _week_key(now: dt.datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def _week_end(now: dt.datetime) -> dt.datetime:
    start = (now - dt.timedelta(days=now.isoweekday() - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start + dt.timedelta(days=7)


async def _ranked(db, period: str = "1S") -> list[dict]:
    """Utenti per rendimento sul periodo (con user_id, per il settle)."""
    gran, days = choose_granularity(period)
    since = utc_now() - dt.timedelta(days=days)
    grp = await db.holdings.aggregate([
        {"$match": {"quantity": {"$gt": 0}}},
        {"$group": {"_id": "$user_id"}},
    ]).to_list(length=10000)
    rows: list[dict] = []
    for r in grp:
        vals = [p["equity"] for p in await reconstruct_equity(db, r["_id"], since, gran)]
        rows.append({"user_id": r["_id"], "return_pct": total_return_pct(vals) or 0.0})
    rows.sort(key=lambda x: x["return_pct"], reverse=True)
    return rows


async def weekly_challenge(db, user_id, *, period: str = "1S", limit: int = 10) -> dict:
    now = utc_now()
    ranked = await _ranked(db, period)
    standings: list[dict] = []
    my_rank = None
    for i, row in enumerate(ranked, start=1):
        if row["user_id"] == user_id:
            my_rank = i
        if i <= limit:
            u = await db.users.find_one({"_id": row["user_id"]}, {"name": 1})
            standings.append({
                "rank": i,
                "pseudonym": anonymize_display_name((u or {}).get("name"), is_self=False),
                "return_pct": row["return_pct"],
                "is_self": row["user_id"] == user_id,
                "prize_proposed": PROPOSED_PRIZES[i - 1] if i <= len(PROPOSED_PRIZES) else None,
            })
    return {
        "week_key": _week_key(now),
        "ends_at": _week_end(now),
        "metric": "rendimento settimanale",
        "standings": standings,
        "my_rank": my_rank,
        "total": len(ranked),
    }


async def settle_weekly_challenge(db, week_key: str, *, period: str = "1S") -> dict:
    now = utc_now()
    ranked = await _ranked(db, period)
    winners = 0
    for i, row in enumerate(ranked[:len(PROPOSED_PRIZES)]):
        uid = row["user_id"]
        if await db.challenge_claims.find_one({"week_key": week_key, "user_id": uid}):
            continue  # idempotente per (settimana, utente)
        prize = PROPOSED_PRIZES[i]
        cr = await grant_fixed_credits(db, user_id=uid, event_id=f"challenge:{week_key}:{uid}",
                                       amount=float(prize["credits"]), now=now)
        await RewardClient(db).accrue(user_id=uid, amount=float(prize["nackl"]),
                                      source="engagement_challenge", metadata={"week_key": week_key, "rank": i + 1})
        await db.challenge_claims.insert_one({"week_key": week_key, "user_id": uid, "rank": i + 1,
                                              "credits": cr["credits"], "nackl": float(prize["nackl"]), "ts": now})
        winners += 1
    return {"week_key": week_key, "winners": winners}
