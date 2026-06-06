"""Faucet CREDITI da engagement — economia SEPARATA dal NACKL.

L'azione di engagement (quiz/streak/pronostico) accredita:
  • NACKL placeholder  → percorso esistente (RewardClient → InternalRewardProvider)
  • CREDITI (questo)   → qui, su LEDGER INDIPENDENTE (`engagement_credit_grants` +
                         `wallet_transactions`), idempotente per `event_id`.

I due path NON si toccano: niente split-brain (problema noto di Fase 6). Il NACKL
resta sul suo ledger (`nackl_ledger`/`reward_balances`), i Crediti sul wallet.

Curva a SCAGLIONI MARGINALI (forma decisa dall'utente):
  tier1 x3 · tier2 x1.5 · tier3 x0.75 · tier4 x0.2
SCALA / SOGLIE / CAP sotto sono **APPROVATI e APPLICATI** (validati in simulazione,
`tools/economy_report.py`; wirati nei gestori engagement — DECISIONS D6f).
"""
from __future__ import annotations

import datetime as dt
import math

# ───────── CONFIG APPROVATA (DECISIONS D6f, applicata al wiring engagement) ─────────
# "1 unità di engagement" (EP) = la stessa magnitudine reward di Fase 6:
#   quiz: 0.5/risposta corretta (+1.0 perfetto) · streak: 1.0→2.2/giorno · pronostico: 2.5.
# Accumulo realistico utente ingaggiato ≈ 5 EP/giorno.
FAUCET: dict = {
    # Migrazione € (D7): ri-scalato ×100 col fondo (10k→€1M) → stesso peso relativo
    # (cap = 0,05%/giorno del fondo). Soglie/moltiplicatori invariati (sono in EP).
    "base": 25.0,  # € per EP a moltiplicatore x1
    "tiers": [(50, 3.0), (200, 1.5), (500, 0.75), (None, 0.2)],  # (soglia cumulata EP, molt.)
    "daily_cap": 500.0,  # €/giorno/utente (freno anti-farm)
}
PROPOSED_FAUCET = FAUCET  # alias retro-compat


# ───────────────────────── PURE ─────────────────────────
def tiered_credits(cum_before: float, delta_ep: float, *, base: float, tiers: list) -> float:
    """Crediti MARGINALI per aggiungere `delta_ep` EP partendo da `cum_before`,
    attraversando i confini degli scaglioni (rendimenti decrescenti)."""
    remaining = max(0.0, delta_ep)
    pos = cum_before
    credits = 0.0
    for thr, mult in tiers:
        upper = math.inf if thr is None else thr
        if pos >= upper:
            continue
        seg = min(remaining, upper - pos)
        credits += seg * base * mult
        pos += seg
        remaining -= seg
        if remaining <= 0:
            break
    return credits


def _day_key(now: dt.datetime) -> str:
    return now.strftime("%Y-%m-%d")


# ───────────────────────── ACCRUAL (DB, idempotente) ─────────────────────────
async def grant_engagement_credits(
    db, *, user_id, event_id: str, ep: float, now: dt.datetime, config: dict | None = None,
) -> dict:
    """Accredita i Crediti-da-engagement per UN evento. Idempotente su `event_id`.

    Indipendente dal NACKL: scrive solo `wallet`, `wallet_transactions`,
    `engagement_credit_grants`, `engagement_credit_state`.
    """
    cfg = config or FAUCET
    base, tiers, daily_cap = cfg["base"], cfg["tiers"], cfg["daily_cap"]

    existing = await db.engagement_credit_grants.find_one({"event_id": event_id})
    if existing:
        return {"credits": float(existing["credits"]), "idempotent": True}

    state = await db.engagement_credit_state.find_one({"_id": user_id}) or {
        "_id": user_id, "cumulative_ep": 0.0, "day_key": None, "day_credits": 0.0,
    }
    cum_before = float(state.get("cumulative_ep", 0.0))

    # reset cap giornaliero a nuovo giorno
    today = _day_key(now)
    day_credits = float(state.get("day_credits", 0.0)) if state.get("day_key") == today else 0.0

    raw = tiered_credits(cum_before, ep, base=base, tiers=tiers)
    remaining_cap = max(0.0, daily_cap - day_credits)
    credits = min(raw, remaining_cap)

    if credits > 0:
        wallet = await db.user_wallets.find_one({"user_id": user_id})
        balance = float(wallet["balance_eur"]) if wallet else 0.0
        new_balance = balance + credits
        await db.user_wallets.update_one(
            {"user_id": user_id},
            {"$set": {"balance_eur": new_balance, "updated_at": now}}, upsert=True,
        )
        await db.wallet_transactions.insert_one({
            "user_id": user_id, "type": "engagement_reward", "amount": credits,
            "balance_after": new_balance, "description_it": "Bonus Crediti da engagement",
            "created_at": now,
        })

    await db.engagement_credit_grants.insert_one({
        "event_id": event_id, "user_id": user_id, "ep": ep, "credits": credits,
        "cumulative_after": cum_before + ep, "ts": now,
    })
    await db.engagement_credit_state.update_one(
        {"_id": user_id},
        {"$set": {"cumulative_ep": cum_before + ep, "day_key": today,
                  "day_credits": day_credits + credits}},
        upsert=True,
    )
    return {"credits": credits, "idempotent": False, "cumulative_after": cum_before + ep}


async def grant_fixed_credits(
    db, *, user_id, event_id: str, amount: float, now: dt.datetime, daily_cap: float | None = None,
) -> dict:
    """Premio CREDITI a importo FISSO (missioni/sfide) — NON passa per gli scaglioni EP.
    Idempotente per `event_id`, condivide il **cap giornaliero** del faucet (disciplina anti-farm).
    Stesso ledger Crediti del faucet, INDIPENDENTE dal NACKL.
    """
    cap = daily_cap if daily_cap is not None else FAUCET["daily_cap"]
    existing = await db.engagement_credit_grants.find_one({"event_id": event_id})
    if existing:
        return {"credits": float(existing["credits"]), "idempotent": True}

    state = await db.engagement_credit_state.find_one({"_id": user_id}) or {}
    today = _day_key(now)
    day_credits = float(state.get("day_credits", 0.0)) if state.get("day_key") == today else 0.0
    credits = max(0.0, min(float(amount), cap - day_credits))

    if credits > 0:
        wallet = await db.user_wallets.find_one({"user_id": user_id})
        balance = float(wallet["balance_eur"]) if wallet else 0.0
        new_balance = balance + credits
        await db.user_wallets.update_one(
            {"user_id": user_id}, {"$set": {"balance_eur": new_balance, "updated_at": now}}, upsert=True,
        )
        await db.wallet_transactions.insert_one({
            "user_id": user_id, "type": "engagement_reward", "amount": credits,
            "balance_after": new_balance, "description_it": "Premio Crediti (missione/sfida)", "created_at": now,
        })
    await db.engagement_credit_grants.insert_one({
        "event_id": event_id, "user_id": user_id, "ep": 0.0, "credits": credits,
        "cumulative_after": float(state.get("cumulative_ep", 0.0)), "ts": now, "kind": "fixed",
    })
    await db.engagement_credit_state.update_one(
        {"_id": user_id},
        {"$set": {"day_key": today, "day_credits": day_credits + credits},
         "$setOnInsert": {"cumulative_ep": float(state.get("cumulative_ep", 0.0))}},
        upsert=True,
    )
    return {"credits": credits, "idempotent": False}
