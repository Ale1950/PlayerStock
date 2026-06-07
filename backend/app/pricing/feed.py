"""Performance feed provider — sorgente prestazioni A INNESTO (D10).

Il motore prezzo (round → performance% → prezzo equo) NON sa da dove vengono gli
eventi: li chiede a un `PerformanceFeedProvider`. Oggi l'unica implementazione è il
GENERATORE SINTETICO (mondo fittizio). In futuro, SE autorizzato legalmente, si
innesterà un adattatore 'real' senza toccare il motore — switch via config
(`PERFORMANCE_FEED`). NESSUNA mappa fittizi↔reali né integrazione reale qui.

UNICA FONTE DI VERITÀ per gli eventi del round: lo stesso `RoundResult` (a) muove il
prezzo (via `performance_pct`) e (b) si somma nelle statistiche stagionali MOSTRATE.
Così non c'è contraddizione tra le stat a schermo e ciò che muove il prezzo.
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.pricing.performance import MatchPerformance

_GOL_PROB = {"ATT": 0.45, "CC": 0.22, "DIF": 0.10, "POR": 0.0}
_ASSIST_PROB = {"ATT": 0.30, "CC": 0.30, "DIF": 0.15, "POR": 0.02}


@dataclass
class RoundResult:
    perf: MatchPerformance   # input oggettivo per il pricing (performance_pct)
    stats: dict              # forma display: presenze/minuti/gol/assist/parate/ammonizioni/voto


def _unit(key: str) -> float:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big") / 2**64


class PerformanceFeedProvider(ABC):
    """Restituisce gli eventi di UN round per UN atleta."""
    name: str = "base"

    @abstractmethod
    def round_performance(self, athlete: dict, round_idx: int) -> RoundResult: ...


class SyntheticPerformanceProvider(PerformanceFeedProvider):
    """Generatore sintetico deterministico: coerente con `score_performance` + ruolo +
    minutaggio, con varianza (forma/fortuna). Mondo fittizio (DECISIONS Fase 2b / D10)."""
    name = "synthetic"

    def round_performance(self, athlete: dict, round_idx: int) -> RoundResult:
        role = athlete["role"]
        score = max(0.5, min(2.0, float(athlete.get("score_performance", 1.0))))
        minutaggio = float(athlete.get("minutaggio_pct", 0.7))
        key = str(athlete.get("source_external_id") or athlete.get("_id"))
        base = f"feed:{key}:{round_idx}:"

        def u(tag: str) -> float:
            return _unit(base + tag)

        # gioca il round?
        if u("plays") > minutaggio + 0.10:
            perf = MatchPerformance(minuti=int(u("bench") * 25))
            stats = {"presenze": 0, "minuti": perf.minuti, "gol": 0, "assist": 0,
                     "parate": (0 if role == "POR" else None), "ammonizioni": 0, "voto": None}
            return RoundResult(perf=perf, stats=stats)

        minuti = 90 if u("full") < 0.7 else 60 + int(u("part") * 29)
        gol_p = min(0.95, _GOL_PROB[role] * score)
        assist_p = min(0.95, _ASSIST_PROB[role] * score)
        gol = (1 if u("g1") < gol_p else 0) + (1 if u("g2") < gol_p * 0.25 else 0)
        assist = 1 if u("a") < assist_p else 0
        amm = (1 if u("y1") < 0.16 else 0) + (1 if u("y2") < 0.02 else 0)
        espulso = u("red") < 0.01
        gol_subiti = 0 if u("cs") < 0.4 else (1 if u("c1") < 0.7 else 2)
        rigori_parati = 1 if role == "POR" and u("rp") < 0.06 else 0
        rigori_segnati = 1 if role in ("ATT", "CC") and u("ps") < 0.05 else 0

        parate = None
        voto = None
        if role == "POR":
            pp = min(0.90, 0.5 * score)
            parate = sum(1 for k in ("p1", "p2", "p3", "p4", "p5") if u(k) < pp)
            voto = round(7.5 - gol_subiti * 0.7 + parate * 0.15 + rigori_parati * 0.6 + u("v") * 0.5, 1)

        perf = MatchPerformance(
            minuti=minuti, gol_fatti=gol, gol_subiti=gol_subiti, ammonizioni=amm,
            espulso=espulso, assist=assist, rigori_segnati=rigori_segnati,
            rigori_parati=rigori_parati, voto=voto,
        )
        stats = {"presenze": 1, "minuti": minuti, "gol": gol, "assist": assist,
                 "parate": parate, "ammonizioni": amm, "voto": voto}
        return RoundResult(perf=perf, stats=stats)


def get_performance_feed(settings=None) -> PerformanceFeedProvider:
    """Seleziona il provider da `PERFORMANCE_FEED`. Oggi: solo 'synthetic'.

    In futuro (post-legale) qui si innesterà un 'real' adapter — il motore prezzo
    non cambia. Sconosciuto → fallback sintetico (mai dati reali per sbaglio).
    """
    name = getattr(settings, "PERFORMANCE_FEED", "synthetic") if settings else "synthetic"
    # if name == "real": return RealDataPerformanceProvider(...)  # SOLO se autorizzato (D10)
    return SyntheticPerformanceProvider()
