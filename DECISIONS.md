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

## ❓ DOMANDE APERTE (da risolvere col fondatore / terzi)

| # | Domanda | Per chi | Blocca fase |
|---|---|---|---|
| Q1 | **APP_ID di listen-and-mine (`0x00…01`) è riusabile per PlayerStock, o serve registrare un app_dapp_id separato presso Acki Nacki?** L'approvazione AN di listen-and-mine **non** estende automaticamente a PlayerStock. | Acki Nacki | Fase 5 |
| Q2 | Google OAuth Client ID/Secret | Fondatore | Fase 1 |
| Q3 | Football-Data.org API token | Fondatore | Fase 1 |
| Q4 | MongoDB connection string (locale o Atlas) + Redis | Fondatore | Fase 1 |
| Q5 | Mining key / wallet di test AN (shellnet) | Fondatore/AN | Fase 5 |
| Q6 | Qualificazione giuridica (gioco vs strumento finanziario vs azzardo) | Legale | pre-lancio |
| Q7 | Football-Data.org dà roster completi o serve fallback Wikipedia? | da verificare | Fase 1 |
