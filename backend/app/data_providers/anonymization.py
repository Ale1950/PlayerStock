"""Livello 2 anonymization: internal full name → display fields.

Esempi:
  "Lautaro Martínez"  → initial="L.", lastname="Martín" (max 8 char), label="L. Martín"
  "Cristiano Ronaldo" → initial="C.", lastname="Ronaldo", label="C. Ronaldo"
  "Dušan Vlahović"    → initial="D.", lastname="Vlahovi" (max 8), label="D. Vlahovi"
"""
from __future__ import annotations

import unicodedata

MAX_LASTNAME_CHARS = 8


def _strip_accents(s: str) -> str:
    """Mantiene caratteri leggibili rimuovendo diacritici per il troncamento."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def anonymize_name(full_name: str) -> tuple[str, str, str]:
    """Ritorna (display_initial, display_lastname, display_label) Livello 2.

    Strategia:
    - prende l'ULTIMA parola come "cognome" (gestisce nomi composti tipo "De Rossi")
    - troncamento del cognome a MAX_LASTNAME_CHARS (8)
    - iniziale = prima lettera del primo token + "."
    """
    if not full_name:
        return "?", "?", "?"
    full = full_name.strip()
    tokens = full.split()
    if len(tokens) == 1:
        # Mono-token: tipico dei brasiliani/spagnoli (Bremer, Vitinha, Pedro, Dodô)
        # Mostra solo il token (no iniziale ridondante).
        single = tokens[0]
        truncated = single[:MAX_LASTNAME_CHARS]
        initial = f"{single[0].upper()}."
        label = truncated
    else:
        initial = f"{tokens[0][0].upper()}."
        # ultima parola = cognome (semplificazione: per "De Rossi" prende "Rossi")
        lastname_full = tokens[-1]
        truncated = lastname_full[:MAX_LASTNAME_CHARS]
        label = f"{initial} {truncated}".strip()
    return initial, truncated, label
