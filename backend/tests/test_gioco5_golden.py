"""Golden test: le costanti driver committate restano allineate a `Gioco 5.xls`.

Salta se l'xls non è presente (es. CI) — è un guard locale anti-drift, non un test
funzionale. L'xls resta FUORI dal repo (DECISIONS.md D0.3); qui lo si rilegge solo
se disponibile sul disco dello sviluppatore.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.config.pricing_constants import DRIVERS, RANGE_CLAMP

XLS_PATH = Path(r"C:\Gioco Calcio\Gioco 5.xls")

pytestmark = pytest.mark.skipif(
    not XLS_PATH.exists(), reason="Gioco 5.xls non presente (atteso in CI)"
)


def _load_xls():
    pytest.importorskip("xlrd")
    from tools.extract_gioco5 import extract

    return extract(str(XLS_PATH))


def test_committed_drivers_match_xls():
    data = _load_xls()
    xls_drivers = data["drivers"]
    for key, by_role in xls_drivers.items():
        for role, bands in by_role.items():
            for band, val in bands.items():
                if val is None:
                    continue
                assert DRIVERS[key][role][band] == pytest.approx(val), f"{key}/{role}/{band}"


def test_committed_clamp_match_xls():
    data = _load_xls()
    for role, b in data["clamp"].items():
        assert RANGE_CLAMP[role]["up"] == pytest.approx(b["up"]), f"{role} up"
        assert RANGE_CLAMP[role]["down"] == pytest.approx(b["down"]), f"{role} down"
