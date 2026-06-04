# PROJECT_SPEC — PlayerStock (MVP Serie A)

> **Fonte unica e autorevole della specifica di prodotto.** In caso di conflitto con
> qualsiasi altro documento (prompt Emergent, prompt generati, note), **vince questo file**.
> Le DECISIONI FINALI di §2 hanno priornità assoluta: dove la vecchia spec funzionale
> divergeva (float 10.000, cap 5–10%, auth multipla, dati simulati) è stata **sovrascritta**.
> Storico override in `DECISIONS.md`.

---

## 0. Concetto e due economie separate

App che simula una **borsa virtuale di atleti** (MVP: calcio Serie A). Ogni atleta è un
"titolo" diviso in quote frazionate; il prezzo varia con performance reali e domanda/offerta
interna.

**Due economie separate (principio guida, mai mescolate):**
1. **TRADING (interno, virtuale) → "Crediti".** Valuta per comprare/vendere quote. Punteggio
   di gioco **senza valore monetario, senza cash-out**. NON è crypto/NACKL.
2. **REWARD per l'uso dell'app → NACKL (mining reale, Acki Nacki).** Accumulato usando l'app;
   **NON** compra quote; validato su **testnet (shellnet)** in Fase 5.

Contenuti **solo Serie A**; architettura **pronta per 4 sport** (calcio/tennis/basket/F1) via config.

---

## 1. Stack e vincoli

- **Mobile**: Expo (SDK recente) / React Native / TypeScript / Expo Router.
- **Backend**: FastAPI + Pydantic v2 + MongoDB + Redis + APScheduler.
- **Auth**: **SOLO Google OAuth** (no email/password, no altri provider).
- Route con prefisso **`/api`**. Secret in `.env`. Calcoli economici **sempre lato server**.
- Pricing engine **source-agnostic**: pesi + fonte dati da config; il valore difendibile è il **metodo**.
- **Quantità di trading reali** (order book reale nel secondario).
- Earning NACKL **solo** via interfaccia `RewardProvider`.

**NON fare**: acquisto quote con NACKL o denaro reale; cash-out Crediti; Mainnet/app_dapp_id
reale in MVP; seed/chiavi di spesa wallet nell'app; terminologia crypto nei testi di trading.

---

## 2. DECISIONI FINALI (override obbligatorio)

| Parametro | Valore |
|---|---|
| Nome app | **PlayerStock** |
| Float quote per giocatore | **1.000.000** |
| Valore base giocatore | **10.000 Crediti** (= €10.000 fittizi, 1:1 non convertibile) |
| Prezzo base azione | **0.01 Credito** (= 10.000 / 1.000.000) |
| Cap utente per giocatore | **3%** del float (= **30.000 quote** max) |
| Budget iniziale nuovo utente | **10.000 Crediti** |
| Holding minimo pre-rivendita | **7 giorni** |
| Fee marketplace totale | **7%** = **3.5% buyer + 3.5% seller** (split 50/50) |
| Floor minimo prezzo | **10%** del prezzo iniziale |
| Trasferimento giocatore | Rimborso automatico a tutti i possessori al **prezzo medio del giorno precedente** alla cessione ufficiale |
| Display UI prezzi | **4 decimali** (es. €0.0350) |
| Auth | **SOLO Google OAuth** |
| Lingua MVP | Solo **italiano**; architettura i18n pronta a **10 lingue** (IT/EN/ES/FR/DE/PT/NL/PL/RO/AR) |
| Roster MVP | **400 giocatori** Serie A (20 squadre × 20) |
| Anonimizzazione | **Livello 2** + disclaimer obbligatorio |
| Dati fixture/calendario | **Reali** da Football-Data.org (§4) |
| Reward NACKL | `InternalRewardProvider` (MVP); `TestnetWalletRewardProvider` shellnet (Fase 5) |

### Mappa squadre fantasy (anonimizzazione L2)
| Reale (DB interno) | Fantasy (UI) |
|---|---|
| Inter | Nerazzurri Milano |
| Juventus | Bianconeri Torino |
| Milan | Rossoneri Milano |
| Napoli | Azzurri Partenopei |
| Roma | Giallorossi Capitolini |
| Lazio | Biancocelesti Capitolini |
| Atalanta | Nerazzurri Bergamo |
| Fiorentina | Viola Firenze |
| Bologna | Rossoblu Felsinei |
| Torino | Granata Torino |
| Genoa | Rossoblu Liguri |
| Lecce | Giallorossi Salentini |
| Udinese | Bianconeri Friulani |
| Cagliari | Rossoblu Sardi |
| Monza | Biancorossi Brianzoli |
| Verona | Gialloblu Scaligeri |
| Empoli | Azzurri Toscani |
| Parma | Gialloblu Ducali |
| Como | Biancoblu Lariani |
| Venezia | Arancioneroverdi Lagunari |

