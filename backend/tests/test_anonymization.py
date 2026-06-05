"""Test anonimizzazione Livello 2.

Garanzia L2: `internal_full_name` non deve MAI raggiungere il client.
Due livelli verificati qui:
  1. anonymize_name() produce display fields troncati (cognome max 8 char).
  2. il modello AthletePublic NON espone internal_full_name nemmeno se presente
     nel documento sorgente (Pydantic scarta i campi extra).
"""
from __future__ import annotations

from bson import ObjectId

from app.data_providers.anonymization import MAX_LASTNAME_CHARS, anonymize_name
from app.models.athlete import AthletePublic


# ───────── anonymize_name() ─────────
def test_multi_token_initial_and_truncation():
    initial, lastname, label = anonymize_name("Lautaro Martinez")
    assert initial == "L."
    assert lastname == "Martinez"  # 8 char esatti, non troncato
    assert len(lastname) <= MAX_LASTNAME_CHARS
    assert label == "L. Martinez"


def test_lastname_never_exceeds_8_chars():
    # cognome lungo deve essere troncato
    _, lastname, _ = anonymize_name("Mario Stramaccioni")
    assert len(lastname) <= MAX_LASTNAME_CHARS
    assert lastname == "Stramacc"


def test_mono_token():
    initial, lastname, label = anonymize_name("Bremer")
    assert initial == "B."
    assert lastname == "Bremer"
    assert label == "Bremer"


def test_compound_surname_takes_last_token():
    initial, lastname, _ = anonymize_name("Daniele De Rossi")
    assert initial == "D."
    assert lastname == "Rossi"


def test_empty_name():
    assert anonymize_name("") == ("?", "?", "?")


# ───────── modello AthletePublic non espone internal_full_name ─────────
def test_athlete_public_strips_internal_full_name():
    doc = {
        "_id": ObjectId(),
        "sport_id": "calcio",
        "internal_full_name": "Lautaro Martinez",  # campo riservato
        "display_initial": "L.",
        "display_lastname": "Martinez",
        "display_label": "L. Martinez",
        "nationality_iso3": "ARG",
        "role": "ATT",
        "age": 27,
        "team_fantasy_id": ObjectId(),
        "team_fantasy_name": "Nerazzurri Milano",
        "team_color_primary": "#0033A0",
        "valore_iniziale_crediti": 1000.0,
        "float_quote": 1_000_000,
        "prezzo_iniziale_crediti": 0.01,
        "prezzo_corrente_crediti": 0.01,
        "status": "ACTIVE",
    }
    public = AthletePublic.model_validate(doc)
    dumped = public.model_dump()
    assert "internal_full_name" not in dumped
    # anche nel JSON serializzato by_alias
    assert "internal_full_name" not in public.model_dump_json()
    assert "Lautaro Martinez" not in public.model_dump_json()
