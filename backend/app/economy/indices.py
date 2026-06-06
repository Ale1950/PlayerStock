"""Indici finanziari (PURI) + bucketing adattivo per le serie equity/prezzo.

Calcolo INTERNO su price_history/equity ricostruita. Niente dati web.
Tutti gli indici sono "best-effort" su serie corte (placeholder MVP): rendimento,
volatilità, max drawdown, beta vs indice di mercato, Sharpe-like.
"""
from __future__ import annotations

import datetime as dt
import statistics
from typing import Sequence


def pct_returns(prices: Sequence[float]) -> list[float]:
    """Rendimenti periodo-su-periodo (semplici)."""
    out: list[float] = []
    for a, b in zip(prices, prices[1:]):
        out.append((b - a) / a if a else 0.0)
    return out


def total_return_pct(prices: Sequence[float]) -> float | None:
    if not prices or prices[0] == 0:
        return None if not prices else 0.0
    return (prices[-1] / prices[0] - 1.0) * 100.0


def volatility(prices: Sequence[float]) -> float:
    """Deviazione standard (popolazione) dei rendimenti, in %."""
    r = pct_returns(prices)
    if len(r) < 1:
        return 0.0
    return statistics.pstdev(r) * 100.0


def max_drawdown(prices: Sequence[float]) -> float:
    """Massima discesa da picco a minimo successivo, in % (≤ 0)."""
    if not prices:
        return 0.0
    peak = prices[0]
    mdd = 0.0
    for p in prices:
        peak = max(peak, p)
        if peak:
            mdd = min(mdd, (p - peak) / peak)
    return mdd * 100.0


def beta(asset: Sequence[float], market: Sequence[float]) -> float:
    """Beta = cov(r_asset, r_market) / var(r_market). 1.0 se asset==market."""
    ra, rm = pct_returns(asset), pct_returns(market)
    n = min(len(ra), len(rm))
    if n < 1:
        return 0.0
    ra, rm = ra[:n], rm[:n]
    mean_m = sum(rm) / n
    var_m = sum((x - mean_m) ** 2 for x in rm) / n
    if var_m == 0:
        return 0.0
    mean_a = sum(ra) / n
    cov = sum((ra[i] - mean_a) * (rm[i] - mean_m) for i in range(n)) / n
    return cov / var_m


def sharpe_like(prices: Sequence[float], rf: float = 0.0) -> float:
    """Rischio/rendimento: media rendimenti / volatilità. 0 se volatilità nulla."""
    r = pct_returns(prices)
    if len(r) < 1:
        return 0.0
    sd = statistics.pstdev(r)
    if sd == 0:
        return 0.0
    return (sum(r) / len(r) - rf) / sd


def win_rate(orders: Sequence[dict]) -> float | None:
    """% di vendite chiuse in profitto (realized_pnl > 0). None se nessuna vendita."""
    sells = [o for o in orders if o.get("side") == "sell"]
    if not sells:
        return None
    wins = sum(1 for o in sells if float(o.get("realized_pnl", 0.0)) > 0)
    return wins / len(sells) * 100.0


def portfolio_indices(prices: Sequence[float], market: Sequence[float] | None = None) -> dict:
    return {
        "return_pct": total_return_pct(prices) or 0.0,
        "volatility": volatility(prices),
        "max_drawdown": max_drawdown(prices),
        "beta": beta(prices, market) if market else 0.0,
        "sharpe": sharpe_like(prices),
    }


# ───────── bucketing adattivo ─────────
def choose_granularity(period_key: str) -> tuple[str, int]:
    """Periodo → (granularità, giorni). Breve→giorni, lungo→settimane."""
    return {
        "1S": ("day", 7),
        "1M": ("day", 31),
        "3M": ("week", 92),
        "all": ("week", 3650),
    }.get(period_key, ("day", 31))


def _key(ts: dt.datetime, gran: str) -> str:
    if gran == "week":
        iso = ts.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    return ts.strftime("%Y-%m-%d")


def bucket_points(points: Sequence[dict], gran: str) -> list[dict]:
    """Aggrega [{ts, value}] in bucket giorno/settimana: vince l'ULTIMO valore del bucket.
    Ritorna una lista ordinata per tempo (un punto per bucket)."""
    buckets: dict[str, dict] = {}
    for p in sorted(points, key=lambda x: x["ts"]):
        buckets[_key(p["ts"], gran)] = {"ts": p["ts"], "value": p["value"]}
    return [buckets[k] for k in sorted(buckets)]