**Disclaimer OBBLIGATORIO** (T&C, landing, footer Home):
> "PlayerStock è un gioco di simulazione. I riferimenti agli atleti utilizzano iniziali e dati
> di cronaca pubblicamente disponibili. I nomi delle squadre sono di fantasia e non
> rappresentano affiliazioni ufficiali con alcun club professionistico."

---

## 3. Anonimizzazione Livello 2 — pattern

Per ogni atleta mostra **solo**:
- Iniziale nome + cognome abbreviato (max 8 char): `L. Martín`
- Nazionalità ISO-3: `ARG`
- Ruolo: `POR` / `DIF` / `CC` / `ATT`
- Età
- Squadra fantasy (mappa §2)
- Statistiche pubbliche

**Vietato**: foto reali, loghi club ufficiali, nome esteso, nome club esatto.
**Avatar**: iniziali stilizzate in cerchio coi colori della squadra fantasy.
Nome reale **solo** nel DB interno, mai esposto in UI/API pubbliche.

---

## 4. Fonte dati

Provider europeo affidabile per fixture/calendario/stat Serie A **2024-25**, dietro
adapter (vedi `ARCHITECTURE.md`).

- **Primario**: **Football-Data.org** (free tier ~10 req/min; Serie A + top-5 leghe). Base UE.
- **Secondario**: OpenLigaDB (free) · API-Football su RapidAPI (paid, backup).
- **Cache Redis** con TTL aggressivo: fixture 1h, stats live 5min (rispetta rate limit).
- `.env`: `DATA_PROVIDER=football_data_org`, `FOOTBALL_DATA_ORG_TOKEN=xxx`.
- Stat normalizzate in **schema interno comune** (futuro: stesso schema tennis/basket/F1).
- Order flow di mercato = **SEMPRE reale** (dagli ordini utente).

Roster 400 giocatori dalla rosa **reale** Serie A 2024-25 (nome reale solo DB → UI = L2).
Fallback se free tier non dà roster completi: parsing Wikipedia delle 20 rose
(`requests + beautifulsoup4`, script commentato).

---

## 5. Valutazione iniziale (metodo oggettivo, asset IP)

Formula trasparente su metriche osservabili (**NON** copiare fonti proprietarie).
Costanti in `backend/app/config/valuation_constants.py`:

```
ValoreIniziale = BaseRuolo × ScorePerformance × FattoreEtà × FattoreMinutaggio × FattoreSquadra × K
```
- **BaseRuolo**: POR 0.85 · DIF 0.90 · CC 1.05 · ATT 1.20.
- **ScorePerformance**: output 12 mesi normalizzato per ruolo ~1.0 (range 0.5–2.0).
- **FattoreEtà**: campana, picco 24–27 (1.15@24, 1.0@30, 0.7@34, under-21 alto potenziale 1.05).
- **FattoreMinutaggio**: % minuti (0.6–1.0). **FattoreSquadra**: 0.9–1.2. **K**: scala globale.

Struttura azionaria (DECISIONI FINALI §2): **float 1.000.000 quote/giocatore**;
**prezzo iniziale = 0.01 Credito** (valore base 10.000 / 1.000.000); cap utente **3%**.
Il prezzo iniziale è la base degli incrementi/decrementi %.

> I valori esatti di `valuation_constants.py` e `pricing_constants.py` (driver gol/assist/voto/
> minuti/clamp) vanno **estratti dal file `Gioco 5.xls` foglio "Serie 1"** in **Fase 2** (Claude Code).
> `Gioco 5.xls` **non è versionato** (know-how riservato — vedi `DECISIONS.md`).

---

## 6. Quotazione ed exchange

```
nuovo_prezzo = vecchio_prezzo × (1 + performance% + mercato% + engagement%)
```
clamp ai range per ruolo, **floor al 10%** del prezzo iniziale; tick post-evento + real-time +
consolidamento giornaliero.

- **Performance %** (settimanale): somma driver oggettivi clampata al range ruolo.
- **Mercato %** (real-time): pressione domanda/offerta da **order flow reale**.
- **Engagement %**: bonus attività utente.

**Exchange a quantità reali:**
- **Emissione primaria**: pool primario al prezzo iniziale (tipo IPO).
- **Mercato secondario P2P**: order book reale limit/market — si compra **solo** ciò che è
  offerto, si vende **solo** ciò che si possiede.
- **Holding minimo 7 giorni** (anti-flip); **cap utente 3%**.
- UI: lista quotazioni (prezzo, %, sparkline); dettaglio titolo (grafico); finestra buy/sell con
  book (bid/ask + quantità reali), saldo Crediti, anteprima fee.

