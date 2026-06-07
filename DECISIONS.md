# DECISIONS — PlayerStock

Log decisionale. Append-only: nuove decisioni in fondo. La spec di prodotto è in `PROJECT_SPEC.md`.

> **Manutenzione documenti (regola di processo)**: ogni fase/decisione aggiorna i documenti canonici
> **nello stesso PR** (un PR non è completo senza). Mappa: **DECISIONS** = scelte · **PROJECT_SPEC** =
> architettura/prodotto · **ROADMAP** = fasi · **DESIGN_SPEC** = design system.

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

### D1.3 — Nomi realistici per nazionalità + guardrail IP (2026-06-07, Claude Code)
I nomi dei 400 giocatori sono realistici e **coerenti per nazionalità** (pool per-nazione in
`fictional_roster.py`, combinazione casuale deterministica). Rafforzato il guardrail IP:
- **Pool ripuliti dai big noti**: rimossi i token DISTINTIVI di calciatori famosi ATTUALI
  (es. Lautaro, Vinicius, Domagoj, Lewandowski, Kovacic, Kelechi, Onyekuru), sostituiti con
  nomi comuni non famosi. `BANNED_REAL_PLAYER_TOKENS` documenta i rimossi.
- **Principio**: vietato l'**eco DELIBERATO** di calciatori reali (niente mapping voluto
  squadra-per-squadra né storpiature fonetiche). Le **coincidenze casuali con nomi poco noti
  restano ammesse** (innocue) — NON serve una blocklist esaustiva (i pro sono migliaia).
- **Rename in-place** dei nomi pre-esistenti che echeggiavano un big: `python -m
  app.cli.rename_real_player_echoes` (deterministico per-ID `source_external_id`, NON ri-seeda;
  tocca solo `internal_full_name` + `display_*` + `updated_at`; allinea anche il seed JSON).
  Applicato: 3 giocatori (Lautaro Acosta→Tomas Sanchez, Domagoj Knezevic→Karlo Bozic,
  Domagoj Novak→Luka Kovacevic). Ruolo/nazionalità/squadra/stat/valori/prezzi/holdings intatti.

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

## D3 — Fase 3 (2026-06-05, Claude Code)

### D3.1 — Modello prezzo: quotazione + book (NON CLOB)
Il prezzo è guidato dalla **formula** (perf% + mercato% + eng%, clamp+floor): è la quotazione
ufficiale. Gli scambi avvengono **al prezzo di quotazione corrente**, non a prezzi limite. Il
flusso ordini muove la quotazione via **mercato%** al tick successivo. (Un CLOB puro con price
discovery dal book è stato scartato: divergerebbe dalla spec §155/§184.)

### D3.2 — MVP: pool a DUE LATI (casa controparte), order book P2P rimandato
Semplificazione MVP: la **casa** è sempre controparte sia in acquisto sia in vendita, al prezzo
di quotazione (buy ×(1+3.5%), sell ×(1−3.5%)). **Droppati per ora**: order book P2P, ordini
limite, matching ask/bid (feature futura). Motivi: liquidità sempre garantita (niente vendite
bloccate con pochi utenti), molto più semplice, e nel modello a quotazione il book non fa price
discovery → complessità senza valore per l'MVP. La casa ha crediti virtuali illimitati (sempre
controparte, incassa le fee). **Scarsità preservata**: float = `primary_pool_qty` + `circulating_qty`
= 1.000.000; il pool può esaurirsi (sold out). Buy: pool↓ circolante↑. Sell: pool↑ circolante↓.

### D3.3 — Regole mercato
Fee 7% totale (3.5% buyer + 3.5% seller) → `house_account` (sink economia). Cap utente **3%**
(30.000 quote/atleta). **Holding minimo 7 giorni** (anti-flip), consumo lotti **FIFO**. `mercato%`:
net flow finestra per atleta → bucket (1-5/6-20/>20 → ±1.2/2.0/2.5%) → `apply_tick` → `price_history`.
Moduli `app/market/` (rules, trade, market_pct) + route `/api/market/*` (orders, holdings, quote).
Collezioni: `holdings` (lotti), `orders`, `trades`, `house_account`. NOTA: scritture trade
sequenziali in MVP (mongomock no-tx); in produzione su Atlas avvolgere in transazione multi-doc.

---

## D5 — Fase 5 (2026-06-05, Claude Code)

### D5.1 — Architettura RewardProvider a 2 strati
ABC `RewardProvider` (`can_earn`/`accrue`/`balance`/`provider_name`, +`is_placeholder`).
Due implementazioni: `InternalRewardProvider` (DB, completo, MVP) e
`TestnetWalletRewardProvider` (Acki Nacki shellnet) **scaffold INERTE** (no-op robusto)
finché Q1/Q5 non sciolte. Selezione via `REWARD_PROVIDER=internal|testnet`. Moduli
`app/reward/` (base, internal, testnet, heartbeat, wallet, service, factory) + route `/api/reward/*`.

