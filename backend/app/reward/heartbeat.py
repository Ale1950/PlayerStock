"""Heartbeat reward: firma HMAC + calcolo accrual placeholder.

⚠️ FARMABILITÀ: l'HMAC con secret lato client è estraibile (decompilazione app) →
un utente può forgiare heartbeat. La protezione vera in MVP è il **cap giornaliero
conservativo** + il legame all'**attività osservata dal server** (più difficile da
falsificare di un beat passivo). Da indurire in Fase 8 prima di qualsiasi valore reale.
"""
from __future__ import annotations

import hashlib
import hmac


def verify_signature(message: str, signature: str, secret: str) -> bool:
    """HMAC-SHA256 in hex, confronto a tempo costante."""
    expected = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, (signature or "").strip().lower())


def compute_accrual(
    *,
    activity_count: int,
    accrued_today: float,
    daily_cap: float,
    base_per_beat: float,
    per_activity: float,
) -> float:
    """NACKL placeholder accreditabile in questo heartbeat.

    raw = base_per_beat (passivo, piccolo) + per_activity × attività osservata (server).
    Limitato dal residuo del cap giornaliero. Mai negativo.
    """
    raw = base_per_beat + per_activity * max(0, activity_count)
    remaining = max(0.0, daily_cap - accrued_today)
    return max(0.0, min(raw, remaining))
