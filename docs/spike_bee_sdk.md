# SPIKE — Mining Acki Nacki / Bee Engine (Fase 0)

> **Obiettivo**: sciogliere il rischio di compatibilità del mining SDK in Expo/RN e definire il
> piano di riuso per la Fase 5. **Metodo**: analisi del repo reale **approvato da Acki Nacki**
> `Ale1950/listen-and-mine-acki-nacki` (clonato e letto, read-only). Nessuna installazione.

---

## 1. Stack del repo reale → risolve la compatibilità RN

| Aspetto | Valore osservato |
|---|---|
| Tipo app | **Telegram Mini App** (`name: listen-mine-tma`, v2.0.0) |
| Framework | **React 18 + Vite 5 + TypeScript** (web) |
| Build | `tsc -b && vite build` · entry `index.html` + `src/main.tsx` |
| RN/Expo? | **NO.** Nessuna dipendenza React Native / Expo. |

**Verdetto compatibilità**: non esiste un binding nativo React Native dell'SDK di mining.
L'implementazione approvata è **web**. → Per PlayerStock (Expo/RN) il miner deve girare in
**WebView** che carica il bundle web, con un bridge RN↔WebView. **Niente porting nativo.**

---

## 2. SDK reale usato (≠ assunzione iniziale)

L'assunzione era `@teamgosh/bee-sdk`. Realtà dal repo:

| Componente | Pacchetto / asset | Uso |
|---|---|---|
| Mining engine | **`bee_sdk` WASM self-hostato** (`public/bee-sdk/bee_sdk.js` + `bee_sdk_bg.wasm`) | gen keys, Miner, tap, reward |
| Letture on-chain | **`@eversdk/core` ^1.48 + `@eversdk/lib-web`** (`public/eversdk/eversdk.wasm`) | saldi NACKL/SHELL via GraphQL |
| Hashing | `js-sha256` | — |

Nota dal codice (`src/services/bee-sdk.ts`): l'SDK è **self-hostato** dalla build di **Mining
Hub** perché `@teamgosh/bee-sdk@0.1.0` (npm) aveva un bug `submit_session_root` (ack-only: la tx
risulta OK localmente ma non atterra on-chain). Il WASM viene caricato dinamicamente
(`fetch` + `new Function()`, riscrivendo `import.meta.url` prima dell'eval).

ABIs on-chain presenti: `Miner.abi.json`, `MinerRoot.abi.json`, `MvGameRoot.abi.json`, `Wallet.abi.json`.

---

## 3. Flusso di MINING (da `src/services/bee-sdk.ts`)

```
1. init(WASM)                                   # carica bee_sdk WASM
2. gen_mining_keys(APP_ID, wallet_name)         # → { deep_link, public, secret }
3. get_miner_address_by_wallet_name(...)        # → miner_address
4. utente apre deep_link nell'app AN Wallet e conferma
5. (polling REST finché le mining key propagano on-chain)
6. Miner.new(endpoints, app_id, miner_address, public, secret)   # timeout 30s
7. miner.add_tap(0,0)                            # smoke test (non fatale)
8. API miner: can_start() / start(durationMs, cb) / add_tap(x,y) / stop() / get_reward()
```

- **Endpoint**: `https://mainnet.ackinacki.org` (bee-sdk) · GraphQL mainnet/mainnet-cf/**shellnet**.
- **APP_ID**: `0x00…0001` (dev/listen-and-mine). `dapp_id` = APP_ID senza `0x`, padded a 64 hex.
- Sessione configurabile (`mining-config.ts`): durata default 15s, 8 tap (dev panel).

---

## 4. CREAZIONE e ACCESSO al wallet

- Il wallet **non è creato né custodito dall'app**. Vive nell'app esterna **AN Wallet**.
- L'app ottiene soltanto:
  - `miner_address` (via `get_miner_address_by_wallet_name`),
  - una **coppia mining key** `public`/`secret` (da `gen_mining_keys`).
- L'autorizzazione passa per un **deep link / QR** verso AN Wallet, che l'utente conferma.
- `blockchain.ts` e `mamaboard.ts` eseguono **solo letture** GraphQL (saldi NACKL currency=1,
  SHELL=2, locked Mamaboard). Nessuna scrittura/spesa dal codice dell'app.

---

## 5. ✅ Sicurezza — SOLO mining key (verificato)

- `grep` di `seed | mnemonic | phrase` nel sorgente: **nessun seed wallet / mnemonic**.
  Le occorrenze "seed" in `App.tsx` sono il **gate di sessione mining** (`can_start`), non una
  frase di recupero wallet.
- **Nessuna chiave di spesa** nel codice. Si usano esclusivamente le **mining key** + deep link
  all'AN Wallet per la firma.
- ✔ Conforme al vincolo di `PROJECT_SPEC.md` §7: *mai seed o chiavi di spesa nell'app*.

---

## 6. Piano di RIUSO in Fase 5 (no copia-incolla)

1. **Host del bundle web-miner** come asset (WebView) dentro l'app Expo/RN — bundle derivato dal
   pattern `listen-and-mine`, **non** copiato verbatim.
2. **Bridge RN ↔ WebView** (`postMessage`): comandi `startSession / stopSession / openWalletDeepLink
   / readBalance`; eventi di ritorno `reward / status / error`.
3. Tutto **dietro l'interfaccia `RewardProvider`** (`can_earn`, `accrue`, `balance`,
   `provider_name`): `TestnetWalletRewardProvider` su **shellnet**.
4. **Due economie separate**: il NACKL passa solo dal `RewardProvider`, **mai** nei Crediti.
5. Riusare la **resilienza** osservata (auto-reboot engine, WS reconnect, categorizzazione errori
   `KitError/GraphQL/network`) come riferimento, riscritta pulita nel wrapper.
6. Segnaposto `# Future: MainnetBeeEngineProvider` per il post-accordo AN (una sola classe da
   sostituire).

---

## 7. ⚠️ Caveat — app_dapp_id (domanda aperta Q1)

L'`APP_ID = 0x00…01` è quello di **listen-and-mine**. L'approvazione di Acki Nacki su
quell'app **non si estende automaticamente** a PlayerStock.

**Da confermare con Acki Nacki prima della Fase 5**: l'app_dapp_id è riusabile per PlayerStock,
oppure serve **registrare un app_dapp_id separato**? Tracciato in `DECISIONS.md` → Q1.

---

## 8. Rischi residui per la Fase 5

- WebView mobile vs WASM: verificare performance/threading del WASM miner in WebView Expo
  (Android `react-native-webview`) — potenziale necessità di worker.
- Deep link AN Wallet su mobile: testare lo scheme/universal link reale.
- Rate/affidabilità nodo shellnet vs mainnet (il repo gira su mainnet; noi useremo shellnet).