### Driver oggettivi CALCIO (valori esatti da `Gioco 5.xls` in Fase 2)
- **Minuti** (>60'/45-60'/≤45'): DIF +0.28/-0.25/-0.50 · CC +0.38/-0.15/-0.38 · ATT +0.45/0.00/-0.10 · POR +0.18/-0.25/-0.50 (%).
- **Gol** (1/≥2): DIF +0.45/+0.75 · CC +0.28/+0.45 · ATT +0.18/+0.25 · POR +0.60/+0.89.
- **Gol subiti squadra** (1/≥2/clean sheet): DIF -0.35/-0.50/+0.18 · CC -0.25/-0.40/+0.10 · ATT -0.15/-0.25/+0.05 · POR -0.35/-0.65/+0.25.
- **Espulsione**: DIF -0.38 · CC -0.50 · ATT -0.75 · POR -0.89.
- **Assist** (1/≥2): DIF +0.45/+0.65 · CC +0.15/+0.25 · ATT +0.10/+0.15 · POR +0.45/+0.65.
- **Rigori** segnati +0.50/+0.75/+0.89 · sbagliati -0.50/-0.89 · parati POR +0.50/+0.78/+1.00.
- **Voto POR**: <6 -0.50 · 6-7 +0.38 · ≥8 +0.50. **Autorete** -0.50/-0.75/-0.89.
- **Ammonizione** -0.25…-0.45 · nessuna +0.38.
- **Range max giornaliero (clamp)**: DIF +4.13/-2.54 · CC +3.10/-2.12 · ATT +2.87/-2.81 · POR +4.24/-3.70 (%).
- Tennis/Basket/F1: stessa struttura, pesi a config (`# TODO: pesi forniti dal fondatore`).

### Driver di mercato (order flow REALE)
- Acquisti 1-5 / 6-20 / >20 = **+1.2 / +2.0 / +2.5 %**.
- Vendite 1-5 / 6-20 / >20 = **-1.2 / -2.0 / -2.5 %**.

### Driver engagement
- Allenamenti 2 / 3-4 / 5+ sett = **+0.25 / +0.40 / +0.48 %**.
- Lega 1-5 / 6-20 / >20 = **+0.25 / +0.55 / +0.71 %**.

---

## 7. Layer reward NACKL — `RewardProvider` (wallet su TESTNET)

Interfaccia astratta `RewardProvider` (metodi: `can_earn`, `accrue`, `balance`, `provider_name`).
Implementazioni:
1. `InternalRewardProvider` — DB, offline/dev (MVP).
2. `TestnetWalletRewardProvider` — Acki Nacki shellnet (Fase 5). Vedi `docs/spike_bee_sdk.md`.
3. Segnaposto NON implementare: `# Future: MainnetBeeEngineProvider — dopo accordo AN`.

Accredito NACKL **solo** via `RewardProvider`, mai mescolato ai Crediti. Autorizzazione via
AN Wallet con **mining key** (deep link/QR) — **mai seed o chiavi di spesa nell'app**. Provider
via `.env` (`REWARD_PROVIDER=internal|testnet`).

> **Spike Fase 0 completato** (`docs/spike_bee_sdk.md`): l'implementazione reale approvata AN
> (`listen-and-mine-acki-nacki`) è **web React+Vite**, non RN nativo → in PlayerStock il miner
> gira in **WebView** dietro `RewardProvider`. SDK = `bee_sdk` WASM self-hostato + `@eversdk`.

---

## 8. Economia Crediti

Budget iniziale nuovo utente = **10.000 Crediti**. Guadagno in-app (daily reward, quiz,
predictions, streak, allenamenti) — separati dal NACKL. **5 boost giornalieri** (daily login,
reset via scheduler). Marketplace fee **7%** sul secondario (sink). Sink/house edge
configurabile. Floor minimo + bonus riattivazione anti-churn.

---

## 9–11. Engagement / Monetizzazione / Sicurezza

- **Engagement**: quiz, predictions, allenamenti (cooldown), streak, leghe + chat, eventi a tempo, news simulate.
- **Monetizzazione**: abbonamento mensile (IAP) per usare l'app + free tier/trial; donazioni; rewarded ads (AdMob).
- **Sicurezza**: heartbeat firmato (HMAC+nonce) per reward; device fingerprint; rilevamento
  emulatori/multi-account; rate limit Redis; cap giornaliero; audit log immutabile; calcoli
  economici lato server.

---

## 12. Testing (obbligatorio)

Unit test: pricing engine (fixture dalle tabelle §6), valutazione iniziale, order book (matching,
fee 7%, holding minimo, cap, quantità reali), reward provider. **Eseguibili con un singolo
comando documentato** (`pytest`).

---

## 13. Schermate mobile

Onboarding/auth (Google); Home quotazioni (prezzo, %, sparkline); Dettaglio titolo (grafico +
buy/sell + book); Portfolio (P&L); Wallet Crediti; Reward NACKL (saldo + connessione wallet
testnet via QR); Engagement; Leghe; Abbonamento; Admin.
