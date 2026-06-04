# ARCHITECTURE — PlayerStock

Documento tecnico di architettura. La specifica di **prodotto** è in `PROJECT_SPEC.md` (autorevole).

---

## 1. Vista d'insieme

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│  Mobile (Expo / RN / TS)    │  HTTPS │  Backend (FastAPI / Pydantic v2)  │
│  Expo Router · i18next      │ /api/* │  Uvicorn · APScheduler            │
│  WebView miner (Fase 5)     │◀──────▶│                                   │
└─────────────────────────────┘        │   ┌─────────────┐  ┌───────────┐ │
                                        │   │  MongoDB    │  │  Redis    │ │
                                        │   │  (persist)  │  │ (cache/   │ │
                                        │   └─────────────┘  │  ratelim) │ │
                                        │                    └───────────┘ │
                                        │   DataProvider ──▶ Football-Data │
                                        │   RewardProvider ─▶ AN shellnet  │
                                        └──────────────────────────────────┘
```

- **Due economie separate** a livello di modulo: `wallet` (Crediti) e `reward` (NACKL) non
  condividono né tabelle né flussi. Vedi `PROJECT_SPEC.md` §0.
- **Calcoli economici sempre lato server.** Il client non calcola mai prezzi/saldi.
- **Tutte le route** con prefisso `/api`.

---

## 2. Moduli backend (`backend/app/modules/`)

| Modulo | Responsabilità | Fase | Strumento |
|---|---|---|---|
| `auth` | Google OAuth, sessione/JWT | 1 | Emergent |
| `user` | profilo, impostazioni | 1 | Emergent |
| `wallet` | Crediti: saldo, movimenti, sink | 4 | Emergent |
| `reward` | `RewardProvider` (NACKL internal/testnet) | 5 | **Claude Code** |
| `player` | anagrafica atleti, anonimizzazione L2 | 1 | Emergent |
| `valuation` | valutazione iniziale (metodo) | 2 | **Claude Code** |
| `pricing` | pricing engine (driver + clamp + floor) | 2 | **Claude Code** |
| `market` | emissione primaria + order book secondario | 3 | **Claude Code** |
| `portfolio` | holding, P&L, prezzo medio carico | 4 | Emergent |
| `events` | eventi sportivi → driver performance | 1/2 | Emergent/CC |
| `engagement` | quiz, predictions, allenamenti, streak, leghe | 6 | Emergent |
| `subscription` | IAP, donazioni, ads | 7 | Emergent |
| `admin` | gestione, audit log | varie | — |

> Confini netti per il vincolo "mai cambiare strumento a metà fase": i moduli critici
> (valuation/pricing/market/reward) sono isolati e con interfacce stabili.

---

## 3. Adapter pattern — `DataProvider`

```
backend/app/data_providers/
├── base.py                  # interfaccia astratta DataProvider
└── football_data_org.py     # FootballDataOrgProvider (concreto)
```

Interfaccia: fixture/calendario, roster, statistiche evento → **schema interno comune**
(stesso schema futuro per tennis/basket/F1). Selezione via `.env` `DATA_PROVIDER`.
Cache Redis TTL: fixture 1h, stats live 5min (rispetta free tier ~10 req/min).

---

## 4. Adapter pattern — `RewardProvider`

Interfaccia astratta (`can_earn`, `accrue`, `balance`, `provider_name`). Implementazioni:
- `InternalRewardProvider` — DB, MVP (default `REWARD_PROVIDER=internal`).
- `TestnetWalletRewardProvider` — Acki Nacki shellnet (Fase 5). Miner in **WebView**
  (bundle web-react bridge), mining key via deep link/QR, **mai seed/spend key**.
- `# Future: MainnetBeeEngineProvider` — segnaposto, post-accordo AN.

Dettaglio integrazione: `docs/spike_bee_sdk.md`.

---

## 5. Modello dati (MongoDB) — schema multi-sport

Modello unico per 4 sport (calcio definito; altri in config con segnaposto).

```
Atleta   { id, sport_id, nome /* solo DB interno */, ruolo, valore_iniziale,
           float_quote, prezzo_corrente, prezzo_iniziale, data_source, eta,
           minutaggio_pct, team_id, nazionalita_iso3 }
Evento   { atleta_id, match_id, tipo, valore, timestamp }
Holding  { user_id, atleta_id, quantita, prezzo_medio_carico, acquired_at }
Ordine   { user_id, atleta_id, lato /* buy|sell */, quantita, prezzo, tipo /* limit|market */, stato }
User     { id, google_sub, email, crediti, locale, created_at }
```

Ingestion dietro interfaccia (generatore ↔ provider intercambiabili). Order flow di mercato
**sempre reale**.

---

## 6. Configurazione / costanti

- `backend/app/config/pricing_constants.py` — struttura azionaria, economia, driver, clamp, mercato, engagement.
- `backend/app/config/valuation_constants.py` — BaseRuolo, fattori età/minutaggio/squadra, K.
- Valori esatti driver **estratti da `Gioco 5.xls` (foglio "Serie 1") in Fase 2**.
- Segreti **solo** in `.env` (vedi `.env.example`).

---

## 7. i18n

- `i18next` + `react-i18next` + `expo-localization`. Default `it`, fallback `it`.
- `frontend/src/i18n/locales/{it,en,es,fr,de,pt,nl,pl,ro,ar}/common.json`.
- MVP: chiavi solo in `it/common.json`; altri JSON `{}` con TODO.
- Backend: errori con `error_code` machine-readable + `message_it`; il client mappa a i18n.
- RTL (`ar`): pre-configura `I18nManager`, non forzare in MVP.
- Dettagli: `docs/i18n_guide.md`.

---

## 8. Struttura repository

```
PlayerStock/
├── README.md · PROJECT_SPEC.md · ARCHITECTURE.md · DECISIONS.md · ROADMAP.md
├── .env.example · .gitignore
├── docs/  (spike_bee_sdk · pricing_model · i18n_guide · compliance)
├── backend/
│   ├── pyproject.toml · requirements.txt · .env.example
│   ├── app/
│   │   ├── main.py
│   │   ├── config/   (pricing_constants.py · valuation_constants.py)
│   │   ├── modules/  (auth user wallet reward player valuation pricing
│   │   │              market portfolio events engagement subscription admin)
│   │   ├── data_providers/  (base.py · football_data_org.py)
│   │   ├── models/   (Pydantic v2)
│   │   └── db/
│   └── tests/        (pytest — pricing/valuation/order book)
├── frontend/
│   ├── package.json · app.json · .env.example
│   ├── app/   (Expo Router: _layout · index · (auth) · (tabs) · player/[id])
│   └── src/   (components hooks services i18n utils theme)
└── .github/workflows/  (backend-tests.yml · frontend-lint.yml)
```

---

## 8. Sicurezza (Fase 8 — Claude Code)

Heartbeat firmato (HMAC + nonce) per reward; device fingerprint; rilevamento
emulatori/multi-account; rate limit su Redis; cap giornaliero; audit log immutabile.
Tutti i calcoli economici lato server.
