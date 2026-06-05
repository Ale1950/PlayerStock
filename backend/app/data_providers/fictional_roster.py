"""Roster FITTIZIO ma realistico (Decisione Fase 1 — Opzione 3 raffinata).

Genera ~400 giocatori inventati ma plausibili (nomi/nazionalità coerenti, età
realistiche) per le 20 squadre fantasy Serie A: 2 POR + 6 DIF + 6 CC + 6 ATT.

NESSUNA persona reale: i nomi sono combinazioni casuali (seed deterministico) di
pool per-nazionalità. L'anonimizzazione L2 gira comunque a valle (display_*).

Il `seed_roster` legge il file statico committato in `app/data/` (niente token
Football-Data per i giocatori). `generate_fictional_roster.py` lo (ri)genera.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from app.config.teams_fantasy_map import SERIE_A_FANTASY_MAP
from app.data_providers.base import DataProvider

# File seed statico nel repo
ROSTER_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "serie_a_roster_fittizio.json"

# Seed di default (deterministico → output riproducibile)
DEFAULT_SEED = 20260605

# Composizione roster per squadra
ROLE_COMPOSITION: list[tuple[str, int]] = [("POR", 2), ("DIF", 6), ("CC", 6), ("ATT", 6)]

# Distribuzione nazionalità (peso relativo). ITA dominante, mix realistico Serie A.
NATIONALITY_WEIGHTS: list[tuple[str, int]] = [
    ("ITA", 50), ("ARG", 6), ("BRA", 6), ("FRA", 5), ("ESP", 4),
    ("DEU", 3), ("NLD", 3), ("BEL", 3), ("PRT", 3), ("SRB", 3),
    ("HRV", 3), ("SEN", 3), ("NGA", 2), ("POL", 2),
]

# Pool nomi/cognomi per nazionalità. Combinati casualmente → nessuna persona reale.
NAME_POOLS: dict[str, dict[str, list[str]]] = {
    "ITA": {
        "first": [
            "Marco", "Luca", "Andrea", "Matteo", "Davide", "Simone", "Lorenzo", "Federico",
            "Alessandro", "Francesco", "Giuseppe", "Antonio", "Stefano", "Riccardo", "Tommaso",
            "Gabriele", "Nicolo", "Emanuele", "Christian", "Daniele", "Filippo", "Edoardo",
            "Giacomo", "Mattia", "Pietro", "Samuele", "Vincenzo", "Salvatore", "Domenico", "Fabio",
            "Cristian", "Manuel", "Leonardo", "Alberto", "Roberto", "Michele", "Enrico", "Paolo",
        ],
        "last": [
            "Rossi", "Bianchi", "Ferrari", "Esposito", "Russo", "Romano", "Colombo", "Ricci",
            "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Mancini", "Costa",
            "Giordano", "Rizzo", "Lombardi", "Moretti", "Barbieri", "Fontana", "Santoro",
            "Mariani", "Rinaldi", "Caruso", "Ferrara", "Galli", "Martini", "Leone", "Longo",
            "Gentile", "Martinelli", "Vitale", "Lombardo", "Serra", "Coppola", "De Santis", "Marchetti", "Parisi",
        ],
    },
    "ARG": {
        "first": ["Lautaro", "Mateo", "Santiago", "Joaquin", "Nicolas", "Facundo", "Agustin",
                  "Tomas", "Lucas", "Franco", "Gonzalo", "Emiliano", "Julian", "Thiago", "Bruno"],
        "last": ["Gomez", "Fernandez", "Lopez", "Diaz", "Martinez", "Sanchez", "Romero",
                 "Sosa", "Acosta", "Benitez", "Medina", "Suarez", "Herrera", "Aguirre", "Paredes"],
    },
    "BRA": {
        "first": ["Gabriel", "Lucas", "Matheus", "Joao", "Bruno", "Rafael", "Felipe", "Vinicius",
                  "Caio", "Igor", "Murilo", "Wesley", "Danilo", "Everton", "Rodrigo"],
        "last": ["Silva", "Santos", "Souza", "Oliveira", "Pereira", "Lima", "Costa", "Almeida",
                 "Ferreira", "Ribeiro", "Carvalho", "Gomes", "Barbosa", "Rocha", "Cardoso"],
    },
    "FRA": {
        "first": ["Hugo", "Lucas", "Theo", "Maxime", "Antoine", "Clement", "Mathis", "Nathan",
                  "Romain", "Enzo", "Yanis", "Loic", "Florian", "Adrien", "Bastien"],
        "last": ["Martin", "Bernard", "Dubois", "Moreau", "Laurent", "Girard", "Lefevre", "Mercier",
                 "Faure", "Roussel", "Garnier", "Chevalier", "Robin", "Morel", "Fontaine"],
    },
    "ESP": {
        "first": ["Pablo", "Sergio", "Alvaro", "Carlos", "Diego", "Javier", "Adrian", "Marcos",
                  "Hugo", "Mario", "Raul", "Iker", "Aitor", "Unai", "Borja"],
        "last": ["Garcia", "Martinez", "Lopez", "Sanchez", "Perez", "Gonzalez", "Rodriguez",
                 "Fernandez", "Moreno", "Jimenez", "Alvarez", "Romero", "Navarro", "Torres", "Gil"],
    },
    "DEU": {
        "first": ["Lukas", "Jonas", "Leon", "Felix", "Maximilian", "Tim", "Niklas", "Florian",
                  "Jan", "Moritz", "Philipp", "Tobias", "Julian", "Marcel", "Erik"],
        "last": ["Muller", "Schmidt", "Schneider", "Fischer", "Weber", "Wagner", "Becker",
                 "Hoffmann", "Schafer", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Neumann"],
    },
    "NLD": {
        "first": ["Daan", "Sem", "Lars", "Bram", "Thijs", "Ruben", "Joost", "Tijn",
                  "Stijn", "Niels", "Jurgen", "Koen", "Wout", "Tim", "Bas"],
        "last": ["de Jong", "Jansen", "de Vries", "van Dijk", "Bakker", "Visser", "Smit",
                 "Meijer", "Mulder", "de Boer", "Bos", "Vos", "Peters", "Hendriks", "van Berg"],
    },
    "BEL": {
        "first": ["Thomas", "Louis", "Arthur", "Noah", "Victor", "Jules", "Lars", "Wout",
                  "Senne", "Lander", "Robbe", "Stan", "Vince", "Mathis", "Aaron"],
        "last": ["Peeters", "Janssens", "Maes", "Jacobs", "Mertens", "Willems", "Claes",
                 "Goossens", "Wouters", "De Smet", "Vermeulen", "Dubois", "Lambert", "Aerts", "Coppens"],
    },
    "PRT": {
        "first": ["Joao", "Diogo", "Rafael", "Tomas", "Goncalo", "Rodrigo", "Miguel", "Andre",
                  "Bruno", "Tiago", "Ricardo", "Nuno", "Fabio", "Pedro", "Duarte"],
        "last": ["Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Rodrigues",
                 "Martins", "Fernandes", "Goncalves", "Sousa", "Lopes", "Marques", "Pinto", "Mendes"],
    },
    "SRB": {
        "first": ["Nikola", "Stefan", "Marko", "Luka", "Aleksandar", "Milos", "Filip", "Nemanja",
                  "Dusan", "Vukasin", "Lazar", "Uros", "Dragan", "Petar", "Andrej"],
        "last": ["Jovanovic", "Petrovic", "Nikolic", "Markovic", "Djordjevic", "Stojanovic",
                 "Ilic", "Pavlovic", "Kovacevic", "Lukic", "Ristic", "Milosevic", "Savic", "Todorovic", "Vasic"],
    },
    "HRV": {
        "first": ["Luka", "Ivan", "Marko", "Ante", "Josip", "Mateo", "Filip", "Petar",
                  "Domagoj", "Mario", "Nikola", "Borna", "Tin", "Roko", "Karlo"],
        "last": ["Horvat", "Kovacevic", "Babic", "Maric", "Juric", "Novak", "Kovacic",
                 "Vukovic", "Knezevic", "Markovic", "Petrovic", "Brkic", "Saric", "Tomic", "Blazevic"],
    },
    "SEN": {
        "first": ["Moussa", "Ibrahima", "Cheikh", "Pape", "Lamine", "Aliou", "Babacar", "Idrissa",
                  "Mamadou", "Ousmane", "Abdou", "Demba", "Khadim", "Modou", "Fallou"],
        "last": ["Diop", "Ndiaye", "Faye", "Sarr", "Gueye", "Diallo", "Ba", "Sow",
                 "Cisse", "Mbaye", "Seck", "Fall", "Diouf", "Sy", "Niang"],
    },
    "NGA": {
        "first": ["Emeka", "Chidi", "Tunde", "Kelechi", "Samuel", "Victor", "Daniel", "Joseph",
                  "Henry", "Peter", "Kingsley", "Sunday", "Bright", "Moses", "Gideon"],
        "last": ["Okafor", "Adeyemi", "Eze", "Okeke", "Obi", "Nwachukwu", "Bello", "Olawale",
                 "Chukwu", "Ibrahim", "Okonkwo", "Adebayo", "Onyekuru", "Babatunde", "Uche"],
    },
    "POL": {
        "first": ["Jakub", "Kacper", "Filip", "Michal", "Mateusz", "Bartosz", "Piotr", "Pawel",
                  "Adam", "Szymon", "Tomasz", "Marcin", "Lukasz", "Dawid", "Krzysztof"],
        "last": ["Nowak", "Kowalski", "Wisniewski", "Wojcik", "Kowalczyk", "Kaminski", "Lewandowski",
                 "Zielinski", "Szymanski", "Wozniak", "Dabrowski", "Kozlowski", "Mazur", "Krawczyk", "Piotrowski"],
    },
}


def _weighted_population(weights: list[tuple[str, int]]) -> list[str]:
    pop: list[str] = []
    for key, w in weights:
        pop.extend([key] * w)
    return pop


def _pick_age(rng: random.Random, role: str) -> int:
    """Età realistica: distribuzione triangolare centrata ~25, POR leggermente più anziani."""
    if role == "POR":
        return int(rng.triangular(19, 39, 28))
    return int(rng.triangular(17, 37, 25))


def generate_roster(seed: int = DEFAULT_SEED) -> list[dict[str, Any]]:
    """Genera la lista (deterministica) di ~400 giocatori fittizi.

    Schema per atleta = identico a `FootballDataOrgProvider.fetch_serie_a_full`:
    external_id, internal_full_name, role, nationality_iso3, age, date_of_birth,
    team_fd_name, team_fd_id.
    """
    rng = random.Random(seed)
    nat_pop = _weighted_population(NATIONALITY_WEIGHTS)
    roster: list[dict[str, Any]] = []
    used_names: set[str] = set()
    ext = 1

    for team in SERIE_A_FANTASY_MAP:
        for role, count in ROLE_COMPOSITION:
            for _ in range(count):
                # nazionalità + nome unico (entro la squadra)
                name = ""
                nat = "ITA"
                for _attempt in range(200):
                    nat = rng.choice(nat_pop)
                    pool = NAME_POOLS[nat]
                    candidate = f"{rng.choice(pool['first'])} {rng.choice(pool['last'])}"
                    if candidate not in used_names:
                        name = candidate
                        break
                used_names.add(name)
                roster.append({
                    "external_id": f"FIC{ext:04d}",
                    "internal_full_name": name,
                    "role": role,
                    "nationality_iso3": nat,
                    "age": _pick_age(rng, role),
                    "date_of_birth": None,
                    "team_fd_name": team["real_name_internal"],
                    "team_fd_id": team["real_id_internal"],
                })
                ext += 1

    return roster


class FictionalRosterProvider(DataProvider):
    """Provider che legge il roster fittizio statico dal file committato nel repo."""

    provider_name = "fictional_roster"

    def __init__(self, *, roster_path: Path | None = None) -> None:
        self.roster_path = roster_path or ROSTER_JSON_PATH

    def _load(self) -> list[dict[str, Any]]:
        return json.loads(self.roster_path.read_text(encoding="utf-8"))

    async def fetch_teams(self, *, sport: str, season: int) -> list[dict[str, Any]]:
        assert sport == "calcio"
        return [
            {"id": t["real_id_internal"], "name": t["real_name_internal"]}
            for t in SERIE_A_FANTASY_MAP
        ]

    async def fetch_roster(self, *, team_external_id: str, season: int) -> list[dict[str, Any]]:
        return [p for p in self._load() if p["team_fd_id"] == team_external_id]

    async def fetch_serie_a_full(self, *, season: int) -> list[dict[str, Any]]:
        """Ritorna l'intero roster fittizio (la stagione è ignorata: dati statici)."""
        return self._load()

    async def health_check(self) -> dict[str, Any]:
        try:
            data = self._load()
            return {"ok": True, "count": len(data), "source": str(self.roster_path.name)}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}
