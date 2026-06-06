"""Athlete & Team Pydantic models (anonimizzazione Livello 2)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import PyObjectId


# ───────── TEAMS FANTASY (Livello 2) ─────────
class TeamFantasyPublic(BaseModel):
    """Squadra fantasy mostrata in UI. Nome reale MAI esposto."""
    id: PyObjectId = Field(alias="_id")
    sport_id: str
    fantasy_name: str
    city: str
    color_primary: str
    color_secondary: str
    country_iso3: str

    model_config = {"populate_by_name": True}


# ───────── ATHLETES (Livello 2) ─────────
class AthletePublic(BaseModel):
    """Atleta mostrato in UI. `internal_full_name` MAI esposto."""
    id: PyObjectId = Field(alias="_id")
    sport_id: str
    display_initial: str
    display_lastname: str
    display_label: str  # es. "L. Martín"
    nationality_iso3: str
    role: Literal["POR", "DIF", "CC", "ATT"]
    age: int | None = None
    team_fantasy_id: PyObjectId
    team_fantasy_name: str | None = None  # denormalizzato per UI veloce
    team_color_primary: str | None = None
    team_color_secondary: str | None = None
    weekly_stats: dict | None = None  # forma compatta (gol/assist/parate/presenze)

    # Pricing in € (migrazione D7): prezzo quota = market_value_eur / FLOAT (ancora €M
    # Opzione B). value = prezzo × FLOAT, una sola fonte di verità.
    valore_iniziale_eur: float
    float_quote: int
    primary_pool_qty: int | None = None  # quote residue nel pool del banco (disponibili)
    prezzo_iniziale_eur: float
    prezzo_corrente_eur: float
    # Valore di mercato € corrente = prezzo_corrente_eur × FLOAT (segue il prezzo, live).
    market_value_eur: float | None = None
    status: Literal["ACTIVE", "TRANSFERRED", "RETIRED"]

    model_config = {"populate_by_name": True}


class AthleteListResponse(BaseModel):
    items: list[AthletePublic]
    total: int
    page: int
    page_size: int


# ───────── SPORT ─────────
class SportPublic(BaseModel):
    id: str = Field(alias="_id")
    name_key: str
    roles: list[str]
    active: bool

    model_config = {"populate_by_name": True}