### D5.2 — Il NACKL interno è un PLACEHOLDER, non NACKL reale
Il NACKL reale è **emesso dal protocollo** (no pre-mine; l'app non lo crea). Quindi l'accrual
dell'`InternalRewardProvider` (`is_placeholder=True`, `source="internal_placeholder"`) è un
**segnaposto dev/MVP**: NON va presentato come "NACKL guadagnato reale". Quando Q1/Q5 si
sciolgono, il saldo reale = ciò che il miner mina, letto **on-chain via GraphQL** dal
`TestnetWalletRewardProvider` — concettualmente distinto dal placeholder.

### D5.3 — Accrual via heartbeat firmato, legato all'attività, cap conservativo
Accrual placeholder = `base_per_beat` (passivo, piccolo) + `per_activity × attività osservata
dal server` (ordini reali nella finestra) — limitato dal **cap giornaliero conservativo**
(`REWARD_DAILY_CAP_NACKL`, default 50). Heartbeat firmato **HMAC+nonce** con anti-replay e
rate-limit. ⚠️ **Farmabile**: l'HMAC con secret lato client è estraibile (decompilazione) → il
cap è l'unica vera protezione ora; legare all'attività osservata riduce la falsificabilità.
**Da indurire in Fase 8** prima di qualsiasi valore reale. Wallet connect accetta **solo la
mining PUBLIC key** (rifiuta seed/mnemonic/chiavi di spesa — test essenziale).

### D5.4 — WebView miner rimandato; schermata Reward viva
Il miner vero (bundle web listen-and-mine in WebView, `bee_sdk` WASM + `@eversdk`) **dipende da
Q1/Q5** → rimandato (niente scaffold inerte lato miner). Costruita però la **schermata Reward**
funzionante: saldo (provider interno, etichettato placeholder), wallet/connect (public key,
QR/deep link "in arrivo"), stato "mining in arrivo".

---

## D3b — Prezzo IBRIDO: impatto trading + rientro (2026-06-05, Claude Code)

### D3b.1 — Modello prezzo IBRIDO (formula = àncora, il trading muove la deviazione)
Evoluzione di D3.1/D3.3: il prezzo di mercato è **àncora-formula × (1 + deviazione)**.
- **prezzo_equo (àncora)** = ValoreIniziale/float; si muove col **rendimento** (perf%, Fase 2). Invariato.
- **deviazione** (scalare per atleta, parte da 0): buy di q quote → `+= k×(q/float)`; sell → `-= k×(q/float)`.
- **rientro LAZY (mean reversion)**: `deviazione_ora = deviazione_ultima × e^(-λ·Δt)`, calcolato **alla lettura**
  (nessun job sempre attivo, sempre coerente).
- **prezzo_mercato** = `clamp(prezzo_equo × (1+deviazione_ora), floor, tetto)`; floor = 10% prezzo iniziale;
  tetto = `prezzo_equo × (1+cap)`.
- Il banco quota a **prezzo_mercato**, poi ±3,5% fee. **Cap 3% e holding 7gg invariati.**

Sostituisce il `mercato%` a net-flow/bucket (D3.3) come driver dell'impatto trading: ora è **continuo**
(deviazione) con rientro, non un tick a scaglioni. Stato persistito per atleta: `prezzo_equo_crediti`,
`deviazione`, `deviazione_ts` — aggiornati nella **stessa transazione atomica** dell'ordine. `price_history`
riceve il punto post-trade + **snapshot periodici** (30 min, scheduler) per mostrare il rientro nella
sparkline. Moduli: `app/market/hybrid_pricing.py` (puro) + `app/market/trade.py`. Test
`tests/test_hybrid_pricing.py`.

### D3b.2 — Parametri (tarati via simulazione, vedi DT)
- **k_impatto = 1.5** → un ordine al cap utente (30.000 = 3% del float) muove la deviazione di **+4,5%**
  (dentro il tetto 0,40). Tarato da 1.0→1.5: a 1.0 il trading era trascurabile vs il rendimento.
- **λ = ln2 / 3h** → **emivita deviazione 3 ore** (rientro "in poche ore").
- **cap deviazione = ±0.40** → anti-fuga (servono ~13 ordini-cap consecutivi senza decadimento per arrivarci).
- **floor = 10%** del prezzo iniziale (invariato).
Costanti in `config/pricing_constants.py`.

---

## DT — Ritaratura economica (2026-06-05, Claude Code)

### DT.1 — `simulate_rounds` esteso (rendimento + pressione trading) + report
`app/cli/simulate_rounds.py`: `apply_rendimento_round` (il rendimento muove l'àncora e ricompone con la
deviazione) + `simulate_economy` (rendimento + trader simulati che comprano/vendono entro cap/holding).
Report deterministico `tools/economy_report.py` (mongomock) su 30/60/90 gg. **Esito (90gg, 30 trader):**
deviazione max ~0,017 ≪ cap 0,40 (nessuna fuga), floor mai toccato, banda prezzo ~1,15–1,91× iniziale
(il rendimento domina), fee sink ~6.000 cr attivo → **l'economia tiene**.

### DT.2 — Budget 10.000 cr e cap 3%: MANTENUTI, budget da rivedere (APERTO)
Con 10.000 cr l'utente copre ~13–18 ordini-cap al prezzo medio → il **cap 3% non morde** molto. Budget e
cap **restano invariati per ora**; la revisione del budget va fatta **dopo** aver disegnato guadagni/sink
(faucet engagement). Vedi DOMANDE APERTE.

---

## D6f — Faucet CREDITI da engagement (PROGETTAZIONE) (2026-06-05, Claude Code)

### D6f.1 — Principio DUE ECONOMIE ribadito: nessun ponte NACKL→Crediti
NESSUN ponte tra NACKL e Crediti (§0 spec). Un eventuale **guadagno parallelo in Crediti** ha sorgente
**ENGAGEMENT** (non NACKL), su **ledger separati**. L'azione di engagement accredita SIA NACKL (esistente,
placeholder) SIA Crediti (nuovo) ma su **path INDIPENDENTI e idempotenti** — niente split-brain
(problema già visto in Fase 6, vedi commit `0f3e635`).

