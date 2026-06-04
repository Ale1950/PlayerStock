# ROADMAP — PlayerStock

Tempi **indicativi**. Costi = ordini di grandezza, non preventivi. I passaggi legali/fiscali
vanno validati da professionisti.

---

## Regole di divisione del lavoro (tutte le fasi)
1. **Chi fa cosa**: Emergent → scaffolding, UI/UX, CRUD, fasi ampie/semplici. Claude Code →
   logica critica (pricing/valuation + test, order book, reward/wallet, anti-cheat, hardening).
2. **Mai cambiare strumento a metà feature**: solo a confine di fase completata e committata.
3. **Handoff obbligatorio a fine fase**: commit + BLOCCO HANDOFF (strumento successivo + motivo).
4. **Dichiarazione a inizio sessione**: lo strumento dichiara chi è e la fase corrente.

### Mapping fasi → strumento
| Fase | Strumento |
|---|---|
| 0 — Setup repo + spec + spike SDK | **Claude Code** ✅ (fatta) |
| 1 — Auth Google + modello dati + seed 400 giocatori + i18n | **Emergent** ◀ prossima |
| 2 — Valuation + Pricing engine + test | **Claude Code** |
| 3 — Mercato / order book | **Claude Code** |
| 4 — Economia Crediti + Portfolio | Emergent |
| 5 — Reward NACKL (testnet shellnet) | **Claude Code** |
| 6 — Engagement | Emergent |
| 7 — Abbonamento + donazioni + ads | Emergent |
| 8 — Anti-cheat + hardening | **Claude Code** |
| 8b — Polish UI finale | Emergent |

---

## I 3 cancelli decisionali
1. **Tecnico (fine Fase 1)**: MVP gira + reward testnet validato? → prosegui.
2. **Valore/legale (fine Fase 3)**: metriche beta promettenti + qualificazione legale gestibile? → registra IP, avvia AN.
3. **Commerciale (fine Fase 4)**: accordo Acki Nacki accettabile? → Mainnet + pubblica.

---

## Fasi

### Fase 0 — Preparazione · Claude Code · ✅ COMPLETATA
Setup repo privato + spec/docs + spike `@teamgosh/bee-sdk` / Acki Nacki (via repo reale
`listen-and-mine`). Tutela IP preliminare (repo privato + commit). Vedi `docs/spike_bee_sdk.md`.

### Fase 1 — MVP core · Emergent (PARTENZA)
Auth Google OAuth + onboarding + modello dati multi-sport + generatore/seed roster 400 giocatori
Serie A (anonimizzazione L2) + i18n architecture. Crea moduli `auth/user/player/events`.
Avvio locale verificato. → Cancello 1.

### Fase 2 — Valuation + Pricing engine + test · Claude Code
Motore valutazione iniziale + pricing engine (calcio) + unit test su fixture. **Estrarre i valori
esatti da `Gioco 5.xls` foglio "Serie 1"** in `pricing_constants.py`/`valuation_constants.py`.

### Fase 3 — Mercato / order book · Claude Code
Emissione primaria + order book secondario P2P (quantità reali) + fee 7% (3.5+3.5) + holding 7gg +
cap 3%. → Cancello 2.

### Fase 4 — Economia Crediti + Portfolio · Emergent
Budget iniziale 10.000, daily reward, 5 boost, sink/house edge, P&L portafoglio.

### Fase 5 — Reward NACKL su testnet · Claude Code
`RewardProvider` (internal + testnet shellnet) + connessione wallet via QR (solo mining key).
Riuso pattern `listen-and-mine` dietro WebView. → vedi domanda aperta Q1 (app_dapp_id).

### Fase 6 — Engagement · Emergent
Quiz, predictions, allenamenti, leghe + chat, streak, eventi a tempo.

### Fase 7 — Abbonamento + donazioni + ads · Emergent
IAP abbonamento mensile + free tier/trial; donazioni; rewarded ads (AdMob); gestione trasferimenti.

### Fase 8 — Anti-cheat + hardening (+ 8b polish UI) · Claude Code (8) / Emergent (8b)
Heartbeat firmato (HMAC+nonce), fingerprint, anti multi-account, rate limit, audit log; poi
rifinitura UI exchange.

### Closed beta + decisione (parallela a Fasi 3–4)
Build EAS → TestFlight / Play Internal Testing; retention D1/D7/D30, DAU/MAU, ARPU. Se promettente:
registrazione IP formale + parere legale + avvio trattativa Acki Nacki.

### Fase Mainnet + lancio (post-accordo AN)
Sostituisci `TestnetWalletRewardProvider` con `MainnetBeeEngineProvider` (una classe);
app_dapp_id reale; onboarding Mamaboard; test Mainnet. Poi store: compliance Apple 3.1.5(b),
privacy, ASO, soft launch → scale.

### Espansione (continuo)
Aggiunta sport (tennis/basket/F1) riempiendo i pesi in config; dati reali con licenze; LiveOps.

---

## Rischi principali
1. **Legale/regolatorio** (qualificazione + token + cash-out): rischio #1 (Fase decisione).
2. **Dipendenza Acki Nacki**: mitiga tenendo MVP autonomo su economia interna fino all'accordo.
3. **Compatibilità SDK in RN**: ✅ sciolta in Fase 0 (WebView).
4. **Tenuta economica** (inflazione Crediti): verifica sink.
5. **Review store** su crypto/gambling: preparata pre-lancio.
6. **Engagement reale < atteso**: misurato in beta.
