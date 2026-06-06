# PlayerStock — DESIGN SPEC (Fase Design · parte 1: fondamenta)

Fonte di verità del design. Direzione: **DARK NATIVO — neon su nero**. Marchio e icone
**proprietari** (tema calcio + mercato). Texture geometrica **generica** (griglia), non un brand.
NESSUN richiamo a loghi/mascotte altrui.

**PRIMARIO = CYAN/TEAL.** Viola = secondario. **Ambra = accento prezzo/valore** (oro NON è più
primario). I colori NON si hardcodano: si leggono dai **token** via `useTheme().colors` (o, per i
moduli statici, da `@/src/theme/colors` = scuro). Aggiungere/cambiare colori SOLO in `src/theme/tokens.ts`.

## Regola di INTENSITÀ MISTA
- **Schermate DATI** (Mercato, Dettaglio, Portafoglio, Classifica, Crediti) → **SOBRIE**: nero pieno,
  card con sottile bordo-superiore a gradiente colorato, numeri mono colorati, **niente glow pesante**.
- **Schermate REWARD ed ENGAGE** → **VIVIDE**: card con riempimento a gradiente + bordo luminescente
  (glow), pill colorate.
- **NACKL SEMPRE etichettato placeholder interno (non on-chain)**, coerente con Fase 5.
- In tema **CHIARO**: niente glow (il neon non rende su bianco) → colori pieni.

---

## 1. Token colore

### SCURO (hero, default)
| token | valore | | token | valore |
|---|---|---|---|---|
| `bg` | `#0E1320` (slate-navy morbido) | | `cyan` (primario) | `#22D3EE` |
| `surface` | `#171E2E` | | `teal` (primario) | `#2DD4BF` |
| `surfaceAlt` | `#212B40` | | `purple` (second.) | `#A78BFA` |
| `border` | `rgba(255,255,255,0.12)` | | `green` (positivo/live) | `#4ADE80` |
| `text` | `#EAF2F7` | | `amber` (prezzo/valore) | `#F5B544` |
| `muted` | `#7E8A99` | | `red` (negativo) | `#FB7185` |
| | | | `chartBlue` | `#5B8DEF` |

### CHIARO (secondario — niente glow)
| token | valore | | token | valore |
|---|---|---|---|---|
| `bg` | `#F5F7F9` | | `cyan` | `#0E9BB5` |
| `surface` | `#FFFFFF` | | `teal` | `#0D9488` |
| `surfaceAlt` | `#EEF1F4` | | `purple` | `#7C3AED` |
| `border` | `rgba(0,0,0,0.10)` | | `green` | `#15A150` |
| `text` | `#121821` | | `amber` | `#B8860B` |
| `muted` | `#5A6472` | | `red` | `#DC4C4C` |
| | | | `chartBlue` | `#3B6FD4` |

### Derivati / alias (in `tokens.ts`)
- `accent`→`cyan`, `accentHover`→`teal`. `gold`→`amber` (compat, prezzo/valore), `warning`→`amber`.
- `onAccent`/`onGold` = `#05070A` (inchiostro scuro su fill cyan/amber/teal).
- `up`/`success`→`green`, `down`/`danger`→`red`.
- `card`/`bgElevated`→`surface`, `cardHover`→`surfaceAlt`, `textPrimary`→`text`, `textSecondary`/`textMuted`→`muted`.
- `grid` (texture), `overlay`, `borderStrong`, `bannerBg/Border/Text`.
- `gradients` (export): `cyanTeal` `[#22D3EE,#2DD4BF]` · `purple` `[#A78BFA,#7C3AED]` · `amber` `[#F5B544,#B8860B]`.

---

## 2. Tipografia (Google Fonts — web via `app/+html.tsx`, nativo via expo-font)

| ruolo | famiglia | preset |
|---|---|---|
| **Titoli pagina** | `Space Grotesk` (bold) | `pageTitle` / `h1` `h2` `h3` |
| **Dati/numeri/label** | `JetBrains Mono` (label MAIUSCOLE muted) | `mono` `caption` `monoLabel` `wordmark` |
| **Corpo** | `Inter` | `body` `bodyBold` `small` |
| **Accento editoriale** (occasionale) | `Fraunces` (serif) | `display` |