### D6f.2 — Faucet a scaglioni — APPROVATO e APPLICATO
Conversione engagement→Crediti a **scaglioni marginali**: tier1 ×3 · tier2 ×1,5 · tier3 ×0,75 · tier4 ×0,2
(forma decisa dall'utente). "1 unità di engagement" (EP) = magnitudine reward di Fase 6 (quiz 0,5/risposta
corretta · streak 1→2,2/giorno · pronostico 2,5).
**Valori APPROVATI:** base **0,25 cr/EP** · soglie EP **[50, 200, 500]** · **cap 5 cr/giorno/utente**
(`FAUCET` in `app/economy/credit_faucet.py`). Simulazione (faucet+rendimento+trading): a 90gg crediti
iniettati < fee drenate (net **−1.801 cr** → niente inflazione netta), bonus medio **~138 cr/utente**
(1,4% del budget). Meccanismo + TDD: `credit_faucet.py` (pura `tiered_credits` + accrual **idempotente**
per `event_id` su `engagement_credit_grants`/`wallet_transactions`; NON tocca `nackl_ledger`/`reward_balances`),
`tests/test_credit_faucet.py`.

### D6f.3 — Wiring nei gestori engagement (applicato)
`grant_engagement_credits` chiamato **accanto** all'accredito NACKL esistente, su ledger indipendenti
(niente split-brain), con `event_id` STABILE:
- `claim_daily_streak` → `event_id = f"streak:{user_id}:{YYYY-MM-DD}"`, EP = reward streak.
- `submit_quiz_attempt` → `event_id = f"quiz:{user_id}:{quiz_id}"`, EP = reward quiz (solo se >0).
- `settle_expired_predictions` → `event_id = f"prediction:{prediction_id}"`, EP = 2,5 (solo se vinta).
La risposta dei gestori espone `credit_bonus`. TDD wiring: `tests/test_engagement_faucet_wiring.py`
(idempotenza per `event_id`, NACKL intatto).

---

## DD — Backbone dati + P&L realizzato (2026-06-05, Claude Code)

### DD.1 — Calcolo INTERNO (giocatori fittizi → niente dati web sui giocatori)
Ribadito D1.1: i giocatori dell'MVP sono **fittizi**; statistiche e aggregati sono **calcolo interno**.
Nessun dato web sui giocatori (Football-Data.org resta solo per fixture/calendario, non per i giocatori).

### DD.2 — Endpoint aggregati `/api/stats/*`
Nuovo modulo `app/modules/stats/`: `GET /api/stats/market` (cap totale, volume 24h/7d, attivi, top
gainers/losers, più scambiati, distribuzione prezzi per ruolo), `/api/stats/athletes/{id}` (market cap,
var 24h/7d, max/min, volume, **n° possessori**, scostamento prezzo vs equo, scomposizione valore
score/ruolo/età/minuti/squadra), `/api/stats/me` (equity, P&L realizzato/non, allocazione ruolo/squadra,
best/worst, fee totali, flusso crediti). Volume dagli `orders`, possessori dagli `holdings` (già tracciati).
Test `tests/test_stats.py`.

