# Match Day #2 (motore live) + Torneo Internazionale sintetico — Design + Piano a fasi

**Obiettivo finale:** modalità "Torneo Internazionale" sintetica (48 nazioni INVENTATE, gironi→eliminazione) costruita SOPRA il motore Match Day live. Tutto simulato dal nostro motore sorpresa. Nessun dato reale, nessun cashout, downside cappato.

**Principio:** il Match Day è la FONDAMENTA. Va progettato GENERICO fin dalla Fase 1 → una "partita torneo" è semplicemente un **event** Match Day il cui slate = i giocatori di 2 nazioni, con un esito che fa avanzare il tabellone. Riuso massimo, zero duplicazione.

**Guardrail IP (D1.3 — vale per le nazioni):** nomi/bandiere/colori nazione **originali e generati**; vietato l'eco di nazioni reali e qualsiasi riferimento a "Mondiale/FIFA/Europei". Riuso `BANNED_*` token + generazione deterministica (come `fictional_roster.py`). Bandiere = **stemmi geometrici generati** (come `TeamBadge`), MAI bandiere reali.

---

# PARTE A — MATCH DAY #2 (piano a fasi, leva per ultima)

**Riuso:** `feed.round_performance` (deterministico per `(atleta, round_idx)`), `surprise_pct`/`apply_tick`/`market_price`, claim atomico idempotente (`_claim_round`), `execute_buy/sell` (già atomici), analytics leaderboard, scheduler, identità Luxury (BentoCard/finestre lime).

**Modello prezzi:** CONDIVISO — i tick-evento muovono i prezzi REALI degli atleti dello slate → trading live riusa buy/sell invariati. Durante un evento LIVE lo slate è ESCLUSO dal round globale.

### Fase 1 — Backend: EVENT generico + slate + tick + API stato (NO leva, NO premi)
- Modello `events{_id, kind:'friendly'|'tournament_match', tournament_id?, match_meta?, status:'scheduled'|'live'|'closed', slate[], opens_at, closes_at, current_tick, last_tick_at, seq}`. **`kind`/`tournament_id` rendono l'event riusabile dal torneo fin da subito.**
- `open_event` (claim atomico, 1 solo live per scope), `run_event_tick` (riusa feed→surprise→tick→price, scopato allo slate, `round_idx` dedicato `seq*100000+tick`, guardia idempotente `min_gap`; `price_history` reason=`match_day` + `event_id`), `close_event`.
- Round globale esclude lo slate mentre LIVE.
- API `GET /api/match-day/current`.
- **Test:** open idempotente, tick idempotente, prezzi solo slate, close.

### Fase 2 — Frontend: schermata Match Day (display)
- Agganciata all'hero "IN ARRIVO" del bento → countdown/LIVE, partite, prezzi e P&L live (read-only). Luxury, responsive. Riuso BentoCard/Sparkline/StatTile, polling `current`.

### Fase 3 — Trading live + leaderboard evento
- Trading live = `execute_buy/sell` invariati (gating "solo durante LIVE" lato API).
- `GET /api/match-day/leaderboard` (P&L nella finestra; riuso analytics).
- **Test:** P&L finestra, ranking, gating temporale.

### Fase 4 — Premi top-5 (idempotente)
- A `close_event`: top-5 per metrica (vedi decisioni), accredito € fittizi (riuso wallet credit) con flag atomico `prizes_settled` → no doppio su redeploy.
- **Test:** ranking, importi, idempotenza accredito, soglia minima.

### Fase 5 — Leva x2 "Boost" (per ultima, più delicata)
- Strumento dedicato: stake S bloccato; payoff `max(0, S·(1+2·move))`; max perdita = S; nessun prestito/margin/saldo negativo. Idempotente al settle.
- UI linguaggio "abilità/sfida".
- **Test:** payoff +/−/floor 0, max loss = stake, no saldo negativo, idempotenza.

---

# PARTE B — LAYER TORNEO (una pagina, si appoggia sopra Match Day)

Il torneo **non duplica** il motore: orchestra molti **event** Match Day (uno per partita) + logica tabellone.

