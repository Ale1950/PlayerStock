"""
Mappa squadre reali Serie A → squadre fantasy (Livello 2 anonimizzazione).

Definita in PROJECT_SPEC.md §2. Lista delle 20 squadre Serie A 2024-25 e relativo
nome fantasy + colori + città. Usata da `data_providers/anonymization.py`.

NON esporre `real_id_internal` o `real_name_internal` in API/UI pubbliche.
"""
from __future__ import annotations
from typing import TypedDict


class FantasyTeamRecord(TypedDict):
    real_id_internal: str           # codice interno (mai esposto)
    real_name_internal: str          # nome reale (DB only)
    fantasy_name: str                # mostrato in UI
    city: str
    color_primary: str
    color_secondary: str
    country_iso3: str
    # alias di matching con il nome restituito da Football-Data.org
    fd_org_match_names: list[str]


SERIE_A_FANTASY_MAP: list[FantasyTeamRecord] = [
    {"real_id_internal": "inter", "real_name_internal": "Inter",
     "fantasy_name": "Nerazzurri Milano", "city": "Milano",
     "color_primary": "#003399", "color_secondary": "#000000", "country_iso3": "ITA",
     "fd_org_match_names": ["FC Internazionale Milano", "Inter", "Internazionale"]},
    {"real_id_internal": "juventus", "real_name_internal": "Juventus",
     "fantasy_name": "Bianconeri Torino", "city": "Torino",
     "color_primary": "#000000", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["Juventus FC", "Juventus"]},
    {"real_id_internal": "milan", "real_name_internal": "Milan",
     "fantasy_name": "Rossoneri Milano", "city": "Milano",
     "color_primary": "#FB090B", "color_secondary": "#000000", "country_iso3": "ITA",
     "fd_org_match_names": ["AC Milan", "Milan"]},
    {"real_id_internal": "napoli", "real_name_internal": "Napoli",
     "fantasy_name": "Azzurri Partenopei", "city": "Napoli",
     "color_primary": "#0066B2", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["SSC Napoli", "Napoli"]},
    {"real_id_internal": "roma", "real_name_internal": "Roma",
     "fantasy_name": "Giallorossi Capitolini", "city": "Roma",
     "color_primary": "#9B1B30", "color_secondary": "#F2C200", "country_iso3": "ITA",
     "fd_org_match_names": ["AS Roma", "Roma"]},
    {"real_id_internal": "lazio", "real_name_internal": "Lazio",
     "fantasy_name": "Biancocelesti Capitolini", "city": "Roma",
     "color_primary": "#87CEEB", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["SS Lazio", "Lazio"]},
    {"real_id_internal": "atalanta", "real_name_internal": "Atalanta",
     "fantasy_name": "Nerazzurri Bergamo", "city": "Bergamo",
     "color_primary": "#1A1A1A", "color_secondary": "#0066B2", "country_iso3": "ITA",
     "fd_org_match_names": ["Atalanta BC", "Atalanta"]},
    {"real_id_internal": "fiorentina", "real_name_internal": "Fiorentina",
     "fantasy_name": "Viola Firenze", "city": "Firenze",
     "color_primary": "#5D3FD3", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["ACF Fiorentina", "Fiorentina"]},
    {"real_id_internal": "bologna", "real_name_internal": "Bologna",
     "fantasy_name": "Rossoblu Felsinei", "city": "Bologna",
     "color_primary": "#8B0000", "color_secondary": "#003399", "country_iso3": "ITA",
     "fd_org_match_names": ["Bologna FC 1909", "Bologna"]},
    {"real_id_internal": "torino", "real_name_internal": "Torino",
     "fantasy_name": "Granata Torino", "city": "Torino",
     "color_primary": "#7A1F2E", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["Torino FC", "Torino"]},
    {"real_id_internal": "genoa", "real_name_internal": "Genoa",
     "fantasy_name": "Rossoblu Liguri", "city": "Genova",
     "color_primary": "#C8102E", "color_secondary": "#002F6C", "country_iso3": "ITA",
     "fd_org_match_names": ["Genoa CFC", "Genoa"]},
    {"real_id_internal": "lecce", "real_name_internal": "Lecce",
     "fantasy_name": "Giallorossi Salentini", "city": "Lecce",
     "color_primary": "#F2C200", "color_secondary": "#9B1B30", "country_iso3": "ITA",
     "fd_org_match_names": ["US Lecce", "Lecce"]},
    {"real_id_internal": "udinese", "real_name_internal": "Udinese",
     "fantasy_name": "Bianconeri Friulani", "city": "Udine",
     "color_primary": "#000000", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["Udinese Calcio", "Udinese"]},
    {"real_id_internal": "cagliari", "real_name_internal": "Cagliari",
     "fantasy_name": "Rossoblu Sardi", "city": "Cagliari",
     "color_primary": "#A41E1A", "color_secondary": "#002F6C", "country_iso3": "ITA",
     "fd_org_match_names": ["Cagliari Calcio", "Cagliari"]},
    {"real_id_internal": "monza", "real_name_internal": "Monza",
     "fantasy_name": "Biancorossi Brianzoli", "city": "Monza",
     "color_primary": "#C8102E", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["AC Monza", "Monza"]},
    {"real_id_internal": "verona", "real_name_internal": "Hellas Verona",
     "fantasy_name": "Gialloblu Scaligeri", "city": "Verona",
     "color_primary": "#F2C200", "color_secondary": "#003399", "country_iso3": "ITA",
     "fd_org_match_names": ["Hellas Verona FC", "Hellas Verona", "Verona"]},
    {"real_id_internal": "empoli", "real_name_internal": "Empoli",
     "fantasy_name": "Azzurri Toscani", "city": "Empoli",
     "color_primary": "#1E5DB1", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["Empoli FC", "Empoli"]},
    {"real_id_internal": "parma", "real_name_internal": "Parma",
     "fantasy_name": "Gialloblu Ducali", "city": "Parma",
     "color_primary": "#F2C200", "color_secondary": "#003399", "country_iso3": "ITA",
     "fd_org_match_names": ["Parma Calcio 1913", "Parma"]},
    {"real_id_internal": "como", "real_name_internal": "Como",
     "fantasy_name": "Biancoblu Lariani", "city": "Como",
     "color_primary": "#003399", "color_secondary": "#FFFFFF", "country_iso3": "ITA",
     "fd_org_match_names": ["Como 1907", "Como"]},
    {"real_id_internal": "venezia", "real_name_internal": "Venezia",
     "fantasy_name": "Arancioneroverdi Lagunari", "city": "Venezia",
     "color_primary": "#FF6600", "color_secondary": "#000000", "country_iso3": "ITA",
     "fd_org_match_names": ["Venezia FC", "Venezia"]},
]


def find_fantasy_by_real_name(real_name: str) -> FantasyTeamRecord | None:
    """Cerca una squadra fantasy dato un nome reale (case-insensitive, supporta alias)."""
    target = real_name.strip().lower()
    for team in SERIE_A_FANTASY_MAP:
        if target == team["real_name_internal"].lower():
            return team
        for alias in team["fd_org_match_names"]:
            if target == alias.lower():
                return team
    # match parziale
    for team in SERIE_A_FANTASY_MAP:
        for alias in team["fd_org_match_names"]:
            if target in alias.lower() or alias.lower() in target:
                return team
    return None
