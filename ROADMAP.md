# ROADMAP — PlayerStock

Tempi **indicativi**. Costi = ordini di grandezza, non preventivi. I passaggi legali/fiscali
vanno validati da professionisti.

---

## ▶ STATO ATTUALE (2026-06-05)

**Fasi 0–6 completate** (MVP core, valuation/pricing, mercato, economia/portfolio, reward NACKL
placeholder, engagement). In aggiunta: **Fase 3b — prezzo ibrido** (impatto trading + rientro, DECISIONS
D3b) e **backbone dati `/api/stats/*`** + P&L realizzato (DD).

**Sequenza:** tuning economico (fatto: k=1.5, faucet engagement wirato) → **design pass CHIUSO**
(`DESIGN_SPEC.md`): chrome + Mercato + Portafoglio + Classifica + Engage + **Crediti-hub + Profilo** fatti,
**WEB target responsive** (tabella desktop / card mobile, DR.1). + guida "Come funziona" e valore €M (Fase 2c).

**Rinviate:** **Fase 7** (monetizzazione) e **Fase 8** (anti-cheat) → pre-lancio. **Fase "prezzo guidato
dalla performance"** (stat sportive che muovono il prezzo via coefficienti Gioco 5, DR.4) → fase "dati reali"
(richiede ritaratura economica). **Order book P2P** (matching tra utenti veri sopra il banco a due lati,
modello azioni "finito-duro", DR.7) → layer futuro quando la liquidità lo giustifica.

---

## Regole di divisione del lavoro (tutte le fasi)
1. **Chi fa cosa**: Emergent → scaffolding, UI/UX, CRUD, fasi ampie/semplici. Claude Code →
   logica critica (pricing/valuation + test, order book, reward/wallet, anti-cheat, hardening).
2. **Mai cambiare strumento a metà feature**: solo a confine di fase completata e committata.
3. **Handoff obbligatorio a fine fase**: commit + BLOCCO HANDOFF (strumento successivo + motivo).
4. **Dichiarazione a inizio sessione**: lo strumento dichiara chi è e la fase corrente.

### Mapping fasi → strumento
| Fase | Strumento | Stato |
|---|---|---|
| 0 — Setup repo + spec + spike SDK | **Claude Code** | ✅ fatta |
| 1 — Auth Google + modello dati + seed 400 giocatori + i18n | **Emergent** | ✅ fatta |
| 2 — Valuation + Pricing engine + test | **Claude Code** | ✅ fatta |
| 3 — Mercato (pool a due lati) | **Claude Code** | ✅ fatta |
| 3b — Prezzo ibrido (impatto trading + rientro) | **Claude Code** | ✅ fatta (D3b) |
| 4 — Economia Crediti + Portfolio | Emergent | ✅ fatta |
| 5 — Reward NACKL (testnet shellnet) | **Claude Code** | ✅ fatta (placeholder) |
| 6 — Engagement | Emergent | ✅ fatta |
| — Tuning economico + backbone dati `/api/stats/*` | **Claude Code** | 🔄 in corso |
| — Design pass (`DESIGN_SPEC.md`) | **Claude Code** | ✅ CHIUSO (Gruppo 3b: Crediti-hub + Profilo; + Fase 2c valore €M e backfill) |
| 7 — Abbonamento + donazioni + ads | Emergent | ⏸ RINVIATA pre-lancio |
| 8 — Anti-cheat + hardening | **Claude Code** | ⏸ RINVIATA pre-lancio |
| 8b — Polish UI finale | Emergent | (confluisce nel design pass) |

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

### Fase 2c — Valore di mercato €M (layer display) · Claude Code · ✅
`market_value_eur` realistico (poche stelle €60–120M, lunga coda €0,5–5M, spread ~150–250x), generato
**deterministico/fittizio** al seed (rosa a fasce + livello squadra come premio club), che **segue il
prezzo** via àncora. Sola visualizzazione: "Valore di mercato" €M su Mercato/Dettaglio, separato da
"Prezzo quota" (Crediti). **Economia di trading INTATTA** (prezzi/budget/cap/fee invariati). Dettaglio
in DECISIONS **DV.1**.

### Fase 3 — Mercato · Claude Code
**MVP (D3.2): pool a DUE LATI** (casa controparte al prezzo di quotazione), order book P2P/ordini
limite **rimandati**. Emissione primaria (IPO, float intero nel pool) + fee 7% (3.5+3.5)→house +
holding 7gg FIFO + cap 3% + `mercato%` (net flow→tick). → Cancello 2.

### Fase 3b — Prezzo IBRIDO (impatto trading + rientro) · Claude Code · ✅
Il trading muove il prezzo mantenendo la formula come **àncora**: `prezzo_mercato = àncora × (1+deviazione)`,
deviazione da buy/sell con **rientro lazy** `e^(−λ·Δt)`. Param: k_impatto **1.5**, emivita **3h**, cap
deviazione **±0.40**, floor 10%. Banco quota a prezzo_mercato +±3,5% fee. Supera il `mercato%` a bucket di
Fase 3. Dettaglio in DECISIONS **D3b**. (+ tuning economico, backbone `/api/stats/*`, P&L realizzato.)

### Fase 4 — Economia Crediti + Portfolio · Emergent
Budget iniziale 10.000, daily reward, 5 boost, sink/house edge, P&L portafoglio.

### Fase 5 — Reward NACKL su testnet · Claude Code
`RewardProvider` a 2 strati: **Internal** (placeholder dev, completo) + **Testnet shellnet**
(scaffold INERTE fino a Q1/Q5). Wallet connect solo mining PUBLIC key (QR/deep link). Schermata
Reward viva (saldo/connect/"mining in arrivo"). **WebView miner rimandato** (dipende da Q1+Q5).
Accrual placeholder via heartbeat firmato legato all'attività, cap conservativo (D5.2–D5.4).

### Fase 6 — Engagement · Emergent
Quiz, predictions, allenamenti, leghe + chat, streak, eventi a tempo.

### Fase 7 — Abbonamento + donazioni + ads · Emergent · ⏸ RINVIATA (pre-lancio)
IAP abbonamento mensile + free tier/trial; donazioni; rewarded ads (AdMob); gestione trasferimenti.
**Rinviata a pre-lancio**: prima si chiudono tuning + design + verifica schermate.

### Fase 8 — Anti-cheat + hardening (+ 8b polish UI) · Claude Code (8) / Emergent (8b) · ⏸ RINVIATA (pre-lancio)
Heartbeat firmato (HMAC+nonce), fingerprint, anti multi-account, rate limit, audit log; poi
rifinitura UI exchange. **Rinviata a pre-lancio** (l'indurimento reward serve prima di qualsiasi valore reale).

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
