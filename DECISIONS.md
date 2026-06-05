# DECISIONS — PlayerStock

Log decisionale. Append-only: nuove decisioni in fondo. La spec di prodotto è in `PROJECT_SPEC.md`.

---

## D0 — Fase 0 (2026-06-04, Claude Code)

### D0.1 — Divisione del lavoro (override CLAUDE_CODE_PROMPT.md)
`CLAUDE_CODE_PROMPT.md` (generato da Emergent) assegnava a Claude Code **tutte le 9 fasi**:
**ERRATO**. Vale la divisione di `Prompt per Emergent.md` + `Roadmap progetto.md`:
- **Claude Code**: Fase 0 (setup+spike) · 2 (valuation+pricing+test) · 3 (order book) · 5 (reward) · 8 (anti-cheat).
- **Emergent**: 1 (auth/dati/seed/i18n) · 4 (economia+portfolio) · 6 (engagement) · 7 (abbonamento+ads) · 8b (polish UI).
- Mai cambiare strumento a metà fase. Handoff a ogni confine di fase.

### D0.2 — Override spec funzionale → DECISIONI FINALI
La vecchia spec funzionale (`Prompt per Emergent.md` §5–6) divergeva. **Vincono** le decisioni
finali di `CLAUDE_CODE_PROMPT.md` §2, riportate in `PROJECT_SPEC.md` §2:

| Parametro | Vecchia spec | **Decisione finale** |
|---|---|---|
| Float quote | 10.000 | **1.000.000** |
| Prezzo base | ValoreIniziale/10.000 (banda 20–500 cr) | **0.01 Credito** (valore base 10.000) |
| Cap utente | 5–10% | **3%** (30.000 quote) |
| Auth | email/Google/FB/Telegram | **solo Google OAuth** |
| Dati | roster fittizi simulati | **reali Football-Data.org + anonimizz. L2** |

Driver pricing (gol/assist/voto/minuti/clamp) coincidono tra i documenti → confermati.

