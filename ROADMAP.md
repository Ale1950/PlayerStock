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
1. **Tecnico (fine Fase 1)**: **MVP core gira** → prosegui. (Il reward testnet è **Fase 5**,
   NON richiesto qui — vedi D1.2.) Criteri: backend su Atlas (`DB_NAME=playerstock`) con
   `/api/health` `/sports` `/teams` `/players` OK · seed popola **400 atleti fittizi** (D1.1) ·
   **nessun `internal_full_name`** nelle response · test base verdi.
2. **Valore/legale (fine Fase 3)**: mercato a quantità reali (pool a due lati) + fee/cap/holding +
   `mercato%` che muove i prezzi funzionante; metriche beta promettenti + qualificazione legale
   gestibile? → registra IP, avvia AN.
3. **Commerciale (fine Fase 4)**: accordo Acki Nacki accettabile? → Mainnet + pubblica.

---

## Fasi

### Fase 0 — Preparazione · Claude Code · ✅ COMPLETATA
Setup repo privato + spec/docs + spike `@teamgosh/bee-sdk` / Acki Nacki (via repo reale
`listen-and-mine`). Tutela IP preliminare (repo privato + commit). Vedi `docs/spike_bee_sdk.md`.

### Fase 1 — MVP core · Emergent (PARTENZA)
Auth Google OAuth + onboarding + modello dati multi-sport + generatore/seed roster 400 giocatori
Serie A (**fittizi realistici**, anonimizzazione L2 — vedi D1.1) + i18n architecture. Crea moduli
`auth/user/player/events`. Avvio locale verificato. → Cancello 1 (criteri in §"3 cancelli", D1.2).

### Fase 2 — Valuation + Pricing engine + test · Claude Code
Motore valutazione iniziale + pricing engine (calcio) + unit test su fixture. **Estrarre i valori
esatti da `Gioco 5.xls` foglio "Serie 1"** in `pricing_constants.py`/`valuation_constants.py`.

### Fase 3 — Mercato · Claude Code
**MVP (D3.2): pool a DUE LATI** (casa controparte al prezzo di quotazione), order book P2P/ordini
limite **rimandati**. Emissione primaria (IPO, float intero nel pool) + fee 7% (3.5+3.5)→house +
holding 7gg FIFO + cap 3% + `mercato%` (net flow→tick). → Cancello 2.

### Fase 4 — Economia Crediti + Portfolio · Emergent
Budget iniziale 10.000, daily reward, 5 boost, sink/house edge, P&L portafoglio.

### Fase 5 — Reward NACKL su testnet · Claude Code
`RewardProvider` a 2 strati: **Internal** (placeholder dev, completo) + **Testnet shellnet**
(scaffold INERTE fino a Q1/Q5). Wallet connect solo mining PUBLIC key (QR/deep link). Schermata
Reward viva (saldo/connect/"mining in arrivo"). **WebView miner rimandato** (dipende da Q1+Q5).
Accrual placeholder via heartbeat firmato legato all'attività, cap conservativo (D5.2–D5.4).

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