### T1 — 48 nazioni inventate + rose per ruolo (backend, additivo)
- Generatore sintetico deterministico (seed): 48 nazioni con **nome originale**, **colori** (primario/secondario), **stemma geometrico** generato (no bandiere reali). Riuso `BANNED_*` + pool nomi per coerenza, **nessuna nazione reale**.
- **Rose per ruolo:** ogni nazione ha una rosa di giocatori finti. Engine prezzi resta su macro-ruoli `POR/DIF/CC/ATT` (coeff. Gioco 5 invariati); aggiungo un campo **display** `position` (POR, DC, TD/TS, CC, ala dx/sx, ATT) SOLO per esposizione UI per ruolo. Riuso nomi per-nazionalità.
- Persistenza `tournament_nations`, `tournament_squads`. Seed **idempotente**.
- **Test:** 48 nazioni uniche, nessun token reale, rose complete per ruolo, idempotenza seed.

### T2 — Tabellone + calendario (backend)
- Modello `tournaments{_id, status, format}` + `tournament_groups` (12 gironi×4) + `tournament_matches` (girone→R32→R16→QF→SF→F). Sorteggio deterministico per seed.
- **Calendario/ritmo:** più partite al giorno (gironi), accelerato; lo scheduler apre/chiude gli **event** per ciascuna partita secondo il calendario (riuso APScheduler + guardie idempotenti). Standings di girone (punti/diff reti) calcolati dagli esiti.
- **Test:** struttura 48→32→…→1, calendario coerente, standings, idempotenza avanzamento.

### T3 — Partita = EVENT Match Day (collante)
- Per ogni `tournament_match`: si crea un **event** (`kind='tournament_match'`, `tournament_id`, slate = giocatori delle 2 nazioni). Durante la finestra: prezzi live + trading + (premi/leva ereditati da Match Day).
- **Esito partita** derivato dal motore: aggregazione sintetica degli eventi-gol della finestra → risultato (es. 2–1) → **avanza il tabellone** in modo **idempotente** (flag `result_settled`). Nessun dato reale.
- **Test:** esito deterministico dalla finestra, avanzamento bracket idempotente.

### T4 — UI Torneo nel bento (frontend, Luxury)
- Card hero "Torneo" (prossima/partita LIVE + countdown), **tabellone** (gironi + albero eliminazione), **partite di oggi**, **standings**, **mio P&L torneo**. Finestre lime, oro, Manrope, responsive (mobile = sezioni impilate).
- Riuso BentoCard/StatTile/Sparkline/TeamBadge (→ versione "nazione" con stemma geometrico).

---

# PARTE C — DECISIONI DA APPROVARE

1. **Leva x2 (downside cappato) → strumento "Boost x2" dedicato.** Stake S bloccato; payoff `max(0, S·(1+2·move))`; max perdita = S; nessun prestito/margin/saldo negativo. *Raccomando.* (NON leva sulle quote reali = richiederebbe prestito.)
2. **Metrica premio top-5 → % di rendimento sul capitale impiegato nell'evento**, con **soglia minima di capitale** per qualificarsi (anti stake-minuscolo-fortunato). Più equa per portafogli piccoli. *Raccomando %* (assoluto favorisce i grandi).
3. **Cadenza/durata → finestra 20 min, tick ogni 15 s (~80 tick), config-driven** (`MATCHDAY_WINDOW_MIN/TICK_SEC/GAIN`). Vivo ma non caotico. Nel torneo (gironi) più finestre/giorno in sequenza.
- *(Torneo)* **Esito partita = aggregazione sintetica della finestra**; **avanzamento bracket idempotente**. Scheduling automatico via scheduler (no ops), con trigger interno on-demand per test.

---

# NOTE
- Vincoli: solo sintetico; test nuovi per ogni logica; guardie idempotenti su tick, premi, leva, esito/avanzamento torneo; Luxury responsive; aggiornare PROJECT_SPEC/ROADMAP/DESIGN_SYSTEM per fase.
- Store/legale: leva+premi → linguaggio "abilità/sfida", mai "scommessa/vincita". Modello pulito (€ fittizi, no cashout, downside cappato). Niente "Mondiale/FIFA".

# ADDENDUM — News thumbnails (richiesta separata, "Fase 2 dopo fase 1")
Polish indipendente sulla colonna "News del giorno" del bento: ad ogni card una **thumbnail astratta** (blocco/gradiente carbone-oro + icona calcistica, **generata, nessuna foto/logo reale**), in alto o a sinistra del titolo; fonte in oro + titolo invariati; bordo finestra lime resta sulla CARD contenitore (non sulle singole news). Responsive, niente hex nuovi, test verdi. **Non Match-Day**: la schedulo come task UI a sé, da fare dopo la Fase 1 Match Day (o come quick-win separato se preferisci).