### DD.3 — P&L realizzato FIFO tracciato
`execute_sell` registra `cost_basis_sold` + `realized_pnl` (FIFO sui lotti) sull'ordine di vendita.
Helper puro `consume_lots_fifo_with_cost` (`app/market/rules.py`).

---

## DG — Direzione DESIGN (decisa; dettaglio in `DESIGN_SPEC.md`) (2026-06-05)

Direzione visiva decisa (il **design pass** la implementa schermata per schermata):
- **Primario CYAN/TEAL** (sostituisce l'oro), **secondario viola**, neon multi-colore su quasi-nero.
- **Intensità MISTA**: sobrio sulle schermate dati / vivido su reward-engage.
- Tema **scuro + chiaro** con toggle; texture geometrica sottile; bordi colorati sottili.
- Tipografia: titoli **Space Grotesk**, dati/numeri **JetBrains Mono**, corpo **Inter**, accento serif **Fraunces**.
- NACKL sempre etichettato **placeholder interno** finché Q1/Q5 aperti.
Stato: token + theme provider (scuro/chiaro) + chrome globale già in repo (parte 1); rifinitura per-schermata
= passaggio finale. Sorgente di verità del design: **`DESIGN_SPEC.md`**.

---

## DR — Web target responsive + analytics portafoglio (2026-06-06, Claude Code)

### DR.1 — WEB è un target → UI RESPONSIVE
Il web è ora target di prima classe. UI **responsive**: primitivo riusabile `ResponsiveTable<T>` (tabella a
colonne **ordinabili** su desktop ≥760px, **card** su mobile) + `useResponsive`. Applicato a Mercato e
Portafoglio (DESIGN_SPEC.md §6b). Identità squadra: `TeamBadge` (colori reali) + bandiera (`flagEmoji`).

### DR.2 — Analytics portafoglio (`/api/stats/me/analytics?period=1S|1M|3M|all`)
Equity nel tempo **ricostruita** da price_history × holdings correnti + cassa (approssimazione MVP: holdings/
cassa costanti sulla finestra), **bucket adattivo** giorni/settimane. Indici PURI (`app/economy/indices.py`):
rendimento · volatilità · max drawdown · beta vs indice di mercato · Sharpe-like. **Confronti**: posizione vs
miglior giocatore di mercato (overlay grafico); portafoglio vs miglior utente (**solo PSEUDONIMO**, mai nome
reale). Test `test_indices.py` (11) + `test_analytics.py` (3).

### DR.3 — Stat sportive sintetiche + backfill storico (placeholder dev)
Stat sportive sintetiche coerenti con score+ruolo (`app/valuation/synthetic_stats.py`, DD) esposte in
`/players` (compatte) + `/stats/athletes/{id}` (complete). `price_history` aveva ts ravvicinati (simulate_rounds
stampa `utc_now()` per tutti i round) → serie temporali collassano: `tools/backfill_price_history.py` ricostruisce
~30 punti/giorno con ts spalmati (ADDITIVO, `reason="backfill"`, NON tocca prezzi/holdings/economia). Going-forward
corretto = snapshot prezzo/equity giornaliero (scheduler) o simulate_rounds con ts distribuiti.

### DR.5 — TECH-DEBT (Fase 8): `/api/users/me` 500 con email non-standard
`UserPublic` usa Pydantic `EmailStr` → utenti con email a TLD riservato (`*.local`/`*.test`/`*.example`,
es. account di test) fanno **500** su `/api/users/me`, che rompe il bootstrap auth (e in browser appare come
errore CORS perché la risposta 500 non porta gli header CORS). **Tech-debt da sistemare in Fase 8/hardening**:
o rilassare la validazione email (accettare/`try` graceful), o normalizzare gli account di test. Per ora,
gli strumenti di screenshot scelgono un holder con email valida.

### DR.6 — Classifica con stat finanziarie (solo pseudonimi)
`/api/stats/leaderboard-analytics?period=` → per utente: patrimonio · rendimento% · ROI vs indice di mercato ·
win-rate (vendite in profitto) · volatilità · trend equity. Ordinabile per metrica. **Mai nome reale**
(`anonymize_display_name`, riga "TU" evidenziata via flag `is_self`). `win_rate` puro in `app/economy/indices.py`.

### DR.7 — Modello azioni "FINITO-DURO" + Valore/Disponibili + order book rinviato
Verificato: il pool del banco è **già finito** per atleta (`primary_pool_qty`, init = float 1.000.000; −buy/+sell;
buy bloccato a 0 con `pool_insufficient`; la vendita NON controlla il pool → sempre possibile). **Decisione
FINITO-DURO** confermata: a 0 disponibili l'acquisto è bloccato ("esaurito sul mercato finché qualcuno non
vende"), la **vendita resta sempre possibile** (il banco ricompra → pool risale). Esposto **disponibili**
(= `primary_pool_qty`) + **% posseduta** + **valore** (= prezzo × float) via `/players` e `/stats/athletes/{id}`.
La **simulazione** gestisce l'esaurimento senza crash (`_trading_step` cattura `APIError`; il buy controlla il
pool prima del decremento → mai negativo) → **nessun accorgimento/ritaratura necessari**.
**Order book P2P RINVIATO** come layer futuro *sopra* il banco (matching tra utenti veri quando la liquidità lo
giustifica); oggi resta il pool a due lati (D3.2). Test `test_market_trade.py::test_sell_works_when_pool_sold_out`.

