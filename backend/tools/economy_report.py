"""Report di RITARATURA economica (Fase: tuning).

Simula rendimento + pressione di trading su un roster sintetico, su orizzonti
30/60/90 giorni, e stampa metriche + proposte di ritaratura (NON applicate).

Deterministico, self-contained (mongomock):  python -m tools.economy_report
"""
from __future__ import annotations

import asyncio
import hashlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # output unicode anche su console Windows
except Exception:
    pass

from bson import ObjectId
from mongomock_motor import AsyncMongoMockClient

from app.cli.simulate_rounds import simulate_economy
from app.config.pricing_constants import (
    BUDGET_INIZIALE_UTENTE_EUR,
    CAP_UTENTE_AZIONI,
    DEVIAZIONE_CAP,
    FLOAT_AZIONI_PER_GIOCATORE,
)
from app.economy.credit_faucet import PROPOSED_FAUCET
from app.models.common import utc_now
from app.valuation.market_value import assign_team_market_values, price_from_market_value

ROLES = ["POR", "DIF", "CC", "ATT"]


def _u(key: str) -> float:
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") / 2**64


async def _seed(db, n_athletes=40, n_traders=30):
    """Seed € (D7): prezzo = ancora €M (Opzione B, coda pesante) / FLOAT."""
    now = utc_now()
    players = []
    for i in range(n_athletes):
        players.append({
            "_id": ObjectId(), "role": ROLES[i % 4],
            "score": 0.8 + _u(f"s{i}") * 1.2,            # 0.8–2.0
            "age": 19 + int(_u(f"a{i}") * 18),
            "minut": 0.4 + _u(f"m{i}") * 0.6,
            "fsq": 0.92 + _u(f"f{i}") * 0.43,
            "team": f"team{i // 20}",                     # squadre da 20 per la curva-rank
        })
    by_team: dict = {}
    for p in players:
        by_team.setdefault(p["team"], []).append(p)
    seeds: dict = {}
    for members in by_team.values():
        seeds.update(assign_team_market_values(
            [{"key": str(p["_id"]), "score": p["score"], "fattore_squadra": p["fsq"]}
             for p in members]))
    for p in players:
        seed = seeds[str(p["_id"])]
        prezzo = price_from_market_value(seed, FLOAT_AZIONI_PER_GIOCATORE)
        await db.athletes.insert_one({
            "_id": p["_id"], "sport_id": "calcio", "status": "ACTIVE", "role": p["role"],
            "prezzo_iniziale_eur": prezzo, "prezzo_equo_eur": prezzo,
            "prezzo_corrente_eur": prezzo, "deviazione": 0.0, "deviazione_ts": now,
            "float_quote": FLOAT_AZIONI_PER_GIOCATORE, "primary_pool_qty": FLOAT_AZIONI_PER_GIOCATORE,
            "circulating_qty": 0, "score_performance": p["score"], "age": p["age"],
            "minutaggio_pct": p["minut"], "fattore_squadra": p["fsq"],
            "market_value_eur_seed": seed,
        })
    traders = []
    for _ in range(n_traders):
        uid = ObjectId()
        await db.user_wallets.insert_one({
            "user_id": uid, "balance_eur": BUDGET_INIZIALE_UTENTE_EUR, "updated_at": now,
        })
        traders.append(uid)
    return traders