`spacing` 4/8/16/24/32/48 · `radius` sm6 md10 lg14 **card18** pill999 · **`borderW` = 1.75** (spessore bordo
box, token globale: i box usano `borderWidth: borderW` invece di `1` → si propaga ovunque).

---

## 3. Componenti (pattern)

- **StatTile** (`src/components/StatTile.tsx`) — *sobrio, dati*: card `surface`, **bordo-superiore 2px a
  gradiente** nel colore della metrica, chip icona tinto, numero grande mono nel colore metrica, label
  MAIUSCOLA muted + sotto-caption. Ogni tile un colore diverso (cyan/teal/purple/green/amber/red). Niente glow.
- **VividCard** (`src/components/VividCard.tsx`) — *vivido, reward/engage*: riempimento a **gradiente**
  (`cyan`/`purple`/`amber`) + **bordo glow** (solo dark) + **pill** di stato. Testo inchiostro scuro
  (`VividText`). Prop `pill="PLACEHOLDER"` per NACKL.
- **Card** (`src/components/Card.tsx`) — base: radius 18, `surface`, border 1px; `accent` = barra
  sinistra 4px.
- **Chip/pill**: radius pieno, border 1px; attivo = fill `cyan`, testo `onAccent`.
- **Status ticker** (`chrome/StatusTicker`): mono, `LABEL: valore`, valori in colore semantico.
- **Bottom-nav**: icone-linea, **attivo `cyan`** (glow su dark riservato; tinta cyan).
- **Toggle tema** sole/luna (`chrome/ThemeToggle`) in header + Profilo.
- **BrandMark** (`chrome/BrandMark`): cerchio (pallone) + trend ascendente, **cyan**. Proprietario.
- **Texture** (`chrome/GeometricBackground`): griglia SVG bassissima opacità.

*(Passaggio finale, NON ora: serie grafiche neon, trend tratteggiato, donut, barre severità, sparkline ovunque.)*

---

## 4. Chrome globale

In `app/(tabs)/_layout.tsx`: **Header** (`AppHeader`: wordmark `PLAYERSTOCK` + dot live `green` +
lingua + toggle tema + profilo/login cyan) · **Status ticker** · **Bottom-nav** cyan attivo · **Texture**.
`ThemeProvider` (`src/theme/ThemeProvider.tsx`) in `app/_layout.tsx`, default **SCURO**, persistito
(`storage` `playerstock.theme.scheme`); `StatusBar` segue il tema.

---

## 5. NACKL

Reward NACKL **SEMPRE etichettato placeholder interno (non on-chain)** (Fase 5). Es. ticker
`NACKL: PLACEHOLDER`; card reward con pill `PLACEHOLDER`. Gamificato sì, ma niente UI che implichi
crypto reale attiva.

---

## 6. Migrazione schermate

```tsx
const { colors } = useTheme();
const styles = useMemo(() => makeStyles(colors), [colors]);
const makeStyles = (colors: ThemeColors) => StyleSheet.create({ /* usa colors.* */ });
```

**Convertite/reattive:** chrome, **home (Mercato)**, **profilo**, **wallet-hub** (parziale).
Le altre tab (classifica/engage/reward) + dettaglio giocatore usano ancora `@/src/theme/colors` (scuro):
leggibili in SCURO ma non commutano in CHIARO. Conversione per-schermata + rifinitura grafica
(StatTile/VividCard ovunque, grafici) = **passaggio finale**, dopo approvazione.

---

## 6b. Uso componenti per schermata (Parte 2)

Nuovi componenti condivisi: `StateView` (loading/vuoto/errore), `PriceChart` (area line SVG, sobrio),
`ValueBars` (scomposizione valore). Servizio `stats.service.ts` → `/api/stats/*`. Dati SOLO interni;
se manca un dato → stato vuoto pulito, **mai numeri finti**.

