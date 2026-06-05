"""Validazione wallet reward: SOLO mining PUBLIC key, mai seed/mnemonic/chiavi di spesa.

Lo spike (DECISIONS D0.5) conferma che l'AN Wallet condivide via QR/deep link solo la
mining public key. Qui rifiutiamo formati seed-like (mnemonic BIP39) e formati non validi.

Limite noto: una public e una secret ed25519 sono entrambe 32 byte (64 hex) → NON
distinguibili dal solo formato. La garanzia è che il QR fornisce solo la public; qui
blocchiamo almeno il caso più pericoloso (seed phrase incollata).
"""
from __future__ import annotations

import re

from app.core.errors import err_bad_request

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def validate_mining_public_key(key: str) -> str:
    """Ritorna la public key normalizzata (hex lower, senza 0x) o solleva APIError."""
    if not key or not key.strip():
        raise err_bad_request("reward.wallet.invalid_key", "Chiave mancante")
    s = key.strip()

    # Seed phrase (mnemonic BIP39): più parole alfabetiche → RIFIUTA categoricamente
    tokens = s.split()
    if len(tokens) >= 12 and all(t.isalpha() for t in tokens):
        raise err_bad_request(
            "reward.wallet.seed_not_allowed",
            "Inserisci la mining PUBLIC key, non una seed phrase o chiave segreta",
        )

    normalized = s[2:] if s.lower().startswith("0x") else s
    normalized = normalized.lower()
    if not _HEX64.match(normalized):
        raise err_bad_request(
            "reward.wallet.invalid_key",
            "Formato mining public key non valido (atteso hex 64 caratteri)",
        )
    return normalized