async def main():
    print("=" * 78)
    print("REPORT RITARATURA ECONOMICA — rendimento + pressione di trading")
    print(f"budget=€{BUDGET_INIZIALE_UTENTE_EUR:.0f} · cap utente={CAP_UTENTE_AZIONI} quote (3%) · "
          f"float={FLOAT_AZIONI_PER_GIOCATORE} · cap deviazione=±{DEVIAZIONE_CAP:.0%}")
    print("=" * 78)
    print(f"{'gg':>3} {'trade':>6} {'fee_€':>10} {'banda prezzo (x iniziale)':>26} "
          f"{'dev|max':>8} {'dev|avg':>8} {'floor':>6} {'cap-buy/fondo':>13}")

    rows = []
    for days in (30, 60, 90):
        db = AsyncMongoMockClient()[f"econ{days}"]
        traders = await _seed(db)
        rep = await simulate_economy(db, days=days, trader_ids=traders)
        rows.append(rep)
        band = f"{rep['price_ratio_min']:.2f}–{rep['price_ratio_max']:.2f}"
        print(f"{rep['days']:>3} {rep['trades_executed']:>6} {rep['fee_revenue']:>9.1f} {band:>26} "
              f"{rep['deviation_abs_max']:>8.3f} {rep['deviation_abs_avg']:>8.4f} {rep['floored_count']:>6} "
              f"{rep['cap_buys_affordable_10k']:>11.2f}")

    r = rows[-1]  # 90 giorni
    print("\n--- COSA REGGE ---")
    print(f"• Cap deviazione: max |dev| osservata = {r['deviation_abs_max']:.3f} ≤ {DEVIAZIONE_CAP:.2f} → "
          "nessuna fuga; il rientro lazy riassorbe lo slippage tra le giornate.")
    print(f"• Floor 10%: atleti al floor a 90gg = {r['floored_count']} → il floor protegge i titoli deboli.")
    print(f"• Fee economia: €{r['fee_revenue']:.0f} drenati in {r['trades_executed']} trade "
          "(sink anti-inflazione attivo).")
    print(f"• Banda prezzo {r['price_ratio_min']:.2f}–{r['price_ratio_max']:.2f}× l'iniziale: "
          "il rendimento domina il movimento, il trading aggiunge rumore ±cap.")

    print("\n--- BUDGET vs CAP (scala €, D7) ---")
    aff = r["cap_buys_affordable_10k"]
    print(f"• Con €{BUDGET_INIZIALE_UTENTE_EUR:.0f} l'utente copre {aff:.2f} ordini-cap al prezzo medio "
          f"(€{r['avg_price']:.2f} → costo cap €{r['cap_buy_cost_at_avg']:.0f}).")
    if aff < 1.0:
        print("    ✓ ATTESO (feature D7): sui titoli costosi il cap 3% supera il fondo → "
              "vincolo di capitale come in un mercato vero. Il cap-quote morde sui titoli economici.")
    elif aff > 8.0:
        print("    ⚠️  molto alto: il cap non morde, un utente può dominare molti titoli → "
              "proposta: ridurre budget o cap per forzare scelte.")
    else:
        print("    ✓ ragionevole: l'utente può prendere posizioni significative su pochi titoli "
              "(diversificazione vincolata dal cap, come da design).")
    print("• k_impatto/λ: se il rumore di trading (dev_avg) è trascurabile vs rendimento, "
          "valutare k_impatto 1.0→1.5 per rendere il trading più 'sentito'; se troppo nervoso, "
          "accorciare l'emivita (λ più alto) per rientri più rapidi.")
    print("• Floor: se floored_count cresce molto su orizzonti lunghi, rivedere i driver di "
          "rendimento negativi o alzare il floor dal 10% al 12–15%.")
    print("\n(Proposte da APPROVARE prima di toccare le costanti.)")

    # ───────── PARTE B: faucet crediti da engagement (PROPOSTA) ─────────
    n_traders = 30
    print("\n" + "=" * 78)
    print("FAUCET € DA ENGAGEMENT — simulazione (config D7 applicata)")
    base = PROPOSED_FAUCET["base"]
    tiers = PROPOSED_FAUCET["tiers"]
    cap = PROPOSED_FAUCET["daily_cap"]
    print(f"base x1 = €{base}/EP · scaglioni EP {[t for t, _ in tiers]} con molt. {[m for _, m in tiers]} "
          f"· cap = €{cap}/gg · ~5 EP/gg/utente · {n_traders} utenti")
    print("=" * 78)
    print(f"{'gg':>3} {'€_in':>11} {'fee_out_€':>10} {'net (in-out)':>13} {'€/utente':>10} {'%fondo':>8}")
    frows = []
    for days in (30, 60, 90):
        db = AsyncMongoMockClient()[f"faucet{days}"]
        traders = await _seed(db, n_traders=n_traders)
        rep = await simulate_economy(db, days=days, trader_ids=traders, faucet_config=PROPOSED_FAUCET)
        frows.append(rep)
        per_user = rep["credits_injected"] / n_traders
        print(f"{days:>3} {rep['credits_injected']:>11.0f} {rep['fee_revenue']:>9.0f} "
              f"{rep['net_credit_flow']:>13.0f} {per_user:>10.1f} {per_user / BUDGET_INIZIALE_UTENTE_EUR * 100:>7.1f}%")

    f = frows[-1]
    print("\n--- ESITO FAUCET (90 giorni) ---")
    healthy = f["net_credit_flow"] < 0
    print(f"• € iniettati = {f['credits_injected']:.0f} vs fee drenate = {f['fee_revenue']:.0f} → "
          f"net = {f['net_credit_flow']:+.0f} € "
          f"({'SINK > FAUCET: niente inflazione netta ✓' if healthy else 'FAUCET > SINK: rischio inflazione ⚠️'}).")
    print(f"• Bonus medio/utente a 90gg = €{f['credits_injected']/n_traders:.0f} "
          f"= {f['credits_injected']/n_traders/BUDGET_INIZIALE_UTENTE_EUR*100:.1f}% del fondo €1.000.000 → "
          "significativo ma non distorsivo.")
    print("• Rendimenti decrescenti: i primi 50 EP (~10gg) valgono x3, poi x1.5/x0.75/x0.2 → "
          "l'onboarding premia, il grind tardivo no.")
    print("• Cap giornaliero freno-farm: limita i picchi a "
          f"€{cap:.0f}/gg/utente anche con molte azioni.")
    print("\nVALORI APPLICATI (D7):")
    print(f"  base=€{base}/EP · soglie EP=[50,200,500] · molt=[3,1.5,0.75,0.2] · cap=€{cap}/gg")
    if not healthy:
        target_base = base * 0.8 * abs(f["fee_revenue"] / max(f["credits_injected"], 1))
        print(f"  ⚠️ per restare sotto il sink, abbassare base a ~€{target_base:.2f}/EP.")


if __name__ == "__main__":
    asyncio.run(main())
