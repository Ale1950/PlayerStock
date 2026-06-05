"""Abstract DataProvider interface (multi-sport ready)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DataProvider(ABC):
    """Interfaccia astratta per provider di dati sportivi.

    Implementazioni concrete devono fornire roster, fixture e statistiche
    normalizzate in uno schema interno comune (multi-sport ready).
    """

    provider_name: str

    @abstractmethod
    async def fetch_teams(self, *, sport: str, season: int) -> list[dict[str, Any]]:
        """Restituisce la lista delle squadre di una stagione."""

    @abstractmethod
    async def fetch_roster(self, *, team_external_id: str, season: int) -> list[dict[str, Any]]:
        """Restituisce il roster (giocatori) di una squadra."""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Restituisce stato e info sul provider (per /api/admin/data-sync-log)."""