### DR.4 — Fase "PREZZO GUIDATO DALLA PERFORMANCE" — RINVIATA
Proposta: legare le stat sportive sintetiche al prezzo via i coefficienti `Gioco 5.xls` (`DRIVERS`), così gli
eventi (gol/assist/parate) **muovano il prezzo** come quelli reali. **RINVIATA**: richiede ritaratura economica
(nuovo `economy_report`) e va in una fase "dati reali". Oggi le stat restano **descrittive** (non toccano il
pricing tarato).

---

## DE — Engage: missioni · sfide · quiz mercato (2026-06-06, Claude Code)

### DE.1 — Meccaniche (costruite + TDD)
4 meccaniche, premi su **DUE economie** su LEDGER SEPARATI (Crediti vs NACKL placeholder, niente split-brain):
- **Quiz mercato** (`market_quiz.py`): domande generate dai DATI veri via `/api/stats` (top gainer, ruolo con
  prezzo medio più alto, n° attivi), 1 quiz/giorno idempotente; risposta via flusso quiz esistente.
- **Pronostici**: riuso predictions Fase 6 (su↑/giù↓ a 24h, chiusi sul prezzo reale).
- **Missioni** (`missions.py`): progressione (primo acquisto · diversifica 3 ruoli · tieni 7gg · 15K patrimonio ·
  azzecca 3 pronostici), claim idempotente per (utente,missione).
- **Sfide settimanali** (`challenges.py`): "miglior rendimento" sul periodo (classifica ricostruita), settle
  top-3 idempotente per (settimana,utente).
Endpoint `/api/engagement/overview|missions|missions/{id}/claim|challenge`. Test `test_engage_mechanics.py`.

