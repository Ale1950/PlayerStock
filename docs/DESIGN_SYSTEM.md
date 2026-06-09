# PlayerStock — DESIGN SYSTEM (fonte di verità)

> Questo documento **sostituisce** `DESIGN_SPEC.md` (vedi DECISIONS **D11/D12**). Direzione:
> **Luxury — carbone + oro**, finestre con **bordo lime 2px**, font **Manrope**, impaginazione **bento "B"**.
> I colori NON si hardcodano: si leggono dai **token** via `useTheme().colors`. Aggiungere/cambiare
> colori SOLO in `frontend/src/theme/tokens.ts`.

## Tema
**Unico tema scuro (Luxury).** Nessun tema chiaro, nessun toggle (ritirati — D12).

## 1. Token colore

| token | valore | uso |
|---|---|---|
| `bg` | `#12110f` | sfondo app (carbone) |
| `surface` | `#1d1a16` | superficie card/pannelli |
| `barBg` | `#1a1813` | header + bottom tab bar |
| `surfaceAlt` (surface-2) | `#26221b` | superficie elevata / chip |
| `borderWindow` (lime) | `#c6ff00` | **bordo finestra 2px** (solo card top-level) |
| `border` (subtle) | `#34302a` | bordi sotto-elementi (NON lime) |
| `text` | `#f3eee4` | testo primario |
| `muted` | `#9a907f` | testo secondario / label |
| `accent` (oro) | `#cda24f` | accento: prezzo/valore, attivo, CTA |
| `onAccent` | `#1d1a16` | inchiostro su riempimenti oro |
| `up` | `#9bc08a` | variazione positiva |
| `down` | `#cf8170` | variazione negativa |
| `avatarBg` | `#2c281f` | sfondo avatar/badge |
| `avatarFg` | `#cda24f` | iniziali/foreground avatar |

**Font:** **Manrope** (pesi 400–800). Una sola famiglia per titoli, corpo, label e numeri
(i numeri usano `fontVariant: ['tabular-nums']`).

## 2. Regola FINESTRA (card)
- **Card "finestra"** (pannello top-level di una schermata/sezione) = `surface` + **bordo `borderWindow` lime 2px** + **radius 16**.
- **Sotto-elementi** (righe lista, chip, sotto-card dentro una finestra) = bordo `border` (subtle), **mai lime**.
- Il lime è la firma visiva: usarlo con parsimonia, solo sui contenitori principali.

## 3. Bento — "impaginazione B" (IMPLEMENTATO)
La home è la **dashboard bento** (`app/(tabs)/home.tsx`); la tabella mercato è nella tab **Mercato** (`app/(tabs)/market.tsx`).
- **Colonna principale 2/3:** card *hero match day · portafoglio · posizione · mercato · talento del giorno*.
- **Colonna destra 1/3 "News del giorno":** lista di card (fonte in **oro** + titolo, link esterni).
- **Mobile:** collassa a 1 colonna, News in fondo.
- Pannelli = `BentoCard` (finestra lime 2px); righe interne su border-subtle.

**Ancora placeholder (in attesa di feature dedicate):** *Match day* (motore giornata live, feature #2) e
*News del giorno* (feed RSS reale). Gli altri moduli usano dati reali esistenti (Talento = best gainer da `/stats/market`).

## 4. Gradienti
Luxury è **piatto**: niente neon/glow forte. I pochi gradienti residui usano coppie **oro/bronzo**
(`#cda24f`→`#b8893f`); positivo `#9bc08a`→`#7fa06f`; negativo `#cf8170`→`#b86a5a`.

## 5. Chrome
- Header e bottom tab bar su `barBg`, separatori `border`.
- Tinta attiva tab/chip = `accent` (oro). Stato "live" = `up`.
- Avatar/badge squadra su `avatarBg`/`avatarFg`.