### D0.3 — `Gioco 5.xls` NON versionato
Il file `Gioco 5.xls` (modello pricing del fondatore, pesi proprietari) **non entra nel repo**
(know-how riservato — vedi D0.6 IP). Resta fuori in `C:\Gioco Calcio\`. I valori esatti dei
driver vengono **estratti in `pricing_constants.py` / `valuation_constants.py` in Fase 2**.
Aggiunto a `.gitignore`.

### D0.4 — Layout repo
Repo in sottocartella pulita `C:\Gioco Calcio\PlayerStock\`. File di input (`*.md`, `*.xls`,
`Base Progetto/`) restano **fuori** dal repo. Branch principale `main`. Repo GitHub **privato**.

### D0.5 — Spike mining Acki Nacki (risolve rischio compat RN)
Spike eseguito leggendo il repo reale approvato AN `Ale1950/listen-and-mine-acki-nacki`.
Findings completi in `docs/spike_bee_sdk.md`. Sintesi:
- Implementazione reale = **web React + Vite** (TMA), **non** RN nativo.
- SDK reale = **`bee_sdk` WASM self-hostato** (build Mining Hub) + **`@eversdk/core`/`lib-web`**
  per letture on-chain. (Il `@teamgosh/bee-sdk@0.1.0` npm aveva un bug `submit_session_root`.)
- **Decisione**: in PlayerStock (Expo/RN) il miner gira in **WebView** che carica il bundle web,
  dietro `RewardProvider`. Niente porting nativo. Riuso wrapper pulito in Fase 5, no copia-incolla.
- Sicurezza verificata: il codice usa **solo mining key** (`gen_mining_keys` → public/secret) +
  deep link all'AN Wallet; **nessun seed/mnemonic, nessuna chiave di spesa**. ✓

### D0.6 — IP strategy (da `Brief_per_avvocato.md`, sintesi non legale)
Il **metodo è l'asset**. Tutele candidate (da validare con legale):
- **Segreto commerciale** su pesi/costanti/tabelle di calibrazione (→ `Gioco 5.xls` fuori repo,
  costanti come know-how riservato).
- **Copyright** sul codice sorgente.
- **Marchio** su nome "PlayerStock" + logo.
- **Data certa**: repo privato + commit (eventuale firma/timestamp da valutare).
- **NDA** verso fornitori/sviluppatori/partner (incluso AN) prima di condividere formule.
- Valore calcolato con **formula propria** su metriche osservabili → non copia valori
  proprietari altrui (riduce rischio banche dati "sui generis", es. Transfermarkt).

### D0.7 — Anonimizzazione L2 + disclaimer (compliance, da Brief)
Roster anonimizzati L2 (iniziali + nazionalità + ruolo + età + squadra fantasy), nome reale solo
DB interno. Disclaimer obbligatorio in T&C/landing/footer Home (testo in `PROJECT_SPEC.md` §2).
Due economie separate, Crediti senza cash-out → argomenti a favore di "gioco di abilità"
(qualificazione da confermare col legale). Dettaglio in `docs/compliance.md`.

---

## D1 — Fase 1 (2026-06-05, Claude Code)

### D1.1 — Seed roster: giocatori FITTIZI realistici (Opzione 3 raffinata)
Il roster dei 400 giocatori è **generato fittizio ma realistico**, NON dati reali e NON
placeholder grezzi. Override del D0.2 ("Dati = reali Football-Data.org") **limitatamente ai
nomi dei giocatori** in Fase 1 (le squadre restano mappate L2 come da spec).

Caratteristiche:
- ~400 giocatori inventati ma plausibili: nomi coerenti per nazionalità, età realistiche,
  composizione **2 POR + 6 DIF + 6 CC + 6 ATT** per ciascuna delle 20 squadre fantasy.
- **Nessuna persona reale**: i nomi sono combinazioni casuali (seed deterministico) di pool
  per-nazionalità → nessun rischio diritti d'immagine / banca dati altrui.
- **File seed statico nel repo**: `backend/app/data/serie_a_roster_fittizio.json`
  (rigenerabile con `python -m app.cli.generate_fictional_roster`).
- Il seeder (`seed_roster`) legge da lì: **niente token Football-Data per i giocatori**.
  Default `DATA_PROVIDER=fictional_roster`. Provider reale (`football_data_org`) resta
  disponibile via `--source football_data_org` per uso futuro.
- **Anonimizzazione L2 gira comunque** a valle: `internal_full_name` solo nel DB, le response
  espongono solo `display_*` (iniziale + cognome troncato + nazionalità + ruolo + età + squadra).

Motivazione: sblocca Cancello 1 senza dipendere da Q3/Q7 (token + completezza roster reale),
riduce rischio legale sui nomi, mantiene il modello dati e la pipeline di anonimizzazione
identici a quelli che useranno i dati reali. Vedi `app/data_providers/fictional_roster.py`.

### D1.2 — Cancello 1 (fine Fase 1): NON richiede reward testnet
Chiarimento al ROADMAP §"3 cancelli": il reward NACKL su testnet è **Fase 5**, non Fase 1.
Il gate per chiudere Fase 1 → Fase 2 è **solo "MVP core gira"**:
- backend su Atlas (`DB_NAME=playerstock`), endpoint `/api/health` `/sports` `/teams` `/players` OK;
- seed popola **400 atleti fittizi** (D1.1);
- **nessun `internal_full_name`** nelle response (anonimizzazione L2);
- i **test base verdi** (suite `backend/tests/`).

Quando verde → Cancello 1 passato → Fase 2 (valuation/pricing da `Gioco 5.xls`, vedi D0.3).

---

## D2 — Fase 2 (2026-06-05, Claude Code)

### D2.1 — Driver di pricing estratti da `Gioco 5.xls` / "Serie 1"
Estratti gli 11 driver (minuti, gol fatti/subiti, ammonizione, espulsione, assist, rigori
segnati/sbagliati/parati, voto portiere, autorete) × 4 ruoli × bande, + clamp settimanale
per ruolo. Strumento `backend/tools/extract_gioco5.py` (committabile: legge l'xls esterno,
nessun valore proprietario al suo interno). Valori in `config/pricing_constants.py` (`DRIVERS`,
`RANGE_CLAMP`). `tests/test_gioco5_golden.py` rilegge l'xls (se presente) come guard anti-drift.
Engine: `app/pricing/` (drivers→performance→engine `apply_tick`) e `app/valuation/` (engine).

### D2.2 — Calibrazione K_GLOBAL + tuning spread (~8x)
`K_GLOBAL=10.000` (neutro ≈ 0.01). Fattori (ruolo/età/minutaggio/squadra/score) **compressi**
per stare nella banda decisa [0.005, 0.050]. **Tuning**: top allargato a ~0.035 alzando SOLO gli
upper bound (base ATT, premio età giovane, squadra top) — il floor 0.005 è indipendente e resta
intatto. Esito: min ≈ 0.00507, max ≈ 0.03505 (spread ≈ 7x). Fasce: riserve 0.005–0.010, medi
0.010–0.022, top 0.030–0.040. (score capato a 2.0 da spec → top fermo ~0.035; per superarlo
servirebbero moltiplicatori distorti.)

### D2b — Input SINTETICI per dar vita al motore (MVP)
`score_performance`, `fattore_squadra` (tier) e `minutaggio_pct` dei 400 giocatori fittizi sono
**sintetici e DETERMINISTICI** (hash dell'identità giocatore/squadra → `app/valuation/synthetic_score.py`):
**segnaposto**, nessuna pretesa di accuratezza, da **sostituire con statistiche reali** quando
disponibili. Servono solo a rendere i prezzi iniziali VARIATI (non più tutti 0.01) e a muovere la
borsa. `cli/seed_roster.py` li cabla nel valuation engine (prezzi in banda + audit fields nel doc).
`cli/simulate_rounds.py` genera N giornate sintetiche → `apply_tick` → collezione `price_history`
(sparkline) — utile anche per testare la Fase 3 senza utenti reali.

---

## ❓ DOMANDE APERTE (da risolvere col fondatore / terzi)

| # | Domanda | Per chi | Blocca fase |
|---|---|---|---|
| Q1 | **APP_ID di listen-and-mine (`0x00…01`) è riusabile per PlayerStock, o serve registrare un app_dapp_id separato presso Acki Nacki?** L'approvazione AN di listen-and-mine **non** estende automaticamente a PlayerStock. | Acki Nacki | Fase 5 |
| Q2 | Google OAuth Client ID/Secret — ✅ forniti, nel `.env` locale (NON nel repo) | Fondatore | Fase 1 |
| Q2b | **Google OAuth redirect URI**: ora PLACEHOLDER `http://localhost:8001/api/auth/google/callback`. Sostituire con l'URI di callback reale quando si implementa l'auth, e aggiornarlo in Google Cloud Console → Auth Platform → Client. | Claude/Emergent | Fase 1 |
| Q3 | Football-Data.org API token | Fondatore | ~~Fase 1~~ → **non blocca** (roster fittizio D1.1); serve solo per passare a dati reali |
| Q4 | MongoDB connection string (locale o Atlas) + Redis | Fondatore | Fase 1 |
| Q5 | Mining key / wallet di test AN (shellnet) | Fondatore/AN | Fase 5 |
| Q6 | Qualificazione giuridica (gioco vs strumento finanziario vs azzardo) | Legale | pre-lancio |
| Q7 | Football-Data.org dà roster completi o serve fallback Wikipedia? | da verificare | ~~Fase 1~~ → **non blocca** (roster fittizio D1.1); rilevante solo al passaggio a dati reali |
