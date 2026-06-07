"""Missioni / obiettivi (Engage, Gruppo 3a) — progressione + premio alla completazione.

Premio SOLO in € via `grant_fixed_credits` (dentro il cap del faucet). NESSUN NACKL:
il gioco non assegna NACKL (solo mining). Idempotenti per (utente, missione).

VALORI premio cappati dal faucet (€500/gg condiviso) → non scompaginano l'economia tarata.
"""
from __future__ import annotations

import datetime as dt

from app.economy.credit_faucet import grant_fixed_credits
from app.models.common import utc_now

# id → (titolo, descrizione, target, reward {credits=€}). SOLO €: il gioco non dà NACKL.
MISSIONS: list[dict] = [
    {"id": "first_buy", "title": "Primo acquisto", "desc": "Compra il tuo 1° giocatore", "target": 1,
     "reward": {"credits": 500}},
    {"id": "diversify_roles", "title": "Diversifica", "desc": "Possiedi giocatori di 3 ruoli diversi", "target": 3,
     "reward": {"credits": 800}},
    {"id": "hold_7d", "title": "Mani ferme", "desc": "Tieni una posizione per 7 giorni", "target": 1,
     "reward": {"credits": 800}},
    {"id": "reach_15k", "title": "Patrimonio 1,5M", "desc": "Raggiungi €1.500.000 di patrimonio", "target": 1_500_000,
     "reward": {"credits": 1500}},
    {"id": "predict_3", "title": "Oracolo", "desc": "Azzecca 3 pronostici", "target": 3,
     "reward": {"credits": 1000}},
]
_BY_ID = {m["id"]: m for m in MISSIONS}


def _naive(d: dt.datetime) -> dt.datetime:
    return d.astimezone(dt.timezone.utc).replace(tzinfo=None) if d.tzinfo else d


async def _progress(db, user_id) -> dict[str, float]:
    holdings = await db.holdings.find({"user_id": user_id, "quantity": {"$gt": 0}}).to_list(length=1000)
    cutoff = _naive(utc_now() - dt.timedelta(days=7))

    roles, held_7d = set(), 0
    equity_pos = 0.0
    for h in holdings:
        a = await db.athletes.find_one({"_id": h["athlete_id"]}, {"role": 1, "prezzo_corrente_eur": 1})
        if a:
            roles.add(a.get("role"))
            equity_pos += h["quantity"] * float(a.get("prezzo_corrente_eur", 0.0))
        for lot in h.get("lots", []):
            ts = lot.get("acquired_at")
            if ts and _naive(ts) <= cutoff:
                held_7d = 1
    w = await db.user_wallets.find_one({"user_id": user_id})
    cash = float(w["balance_eur"]) if w else 0.0
    won = await db.predictions.count_documents({"user_id": user_id, "status": "won"})
    return {
        "first_buy": 1 if holdings else 0,
        "diversify_roles": len(roles),
        "hold_7d": held_7d,
        "reach_15k": cash + equity_pos,
        "predict_3": won,
    }


async def evaluate_missions(db, user_id) -> list[dict]:
    prog = await _progress(db, user_id)
    claimed = {c["mission_id"] for c in await db.mission_claims.find({"user_id": user_id}).to_list(length=100)}
    out: list[dict] = []
    for m in MISSIONS:
        p = prog.get(m["id"], 0)
        out.append({
            "id": m["id"], "title": m["title"], "description": m["desc"],
            "progress": p, "target": m["target"],
            "completed": p >= m["target"],
            "claimed": m["id"] in claimed,
            "reward_proposed": m["reward"],
        })
    return out


async def claim_mission(db, user_id, mission_id: str) -> dict:
    m = _BY_ID.get(mission_id)
    if not m:
        return {"claimed": False, "error": "mission.unknown"}
    if await db.mission_claims.find_one({"user_id": user_id, "mission_id": mission_id}):
        return {"claimed": False, "already": True}
    prog = await _progress(db, user_id)
    if prog.get(mission_id, 0) < m["target"]:
        return {"claimed": False, "incomplete": True}

    now = utc_now()
    # SOLO €: il riscatto missione NON accredita NACKL (NACKL = solo mining).
    cr = await grant_fixed_credits(db, user_id=user_id, event_id=f"mission:{user_id}:{mission_id}",
                                   amount=float(m["reward"]["credits"]), now=now)
    await db.mission_claims.insert_one({"user_id": user_id, "mission_id": mission_id,
                                        "credits": cr["credits"], "ts": now})
    return {"claimed": True, "credits": cr["credits"]}
