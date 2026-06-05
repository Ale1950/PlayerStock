"""Football-Data.org provider (Serie A roster + fixture).

Endpoint v4: https://api.football-data.org/v4
Free tier: ~10 req/min. Cache su DB (no Redis Fase 1).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

import requests

from app.data_providers.base import DataProvider

logger = logging.getLogger(__name__)

# Mapping ruoli FD.org → ruoli interni
POSITION_MAP: dict[str, str] = {
    "Goalkeeper": "POR",
    "Defence": "DIF", "Defender": "DIF", "Centre-Back": "DIF",
    "Left-Back": "DIF", "Right-Back": "DIF", "Left Wing-Back": "DIF",
    "Right Wing-Back": "DIF", "Sweeper": "DIF",
    "Midfield": "CC", "Midfielder": "CC", "Defensive Midfield": "CC",
    "Central Midfield": "CC", "Attacking Midfield": "CC",
    "Left Midfield": "CC", "Right Midfield": "CC",
    "Offence": "ATT", "Forward": "ATT", "Striker": "ATT", "Centre-Forward": "ATT",
    "Left Winger": "ATT", "Right Winger": "ATT", "Second Striker": "ATT",
}

# Mapping nazionalità (nomi inglesi FD.org → ISO-3)
NATIONALITY_TO_ISO3: dict[str, str] = {
    "Italy": "ITA", "France": "FRA", "Germany": "DEU", "Spain": "ESP",
    "Argentina": "ARG", "Brazil": "BRA", "Portugal": "PRT", "England": "ENG",
    "Netherlands": "NLD", "Belgium": "BEL", "Croatia": "HRV", "Serbia": "SRB",
    "Switzerland": "CHE", "Austria": "AUT", "Denmark": "DNK", "Sweden": "SWE",
    "Norway": "NOR", "Poland": "POL", "Romania": "ROU", "Ukraine": "UKR",
    "Russia": "RUS", "Czech Republic": "CZE", "Slovakia": "SVK", "Slovenia": "SVN",
    "Hungary": "HUN", "Greece": "GRC", "Turkey": "TUR", "Albania": "ALB",
    "Bosnia and Herzegovina": "BIH", "Montenegro": "MNE", "North Macedonia": "MKD",
    "Kosovo": "XKX", "Senegal": "SEN", "Nigeria": "NGA", "Ghana": "GHA",
    "Ivory Coast": "CIV", "Cameroon": "CMR", "Morocco": "MAR", "Algeria": "DZA",
    "Tunisia": "TUN", "Egypt": "EGY", "South Korea": "KOR", "Japan": "JPN",
    "Australia": "AUS", "United States": "USA", "Mexico": "MEX",
    "Chile": "CHL", "Colombia": "COL", "Uruguay": "URY", "Paraguay": "PRY",
    "Peru": "PER", "Venezuela": "VEN", "Ecuador": "ECU", "Bolivia": "BOL",
    "Ireland": "IRL", "Scotland": "SCO", "Wales": "WAL", "Northern Ireland": "NIR",
    "Finland": "FIN", "Iceland": "ISL",
}


def _normalize_role(fd_position: str | None) -> str:
    if not fd_position:
        return "CC"
    return POSITION_MAP.get(fd_position.strip(), "CC")


def _normalize_nationality(fd_nationality: str | None) -> str:
    if not fd_nationality:
        return "UNK"
    return NATIONALITY_TO_ISO3.get(fd_nationality.strip(), fd_nationality.strip()[:3].upper())


def _compute_age(date_of_birth: str | None) -> int | None:
    if not date_of_birth:
        return None
    try:
        d = date.fromisoformat(date_of_birth[:10])
        today = date.today()
        return today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    except Exception:
        return None


class FootballDataOrgProvider(DataProvider):
    provider_name = "football_data_org"

    SERIE_A_CODE = "SA"  # competition code

    def __init__(self, *, api_token: str, base_url: str = "https://api.football-data.org/v4") -> None:
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"X-Auth-Token": api_token})

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        resp = self._session.get(url, timeout=20)
        if resp.status_code == 429:
            logger.warning("Football-Data.org rate-limited (429), sleeping 6s")
            import time
            time.sleep(6)
            resp = self._session.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()

    async def fetch_teams(self, *, sport: str, season: int) -> list[dict[str, Any]]:
        """Serie A teams + roster (FD.org returns squad inside teams endpoint)."""
        assert sport == "calcio"
        path = f"/competitions/{self.SERIE_A_CODE}/teams?season={season}"
        data = await asyncio.to_thread(self._get, path)
        return data.get("teams", [])

    async def fetch_roster(self, *, team_external_id: str, season: int) -> list[dict[str, Any]]:
        """Roster di una singola squadra."""
        path = f"/teams/{team_external_id}"
        data = await asyncio.to_thread(self._get, path)
        return data.get("squad", [])

    async def fetch_serie_a_full(self, *, season: int) -> list[dict[str, Any]]:
        """Fetch combinato: ritorna lista di dict normalizzati per ogni giocatore.

        Output schema (per atleta):
        {
            "external_id": "12345",
            "internal_full_name": "Lautaro Martínez",
            "role": "ATT",
            "nationality_iso3": "ARG",
            "age": 27,
            "date_of_birth": "1997-08-22",
            "team_fd_name": "FC Internazionale Milano",
            "team_fd_id": 108,
        }
        """
        teams = await self.fetch_teams(sport="calcio", season=season)
        results: list[dict[str, Any]] = []
        for team in teams:
            squad = team.get("squad", [])
            for player in squad:
                name = (player.get("name") or "").strip()
                if not name:
                    continue
                results.append({
                    "external_id": str(player.get("id", "")),
                    "internal_full_name": name,
                    "role": _normalize_role(player.get("position")),
                    "nationality_iso3": _normalize_nationality(player.get("nationality")),
                    "age": _compute_age(player.get("dateOfBirth")),
                    "date_of_birth": player.get("dateOfBirth"),
                    "team_fd_name": team.get("name", ""),
                    "team_fd_short_name": team.get("shortName", ""),
                    "team_fd_id": team.get("id"),
                })
        return results

    async def health_check(self) -> dict[str, Any]:
        try:
            data = await asyncio.to_thread(self._get, f"/competitions/{self.SERIE_A_CODE}")
            return {"ok": True, "competition": data.get("name", "")}
        except Exception as e:
            return {"ok": False, "error": str(e)}
