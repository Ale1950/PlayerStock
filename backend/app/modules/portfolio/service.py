"""Portfolio service: cost-basis FIFO, valore corrente, P&L per posizione,
aggregazione totali, leaderboard, storico prezzi (sparkline).

Modulo additivo Fase 4. Non scrive sul DB se non per audit log: legge da
`holdings`, `user_wallets`, `athletes`, `price_history` e calcola in memoria.

Cost basis: il modulo Fase 3 conserva i `lots` residui (post-FIFO sulle
vendite). Quindi il costo della posizione corrente è la somma pesata dei
lotti residui — questa è esattamente la base "FIFO" del capital allocato.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Sequence


# ───────────────────────── PURE FUNCTIONS (testabili senza DB) ─────────────────────────

def cost_basis_from_lots(lots: Sequence[dict]) -> float:
    """Costo totale della posizione: Σ(qty × price) sui lotti residui FIFO.

    `lots` è una lista di dict {qty, price, acquired_at} (campi obbligatori: qty, price).
    Restituisce 0.0 se la lista è vuota.
    """
    total = 0.0
    for lot in lots:
        qty = lot.get("qty", 0) or 0
        price = lot.get("price", 0.0) or 0.0
        total += qty * price
    return total


def avg_cost_per_share(lots: Sequence[dict]) -> float:
    """Costo medio per quota (Σ(qty×price) / Σ(qty)). 0 se nessun lotto."""
    total_qty = sum((lot.get("qty", 0) or 0) for lot in lots)
    if total_qty <= 0:
        return 0.0
    return cost_basis_from_lots(lots) / total_qty


def position_pnl(*, qty: int, lots: Sequence[dict], current_price: float) -> dict:
    """Calcola P&L assoluto e % per una singola posizione.

    Restituisce:
        {
          "quantity": qty,
          "avg_cost": float,
          "cost_basis": float,        # Σ(qty×price) sui lotti
          "current_price": float,
          "current_value": float,     # qty × current_price
          "pnl_abs": float,           # current_value - cost_basis
          "pnl_pct": float | None,    # None se cost_basis=0 (evita divisione per 0)
        }
    """
    if qty < 0:
        qty = 0
    cost_basis = cost_basis_from_lots(lots)
    current_value = qty * (current_price or 0.0)
    avg_cost = avg_cost_per_share(lots)
    pnl_abs = current_value - cost_basis
    pnl_pct: float | None
    if cost_basis > 0:
        pnl_pct = (pnl_abs / cost_basis) * 100.0
    else:
        pnl_pct = None
    return {
        "quantity": qty,
        "avg_cost": avg_cost,
        "cost_basis": cost_basis,
        "current_price": current_price or 0.0,
        "current_value": current_value,
        "pnl_abs": pnl_abs,
        "pnl_pct": pnl_pct,
    }


def aggregate_totals(*, balance_eur: float, positions: Iterable[dict]) -> dict:
    """Aggrega i totali del portafoglio.

    `positions` è un iterabile di dict con almeno `current_value`, `cost_basis`.
    Restituisce:
        {
          "cash_eur": float,
          "positions_value": float,       # Σ current_value
          "positions_cost_basis": float,  # Σ cost_basis
          "total_equity": float,          # cash + positions_value
          "total_pnl_abs": float,         # positions_value - positions_cost_basis
          "total_pnl_pct": float | None,
          "positions_count": int,
        }
    """
    positions_list = list(positions)
    positions_value = sum(p.get("current_value", 0.0) for p in positions_list)
    cost_basis = sum(p.get("cost_basis", 0.0) for p in positions_list)
    total_pnl_abs = positions_value - cost_basis
    if cost_basis > 0:
        total_pnl_pct = (total_pnl_abs / cost_basis) * 100.0
    else:
        total_pnl_pct = None
    return {
        "cash_eur": float(balance_eur or 0.0),
        "positions_value": positions_value,
        "positions_cost_basis": cost_basis,
        "total_equity": float(balance_eur or 0.0) + positions_value,
        "total_pnl_abs": total_pnl_abs,
        "total_pnl_pct": total_pnl_pct,
        "positions_count": sum(1 for p in positions_list if p.get("quantity", 0) > 0),
    }


def anonymize_display_name(name: str | None, *, is_self: bool = False) -> str:
    """Privacy leaderboard: il proprio nome è mostrato pieno; gli altri sono
    abbreviati come "PrimoNome C." (iniziale del cognome).

    Esempi (is_self=False):
      "Mario Rossi"           → "Mario R."
      "Alessandro Della Valle" → "Alessandro D."
      "Pelé"                  → "Pelé"
      ""                      → "Player"
    """
    if not name:
        return "Player"
    n = name.strip()
    if is_self:
        return n
    tokens = n.split()
    if len(tokens) == 1:
        return tokens[0]
    return f"{tokens[0]} {tokens[-1][0].upper()}."


# ───────────────────────── DB-BACKED FUNCTIONS ─────────────────────────

async def build_portfolio_response(db, user_id) -> dict:
    """Costruisce la risposta GET /api/portfolio per un utente.

    Anonimizzazione Livello 2 sempre: NON include `internal_full_name` mai.
    """
    wallet = await db.user_wallets.find_one({"user_id": user_id})
    balance = float(wallet["balance_eur"]) if wallet else 0.0

    holdings = await db.holdings.find({
        "user_id": user_id,
        "quantity": {"$gt": 0},
    }).to_list(length=1000)

    positions: list[dict] = []
    for h in holdings:
        athlete = await db.athletes.find_one({"_id": h["athlete_id"]})
        if not athlete:
            continue
        current_price = float(athlete.get("prezzo_corrente_eur", 0.0))
        pnl = position_pnl(
            qty=int(h.get("quantity", 0)),
            lots=h.get("lots", []),
            current_price=current_price,
        )
        # Squadra fantasy denormalizzata (NON è sul doc atleta) → lookup
        team = None
        if athlete.get("team_fantasy_id") is not None:
            team = await db.teams_fantasy.find_one({"_id": athlete["team_fantasy_id"]})
        team = team or {}
        positions.append({
            "athlete_id": str(h["athlete_id"]),
            "display_label": athlete.get("display_label"),
            "display_initial": athlete.get("display_initial"),
            "display_lastname": athlete.get("display_lastname"),
            "role": athlete.get("role"),
            "nationality_iso3": athlete.get("nationality_iso3"),
            "team_fantasy_name": team.get("fantasy_name"),
            "team_color_primary": team.get("color_primary"),
            "prezzo_iniziale_eur": float(athlete.get("prezzo_iniziale_eur", 0.0)),
            "status": athlete.get("status", "ACTIVE"),
            **pnl,
        })

    positions.sort(key=lambda p: p["current_value"], reverse=True)
    totals = aggregate_totals(balance_eur=balance, positions=positions)

    return {"totals": totals, "positions": positions}


async def build_wallet_response(db, user_id, *, recent_limit: int = 20) -> dict:
    """Risposta unificata GET /api/wallet: saldo + ultime N transazioni."""
    wallet = await db.user_wallets.find_one({"user_id": user_id})
    balance = float(wallet["balance_eur"]) if wallet else 0.0
    updated_at = wallet["updated_at"] if wallet else None
    cursor = db.wallet_transactions.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(recent_limit)
    raw_items = await cursor.to_list(length=recent_limit)
    items: list[dict] = []
    for t in raw_items:
        items.append({
            "id": str(t["_id"]),
            "type": t.get("type"),
            "amount": float(t.get("amount", 0.0)),
            "balance_after": float(t.get("balance_after", 0.0)),
            "description_it": t.get("description_it", ""),
            "created_at": t.get("created_at"),
        })
    return {
        "balance_eur": balance,
        "updated_at": updated_at,
        "recent_transactions": items,
        "recent_limit": recent_limit,
    }


async def build_leaderboard(db, current_user_id, *, limit: int = 50) -> dict:
    """Top utenti per equity totale (cassa + valore titoli al prezzo corrente).

    Privacy: nome anonimizzato per chi NON è l'utente corrente.
    Mai esposti: email, user_id (sostituito da rank), holdings dettagliate.
    """
    # 1. Mappa prezzo corrente per atleta (una volta sola)
    athletes_cur = await db.athletes.find(
        {}, {"_id": 1, "prezzo_corrente_eur": 1, "status": 1}
    ).to_list(length=10000)
    price_by_aid: dict = {a["_id"]: float(a.get("prezzo_corrente_eur", 0.0))
                          for a in athletes_cur if a.get("status") == "ACTIVE"}

    # 2. Aggrega per user: somma qty*price corrente
    pipeline_h = [
        {"$match": {"quantity": {"$gt": 0}}},
        {"$group": {"_id": {"user_id": "$user_id", "athlete_id": "$athlete_id"},
                    "qty": {"$sum": "$quantity"}}},
    ]
    holdings_grouped = await db.holdings.aggregate(pipeline_h).to_list(length=100000)
    positions_value_by_user: dict = {}
    for row in holdings_grouped:
        uid = row["_id"]["user_id"]
        aid = row["_id"]["athlete_id"]
        cur = price_by_aid.get(aid, 0.0)
        positions_value_by_user[uid] = positions_value_by_user.get(uid, 0.0) + (row["qty"] * cur)

    # 3. Carica utenti attivi
    users = await db.users.find(
        {"status": "active"},
        {"_id": 1, "name": 1, "picture": 1, "created_at": 1},
    ).to_list(length=10000)

    # 4. Carica saldi
    wallets = await db.user_wallets.find(
        {}, {"user_id": 1, "balance_eur": 1, "_id": 0}
    ).to_list(length=10000)
    balance_by_user = {w["user_id"]: float(w.get("balance_eur", 0.0)) for w in wallets}

    # 5. Costruisce la lista
    rows: list[dict] = []
    for u in users:
        uid = u["_id"]
        cash = balance_by_user.get(uid, 0.0)
        pos_val = positions_value_by_user.get(uid, 0.0)
        equity = cash + pos_val
        rows.append({"_uid": uid, "name": u.get("name", ""), "cash": cash,
                     "positions_value": pos_val, "total_equity": equity})

    rows.sort(key=lambda r: r["total_equity"], reverse=True)
    items: list[dict] = []
    for rank, r in enumerate(rows[:limit], start=1):
        is_self = (r["_uid"] == current_user_id)
        items.append({
            "rank": rank,
            "display_name": anonymize_display_name(r["name"], is_self=is_self),
            "is_self": is_self,
            "total_equity": round(r["total_equity"], 4),
            "positions_value": round(r["positions_value"], 4),
            "cash_eur": round(r["cash"], 4),
        })

    # 6. Self rank (se l'utente è fuori dal top-N)
    self_rank = next((r["rank"] for r in items if r["is_self"]), None)
    if self_rank is None:
        for rank, r in enumerate(rows, start=1):
            if r["_uid"] == current_user_id:
                self_rank = rank
                self_data = {
                    "rank": rank,
                    "display_name": anonymize_display_name(r["name"], is_self=True),
                    "is_self": True,
                    "total_equity": round(r["total_equity"], 4),
                    "positions_value": round(r["positions_value"], 4),
                    "cash_eur": round(r["cash"], 4),
                }
                break
        else:
            self_data = None
    else:
        self_data = next((it for it in items if it["is_self"]), None)

    return {"items": items, "self": self_data, "total_users": len(rows)}


async def fetch_price_history(db, athlete_id, *, limit: int = 30) -> list[dict]:
    """Punti per sparkline: ultimi `limit` campioni di `price_history`.

    Restituisce lista di {ts, price} ordinata crescente per timestamp.
    Se la collection è vuota, restituisce []. NIENTE leak di campi interni.
    """
    # NB: nel repo canonico price_history usa il campo `prezzo` (Fase 2b/3);
    # manteniamo fallback su `price` per compatibilità.
    cursor = db.price_history.find(
        {"athlete_id": athlete_id},
        {"_id": 0, "ts": 1, "prezzo": 1, "price": 1},
    ).sort("ts", -1).limit(limit)
    raw = await cursor.to_list(length=limit)
    raw.reverse()  # ordine crescente per disegnare la sparkline
    return [{"ts": p["ts"], "price": float(p.get("prezzo", p.get("price", 0.0)))} for p in raw]
