# PlayerStock

App mobile di **borsa virtuale di atleti** (MVP: Serie A). Ogni atleta è un "titolo" diviso in quote frazionate; il prezzo varia con le performance reali e la domanda/offerta interna.

> **Disclaimer.** PlayerStock è un gioco di simulazione. I riferimenti agli atleti utilizzano iniziali e dati di cronaca pubblicamente disponibili. I nomi delle squadre sono di fantasia e non rappresentano affiliazioni ufficiali con alcun club professionistico.

## Due economie separate (principio guida)

1. **TRADING → "Crediti"** — valuta virtuale interna per comprare/vendere quote. Punteggio di gioco, **nessun valore monetario, nessun cash-out**. NON è crypto.
2. **REWARD → "NACKL"** — token reale (Acki Nacki), accumulato usando l'app via mining. **Non** compra quote. Validato su testnet (shellnet) in Fase 5.

Le due economie **non si mescolano mai**.

## Stack

| Layer | Tecnologie |
|---|---|
| Mobile | Expo (SDK recente) · React Native · TypeScript · Expo Router |
| Backend | FastAPI · Pydantic v2 · MongoDB · Redis · APScheduler |
| Auth | **Solo Google OAuth** (niente email/password) |
| Dati | Football-Data.org (adapter `DataProvider`) |
| i18n | i18next · react-i18next · expo-localization (default `it`, pronto 10 lingue) |
| Reward | `RewardProvider` → internal (MVP) / testnet shellnet (Fase 5) |

## Prerequisiti locali

- **Node** ≥ 20 + npm/yarn
- **Python** ≥ 3.11
- **MongoDB** ≥ 6 (locale o Atlas)
- **Redis** ≥ 7
- **Git** + account GitHub
- (Fase 1) Google OAuth Client ID/Secret · Football-Data.org API token

## Avvio locale

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
copy .env.example .env          # poi compila i segreti
uvicorn app.main:app --reload --port 8001
```
Tutte le route hanno prefisso `/api`.

### Frontend
```bash
cd frontend
npm install
copy .env.example .env          # imposta EXPO_PUBLIC_BACKEND_URL
npx expo start
```

### Servizi
MongoDB e Redis devono girare in locale (o via connection string in `.env`).

### Dati seed
Il roster 400 giocatori Serie A viene caricato in **Fase 1** (Emergent) da Football-Data.org con anonimizzazione Livello 2. Vedi `PROJECT_SPEC.md` §4.

## Test
```bash
cd backend
pytest                          # unit test pricing/valuation/order book (Fasi 2-3)
```

## Documenti di riferimento

| File | Contenuto |
|---|---|
| `PROJECT_SPEC.md` | Specifica di prodotto **autorevole** (fonte unica) |
| `ARCHITECTURE.md` | Stack, moduli, adapter, struttura repo |
| `DECISIONS.md` | Log decisioni + override spec + domande aperte |
| `ROADMAP.md` | Fasi 0–9 + mapping strumento |
| `docs/spike_bee_sdk.md` | Spike compatibilità mining Acki Nacki (Fase 0) |
| `docs/pricing_model.md` | Dettaglio pricing/valuation |
| `docs/i18n_guide.md` | Guida multilingua |
| `docs/compliance.md` | Disclaimer, anonimizzazione, profili legali |

## Divisione del lavoro

Sviluppo a fasi alternando **Emergent** (scaffolding/UI/CRUD) e **Claude Code** (logica critica: pricing, order book, reward, anti-cheat). Mai cambiare strumento a metà fase. Vedi `ROADMAP.md`.