### Primitivo RESPONSIVE (web = target)
`ResponsiveTable<T>` (`src/components/ResponsiveTable.tsx`) + hook `useResponsive` (breakpoint 760px):
**TABELLA a colonne ordinabili su desktop · CARD su mobile**, stessa sorgente dati. Riusabile in tutte
le schermate. Il chiamante passa `columns` (desktop, con `sortable`) + `renderCard` (mobile) + `sort`/`onSort`.
Prop **`onRowPress`** = riga desktop tappabile (cursor pointer su web) — usato in Mercato per aprire il
Dettaglio (regressione cliccabilità risolta). Prop `rowStyle` = evidenziazione riga (es. "TU" in Classifica).
Componenti di supporto: `TeamBadge` (stemma colori reali squadra + iniziali), `flagEmoji(iso3)` (bandiera),
`StateView`.

- **MERCATO** (`app/(tabs)/home.tsx`, sobrio · RESPONSIVE · `/stats/market` + `/players` + price-history):
  striscia top gainers/losers · 4 `StatTile` market-wide (cap=amber, volume=cyan, attivi=teal, mov.max=purple).
  - **Desktop**: tabella colonne ordinabili — Cognome · Squadra (`TeamBadge`+colore) · Nazione (bandiera) ·
    Prezzo (**amber**) / Var% (verde/rosso) · Trend (`Sparkline`) · Stagione (gol/assist o parate).
  - **Mobile**: card ricca con `TeamBadge` colorato (al posto dell'accent-bar) + bandiera + ruolo + squadra +
    prezzo/var + sparkline + mini-stat stagionali.
  - Colonne **VALORE** (= prezzo × float, leggibile) e **DISPONIBILI** (quote residue del pool del banco) + **%
    posseduta**, ordinabili. Stato **ESAURITO** (pool ≤ 0) evidente su riga/card (badge rosso). Righe/card tappabili → Dettaglio.
  - Ricerca **multi-campo** (cognome/squadra/nazione, client-side) · filtri **ruolo** + **squadra** (server) +
    **nazione** (chip bandiera) · `StateView` (loading/vuoto/errore, niente numeri finti).
  - Dati: **stat sportive sintetiche** (`/players` compatte + `/stats/athletes/{id}` complete) coerenti con
    score+ruolo (`synthetic_stats.py`); **colori squadra** da `teams_fantasy`; **disponibili** = `primary_pool_qty`.
- **DETTAGLIO** (`app/player/[id].tsx`, sobrio · `/stats/athletes/{id}` + price-history):
  hero compatto con accent-bar ruolo · prezzo grande mono **amber** + var 24h · `PriceChart` con
  toggle **24H/7D/30D** · `StatTile` (market cap, possessori, var 7g, volume 7g, max, min) ·
  card scostamento vs equo + deviazione · `ValueBars` (ruolo/score/età/minuti/squadra) · tile **VALORE** +
  **DISPONIBILI** (% poss / ESAURITO) · **card buy/sell wirata** (ritematizzata: buy cyan, sell rosso). Se
  **ESAURITO**: banner "esaurito sul mercato finché qualcuno non vende", **buy disabilitato**, sell sempre attiva.
- **PORTAFOGLIO** (`app/(tabs)/portfolio.tsx`, sobrio · RESPONSIVE · `/portfolio` + `/stats/me/analytics`):
  hero patrimonio (cassa/titoli/P&L) · **selettore periodo** 1S/1M/3M/tutto · **grafico equity** (`PriceChart`)
  con **bucket adattivo** (giorni/settimane) + **overlay tratteggiato cyan = miglior utente** (solo pseudonimo) ·
  pannello **indici** (rendimento/volatilità/maxDD/beta/Sharpe) + confronto col miglior utente · **posizioni
  espandibili** → grafico andamento + indici + **overlay confronto col miglior giocatore** (`PriceChart.overlay`).
  `PriceChart` ora accetta `overlay` (seconda serie normalizzata, cyan tratteggiata). `StateView`.
- **CLASSIFICA** (`app/(tabs)/leaderboard.tsx`, sobrio · RESPONSIVE · `/stats/leaderboard-analytics`):
  stat **finanziarie** (non sportive) per utente — **solo pseudonimi**. Desktop = `ResponsiveTable` ordinabile
  (# medaglia · Pseudonimo [**TU** evidenziato] · Patrimonio · Rendimento% · ROI vs mercato · Win-rate · Volatilità ·
  mini-trend `Sparkline`); mobile = card con medaglia top-3 + metriche compatte. Tab ordinamento
  **PATRIMONIO/RENDIMENTO/SETTIMANA** + selettore periodo. Riga "TU" evidenziata (`ResponsiveTable.rowStyle`). `StateView`.
- **ENGAGE** (`app/(tabs)/engage.tsx`, **VIVIDO** · `/engagement/overview`): **launcher COMPATTI e UNIFORMI**
  (`VividCard` glow, **altezza fissa**, **gap** in griglia 2-col desktop / stack mobile) per le **6 attività**, ognuna
  con un **colore neon DISTINTO** disposto a scacchiera (cyan·purple / green·amber / pink·teal — nessuna colonna
  mono-colore): Streak · Quiz Mercato · Pronostici · Sfida · Missioni · **News**. 6 gradienti in `gradients`
  (cyanTeal/teal/purple/green/amber/pink), `VividCard variant`. Tap → **pannello dedicato** (`Modal`: centrato su desktop
  ~560px, quasi-fullscreen su mobile) col contenuto: Quiz → domande dai dati `/api/stats`; Missioni → lista con barre
  progresso + riscatta; Sfida → classifica (pseudonimi + TU + premi); Pronostici → lista; Streak → riscatta;
  **News → feed eventi** (top mover con spiegazione sportiva sintetica · esauriti · news personalizzate sulle tue
  posizioni; informativo, nessun premio). Pannello **sobrio** (surface, leggibile). **Premi DISTINTI** (valori
  APPROVATI): *Crediti* (gioco) vs *NACKL* (placeholder) — ledger separati. `StateView`.
- **Crediti-hub** (`(tabs)/wallet.tsx`, voce nav "Crediti") — **3 blocchi, tematizzato (chiaro/scuro)**:
  1. **Crediti** (SOBRIO): saldo grande (amber); card "guadagno da attività oggi" con **barra progresso x/5**
     (tetto faucet giornaliero, derivato dai movimenti `engagement_reward` di oggi — solo display) + link
     "Guadagna Crediti" → Engage; **Movimenti** in `ResponsiveTable` (tabella desktop / card mobile) con `StateView`.
  2. **Reward · NACKL** (VIVIDO, nettamente distinto): `VividCard` viola con pill **"ANTEPRIMA · NON REALE"**
     (`is_placeholder`), saldo NACKL, stato/rete/accrual, nota "economia separata: non si mischia coi Crediti,
     non compra quote"; sotto, card SOBRIA wallet-connect (SOLO mining **public** key) + "QR in arrivo".
  3. **Traguardi** (DISPLAY-ONLY): badge celebrativi derivati dai dati (benvenuto / prime attività / NACKL attivo /
     tetto pieno), **nessun premio** (etichetta esplicita).
- **Profilo** (`(tabs)/profile.tsx`, sobrio, additivo): intestazione account Google (soprannome+email); **"Le tue
  statistiche"** (rendimento / ROI vs mercato / win-rate da `/stats/leaderboard-analytics` self) + link Classifica;
  **Impostazioni** (lingua IT attiva + "altre in arrivo", tema sole/luna); link **"Come funziona"**; Esci; versione.

---

## 7. Bottom-nav (accorpamento — GIÀ implementato, approvato)

7 voci troppe per mobile → **5 voci**: `Mercato · Portafoglio · Classifica · Engage · Crediti(hub)`.
Reward e Profilo dentro rotte nascoste (`href:null`): Reward confluito nel **blocco NACKL** dell'hub Crediti;
Profilo dall'icona header. **Design pass CHIUSO** dopo Gruppo 3b (+ Fase 2c valore €M e relativo backfill).
