"""RED→GREEN: funzioni pure reward — accrual da attività, firma HMAC, public key.

NB: l'accrual interno è un PLACEHOLDER dev/MVP, NON NACKL reale (emesso dal protocollo).
"""
from __future__ import annotations

import hashlib
import hmac

import pytest

from app.core.errors import APIError
from app.reward.heartbeat import compute_accrual, verify_signature
from app.reward.wallet import validate_mining_public_key


# ───────── accrual (placeholder) legato all'attività osservata ─────────
def test_accrual_scales_with_observed_activity():
    # base piccola (heartbeat passivo, farmabile) + bonus per attività reale
    a0 = compute_accrual(activity_count=0, accrued_today=0.0, daily_cap=100.0,
                         base_per_beat=0.1, per_activity=1.0)
    a5 = compute_accrual(activity_count=5, accrued_today=0.0, daily_cap=100.0,
                         base_per_beat=0.1, per_activity=1.0)
    assert a0 == pytest.approx(0.1)
    assert a5 == pytest.approx(5.1)
    assert a5 > a0


def test_accrual_capped_by_daily_remaining():
    a = compute_accrual(activity_count=50, accrued_today=98.0, daily_cap=100.0,
                        base_per_beat=0.1, per_activity=1.0)
    assert a == pytest.approx(2.0)  # solo il residuo del cap


def test_accrual_zero_when_cap_reached():
    a = compute_accrual(activity_count=10, accrued_today=100.0, daily_cap=100.0,
                        base_per_beat=0.1, per_activity=1.0)
    assert a == 0.0


# ───────── firma heartbeat HMAC ─────────
def test_verify_signature_valid():
    secret = "s3cr3t"
    msg = "user123:nonceABC:1234567890"
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    assert verify_signature(msg, sig, secret) is True


def test_verify_signature_invalid():
    assert verify_signature("msg", "deadbeef", "s3cr3t") is False


# ───────── wallet: SOLO mining public key, mai seed/spesa ─────────
def test_accepts_valid_public_key_hex():
    key = "a" * 64
    assert validate_mining_public_key(key) == key
    assert validate_mining_public_key("0x" + "B" * 64) == "b" * 64  # normalizza


def test_rejects_seed_phrase():
    mnemonic = "legal winner thank year wave sausage worth useful legal winner thank yellow"
    with pytest.raises(APIError):
        validate_mining_public_key(mnemonic)


def test_rejects_wrong_length_or_non_hex():
    with pytest.raises(APIError):
        validate_mining_public_key("abc123")          # troppo corta
    with pytest.raises(APIError):
        validate_mining_public_key("z" * 64)          # non hex
    with pytest.raises(APIError):
        validate_mining_public_key("")                # vuota