### DE.2 — Premio CREDITI a importo fisso, DENTRO il cap del faucet (anti-inflazione)
I premi Crediti di missioni/sfide passano da `grant_fixed_credits` (`credit_faucet.py`): importo fisso,
idempotente, **che condivide il CAP GIORNALIERO del faucet** (5 cr/gg/utente). **Conseguenza chiave**: il tetto
giornaliero di Crediti-da-engagement per utente resta **5 cr/gg** *qualunque* sia la combinazione di
EP-faucet + missioni + sfide → **niente nuovo faucet non-cappato**, l'analisi economica resta quella di D6f
(a 90gg iniezione < sink fee). I premi NACKL sono separati (placeholder, non toccano l'economia Crediti).

### DE.3 — VALORI PREMIO — APPROVATI (definitivi)
Missioni: primo_acquisto 5cr+5N · diversifica 8cr+10N · tieni_7gg 8cr+10N · 15K 15cr+25N · oracolo 10cr+15N.
Sfida (top-3): 1° 20cr+50N · 2° 10cr+30N · 3° 5cr+20N.
Sicuri per l'economia: il cap condiviso del faucet (5 cr/gg/utente) limita il totale Crediti-da-engagement a
≤ 450 cr/utente su 90gg (in pratica molto meno) → sotto il sink fee (~6k/90gg, D6f). NACKL placeholder (non
tocca l'economia Crediti).

### DE.4 — News / Eventi di mercato (6ª attività, informativa)
`app/modules/engagement/news.py` → `market_news` nel feed `/engagement/overview` (`news.items`). Da DATI INTERNI
(`market_overview` + stat sintetiche + holdings): top mover settimana con **spiegazione sportiva sintetica**
("2 gol → +7%"), giocatori **ESAURITI**, e news **PERSONALIZZATE** sulle posizioni dell'utente (var ≥ 2%).
**Informativo: nessun premio** → zero carico sul faucet. Test `test_news.py`; smoke Atlas OK.

---

## DH — Resilienza startup backend (2026-06-06, Claude Code)

### DH.1 — Il backend non muore più su un blip Atlas all'avvio (era debolezza nota)
**Diagnosi**: il login web falliva con "Errore di accesso" perché il **backend era morto**: al precedente
avvio Atlas aveva un reset TLS transitorio (`WinError 10054` su tutti gli shard) e il `lifespan` faceva
`ensure_indexes` + `run_all_seeds` **abortendo** → `Application startup failed. Exiting.` → :8001 giù → la
richiesta `/api/auth/google/exchange` non arrivava mai (nessun log lato server). Causa-radice = **connettività
Atlas ricorrente** (M0 free che sfarfalla / rete satura dal mining); Atlas in sé era poi raggiungibile.

**Fix (resilienza)**:
- `app/core/db.py`: client con `serverSelectionTimeoutMS=8000` (fallimento RAPIDO, non 30s) — motor resta
  **lazy** + riconnessione automatica. Nuovo `db_health()` (ok/degraded, non solleva mai).
- `app/main.py` lifespan: `ensure_indexes` + `run_all_seeds` in **try/except con log + CONTINUA** (sono
  idempotenti e Atlas è già seedato → saltarli su un blip è sicuro); `start_scheduler` idem. L'app parte
  **degradata** e si riconnette quando Atlas torna, invece di morire.
- `/api/health` riporta `db: ok|degraded` invece di crashare.
- **Verificato**: avvio con Mongo irraggiungibile (`MONGO_URL=10.255.255.1`) → log "Startup DB init SALTATO …
  modalità degradata" + **"Application startup complete"** (non più "Exiting") + `/health` 200. Con Atlas su →
  `/health {db:ok}`, exchange OAuth raggiungibile, login sbloccato. TDD `test_db_resilience.py`.
- **Perf `GET /api/stats/market` — RISOLTO**: era N+1 (una query price_history × 400 atleti → timeout). Ora
  **una sola aggregazione** (`$match` finestra 24h → `$group` first prezzo per atleta) per la var dei gainers/losers.
  Misurato su Atlas reale: **0,69s** (prima: timeout >15s). Test `test_stats.py::test_market_overview`.

### DH.2 — Rifinitura design globale (token)
Sfondo dark da quasi-nero `#05070A` a **slate-navy `#0E1320`** (più morbido; surface/surfaceAlt ricalibrati);
bordo box da 1px a **`borderW`=1.75** (token globale, i box usano `borderWidth: borderW`) + opacità bordo alzata
(`rgba(255,255,255,0.12)` dark · `rgba(0,0,0,0.14)` light). Cambi puramente nei TOKEN → si propagano a tutte le
schermate. Engage rifatto a **launcher uniformi → pannello dedicato** (DESIGN_SPEC §6b).

### DV.1 — Valore di mercato €M (Fase 2c, layer di display, economia INTATTA)
I 400 giocatori sono FITTIZI: si genera un `market_value_eur` realistico per **forma e scala**
(poche stelle costose, lunga coda di gregari economici, stile Transfermarkt), **deterministico** e
**senza dati esterni**. Solo strato di visualizzazione: prezzo quota, budget 10k, cap 3%, fee 7%,
pricing/valuation/trade **NON cambiano**.
- **Generazione (Opzione B)**: rosa strutturata per squadra → fasce **S/A/B/C/D** (~1/3/6/6/4 su 20)
  assegnate per rank del **talento = `score_performance`** (lo stesso che guida il prezzo); ogni fascia
  ha un range €, posizione entro fascia = score; **livello squadra** (grande/media/piccola da
  `fattore_squadra`) = moltiplicatore = **UNICO scostamento voluto** (premio club: a parità di rank,
  big > piccola). Tutta la calibrazione in `MARKET_VALUE_CONFIG` (un solo punto, ritarabile).
- **Tracking**: valore mostrato = `prezzo_corrente × anchor`, con `anchor = seed / prezzo_iniziale`
  fissata al seed → il valore segue il prezzo (+x% prezzo ⇒ +x% valore) mantenendo la coda del seed.
- **Campi atleta** (deterministici): `market_value_eur_seed`, `mv_anchor_eur` (backfill
  `app.cli.backfill_market_value`, idempotente, tocca SOLO questi 2 + `updated_at`). Esposto come
  `market_value_eur` (corrente) su `AthletePublic` e `athlete_market_stats`.
- **UI**: "**Valore di mercato**" in €M (`formatEuroM`, es. €72,5M) su lista Mercato e Dettaglio,
  **al posto** del vecchio "VALORE" (prezzo×1M in crediti); distinto e separato da "**Prezzo quota**"
  (Crediti). Test `tests/test_market_value.py` (coda pesante spread 150–250x, Spearman valore↔talento,
  effetto club, tracking, determinismo, **regressione** prezzi/cap/fee invariati).
- **Distribuzione reale al seed** (Atlas, 400): min €0,5M · mediana €6,6M · max €83M · **spread 166x**;
  14 sopra €60M, 178 sotto €5M. Parametri di partenza ok, ritarabili dopo osservazione.

---

## D7 — Migrazione a € (valuta unica) (2026-06-07, Claude Code)
La valuta di trading passa da "Crediti" a **€ virtuali**. **Una sola fonte di verità**:
`prezzo quota = market_value_eur / 1.000.000` (l'ancora è il valore €M Fase 2c, coda pesante
€0,50–€115). `value = prezzo × 1.000.000` live (niente più doppia scala Crediti/€).

- **Motore invariato**: deviazione da trading, mean-reversion λ, floor 10%, cap deviazione ±40%,
  driver Gioco 5.xls sono **relativi/%** → scale-invariant. `k_impatto = 1.5` invariato
  (rivalutare 2.0 più avanti se col volume reale il mercato risulta statico).
- **Fondo iniziale**: €1.000.000/utente (`BUDGET_INIZIALE_UTENTE_EUR`).
- **Cap/fee/holding invariati**: 3% (30.000 quote), 7% (3,5+3,5), 7 giorni. *Effetto atteso*: sui
  titoli costosi (€115) il cap 3% (€3,45M) supera il fondo → vincolo di capitale come in un
  mercato vero; il cap-quote morde sui titoli economici.
- **Faucet engagement ×100** (col fondo ×100, stesso peso relativo 0,05%/giorno): `base €25/EP`,
  `cap €500/giorno`; soglie EP e moltiplicatori invariati. Reward fissi missioni/sfide ×100.
- **Reset pulito** (pre-lancio): `python -m app.cli.reset_to_euro` — tutti a €1.000.000, holding
  azzerate, ledger di trading azzerato, atleti ri-ancorati in €. **NACKL separato e INTATTO**.
- **Campi rinominati** `*_crediti → *_eur` (`balance_eur`, `prezzo_*_eur`, `valore_*_eur`,
  `cash_eur`); display prezzo a **2 decimali** (es. €86,30). UI/guida "Come funziona"/i18n in €.
- **Disclaimer**: "simulazione · valuta virtuale (€ simbolici) · nessun valore reale · nessun
  prelievo" (welcome/consent/home/dettaglio).
- **Anti-inflazione ri-verificata** alla nuova scala (`tools/economy_report.py`): a 90gg faucet
  iniettati ~€415k vs fee drenate ~€1,5M → **net −€1,09M (SINK > FAUCET) ✓**.
- L'engine `valuation()` (Cr) resta come legacy NON più nel path prezzo.

---

## D8 — Principio NACKL: solo mining, mai dal gioco (VINCOLO permanente) (2026-06-07, Claude Code)
**Il gioco non regala MAI NACKL.** I NACKL derivano UNICAMENTE dal **mining** — *time-based*, in
funzione del tempo in cui l'account/app resta attivo su una qualsiasi schermata. Il mining è un
**sottosistema SEPARATO** con registrazione propria (**opt-in**), in continua evoluzione (boost e
acquisto boost **da definire**). Il NACKL resta placeholder/inerte fino all'integrazione reale Acki
Nacki (Q1/Q5), separato dai € e **non compra quote**.

- **Engagement disaccoppiato dal NACKL**: le attività (streak, quiz, pronostici, missioni, sfide)
  accreditano **solo €** (faucet `grant_engagement_credits`/`grant_fixed_credits`). Rimossi tutti gli
  accrual NACKL: `service.py` (streak/quiz/prediction), `missions.py`, `challenges.py`; eliminato
  l'adapter `engagement/reward_client.py` (orfano) → engagement non può più accreditare NACKL.
- **Unica fonte di accrual NACKL** = `app/reward/` (heartbeat/mining: `process_heartbeat` →
  `compute_accrual` time-based con cap → `InternalRewardProvider.accrue`). Verificato: nessun altro
  `.accrue()` nel codebase.
- **Copy**: rimossi i riferimenti "NACKL dalle attività" da Engage (intro, toast, premi, CTA),
  guida "Come funziona" (§13) e blocco "Reward · NACKL" dell'Hub €. Premi missioni/sfide = solo €.
- Test: `test_engagement_faucet_wiring` ora assert NACKL = 0 dopo ogni evento engagement.

---

## D9 — Piano MINING NACKL (NON implementare ora) (2026-06-07, Claude Code)
Estende [[D8]]. Definisce COME il NACKL verrà generato quando si farà il wiring reale.

- **Modello**: il **mining è l'UNICA fonte** di NACKL, **time-based** = in funzione del tempo in cui
  l'app resta **attiva e in primo piano**. **Opt-in** (richiede policy Acki Nacki + wallet collegato).
- **Test senza il team AN**: fattibili con un **wallet di TEST self-attivato** seguendo il protocollo
  standard Acki Nacki — non serve coinvolgere il team AN per i primi test.
- **Contatto AN / Eugene: RIMANDATO** a dopo il **parere legale** (nessun contatto prima).
- **Da verificare al wiring (Q1)**: se `bee-sdk` richiede un **`app_dapp_id`** per minare.
- **Guardrail (sicurezza)**: nell'app vive **SOLO la chiave PUBBLICA** (mining), MAI la privata/di
  spesa; il mining è un **sottosistema separato dall'economia €** (non si mischia, non compra quote).
- **Backend**: partirà dal repo **Listen & Mine** (`listen-and-mine`) in una **cartella dedicata**
  del progetto PlayerStock — più avanti.
- **Stato**: scaffold INERTE/placeholder (vedi Fase 5); boost e acquisto boost **da definire**.

---

## D10 — Prezzo guidato dalla performance + feed a innesto (2026-06-07, Claude Code)
*(NB: richiesta come "D9" ma D9 è già il piano mining → registrata come D10.)*

Le **prestazioni muovono il prezzo**: buona prestazione → su, scarsa → giù. È il motore di
vivacità del mercato. Mondo **fittizio** → prestazioni **sintetiche**.

- **Meccanica**: ogni *round* il feed genera gli eventi del giocatore → `performance_pct`
  (coeff. **Gioco 5.xls** `DRIVERS` × `PERF_PRICE_GAIN`, poi clamp `RANGE_CLAMP`) → sposta
  **`prezzo_equo_eur` (ancora)** via `apply_tick` (floor 10%); il prezzo di mercato ricompone la
  **deviazione di trading** decaduta. **Performance = fondamentale · trading = sentiment: separati.**
- **Feed a INNESTO** (`app/pricing/feed.py`): `PerformanceFeedProvider` con unica impl
  `SyntheticPerformanceProvider`. Switch via `PERFORMANCE_FEED`. In futuro, **SE autorizzato**, si
  innesta un adattatore 'real' **senza toccare il motore prezzo**. Nessuna mappa fittizi↔reali ora.
- **Unica fonte di verità**: gli stessi eventi (a) muovono il prezzo e (b) si sommano in
  `season_stats` (mostrate) + `round_events` (citati da News). `synthetic_stats` ora LEGGE l'accumulo.
- **Cadenza CONFIGURABILE** (`ROUND_INTERVAL_MIN`, scheduler): default ATTIVO = **VELOCE (30 min)**
  per mercato vivo in dev; **realistico/prod = settimanale** (10080). `ROUND_ENABLED` on/off.
- **Magnitudine** (`PERF_PRICE_GAIN`): default veloce **2.5×** (movimenti visibili); realistico
  **1.0** (golden invariato). Estremi clampati per ruolo (ATT +2,87/−2,81 · POR +4,24/−3,70 ecc.).
- **Seed**: `seed_previous_season` (10 round) → stat e prezzi partono "con storia". Convive col
  backfill (passato); i round forward guidano il movimento live (`price_history` reason `round`).
- **Non inietta valuta** → nessun impatto su inflazione/faucet/economia €.

### DINAMICHE FUTURE (sintetiche — arricchimento del prezzo-performance, da implementare)
Calendario partite (settimana corrente + 2 successive), **infortuni con livello di gravità**
(anche "da allenamento"), **più competizioni** (campionato + coppe), **forma/fatica**. Tutto
SINTETICO, mondo fittizio.

### DATI REALI = RIMANDATO (parere legale)
Architettura pronta (feed a innesto), ma **nessuna mappa/integrazione reale** finché il legale non dà
il via. **Posizione legale**: un nome fittizio mappato **1:1 a un giocatore reale + dati reali** è la
posizione **PIÙ DEBOLE** (possibile aggiramento dei diritti). Opzioni pulite: **(A)** fittizio +
sintetico, oppure **(B)** giocatori reali **propriamente licenziati** (nomi veri). I provider
(Opta/Sportradar) licenziano **solo i DATI**: NON i diritti nome/immagine, NÉ la classificazione del
prodotto (gioco a € su persone reali). **3 domande per il legale**: (1) dati, (2) immagine giocatori,
(3) classificazione del prodotto a €.

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
| Q8 | **Rotazione credenziali**: Google OAuth Client ID/Secret + Football-Data token sono stati esposti in `.env` durante lo sviluppo → ruotare prima del lancio | Fondatore | pre-lancio |
| Q9 | **i18n**: lingue oltre IT (EN/ES/FR/DE/PT/NL/PL/RO/AR) da tradurre/revisionare (architettura pronta, contenuti no) | Fondatore | post-MVP |
| ~~Q10~~ | ~~Design faucet engagement: approvare scala/soglie/cap~~ → ✅ **APPROVATO e wirato** (D6f.2/D6f.3) | — | — |
| Q11 | **Revisione budget iniziale** (10.000 cr) e cap dopo il disegno guadagni/sink (DT.2) | Fondatore | tuning |
