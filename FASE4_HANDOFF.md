# PlayerStock — Fase 4 (Emergent) — Economia Crediti + Portfolio

## Endpoint nuovi (additivi, prefix /api)
- **GET /api/portfolio** (JWT) — posizioni con qty, prezzo corrente, cost basis FIFO,
  P&L assoluto e %, totali (cassa + valore titoli + total equity + total P&L)
- **GET /api/wallet** (JWT) — saldo crediti + ultime N transazioni (default 20)
- **GET /api/leaderboard** (JWT) — top 50 utenti per equity totale; privacy:
  "Mario R." per altri, nome pieno per self; `self` separato se fuori dal top-N
- **GET /api/athletes/{id}/price-history?limit=N** (public, no auth) — punti sparkline

I 2 endpoint legacy Fase 1 restano funzionanti:
- GET /api/wallet/balance  (legacy)
- GET /api/wallet/transactions (legacy)

## Schermate frontend cablate
- `app/(tabs)/portfolio.tsx` — sostituito stub: lista posizioni con sparkline,
  P&L verde/rosso, totali, pull-to-refresh
- `app/(tabs)/leaderboard.tsx` — NUOVA tab
- `app/(tabs)/_layout.tsx` — aggiunta tab "Classifica"
- `src/services/portfolio.service.ts` — nuovo client typed
- `src/components/Sparkline.tsx` — minimal SVG sparkline

## Assunzioni sul modello dati (per Claude Code in fase di merge)
- `holdings.lots[i].price` ESISTE già (popolato in Fase 3 da `execute_buy`)
- `wallet_transactions.description_it` ESISTE già (Fase 1)
- `users.status == "active"` per leaderboard (esclude soft-deleted)
- `price_history.{athlete_id, ts, price}` con indice già esistente
- `athletes.prezzo_corrente_crediti` aggiornato dal pricing engine Fase 2
- Cost basis FIFO ≡ Σ(qty × price) sui lotti residui (post-`consume_lots_fifo`)

## Test
26/26 unit test passati (`backend/tests/test_portfolio_service.py`):
- cost_basis_from_lots (empty, single, multi, zero qty, missing fields)
- avg_cost_per_share (empty, uniform, weighted, zero qty)
- position_pnl (profit, loss, breakeven, multi-lot weighted, no-div-zero, negative-qty-clamp, floor scenario)
- aggregate_totals (empty, mixed, excludes zero-qty, only-cash)
- anonymize_display_name (privacy: anon vs self, single-token, empty fallback, no-email-leak)

## Validazione E2E (eseguita su Emergent con seed mock Fase 3)
- 4 posizioni: utile +56%, +13%, perdita -10%, breakeven 0%
- Total equity 10.020,3125 Crediti (cash 9883,56 + titoli 136,75)
- Wallet 5 transazioni recenti restituite
- Leaderboard 1 utente con flag SELF
- Price history 5 punti (sparkline)

## Cosa NON ho toccato
- `app/market/*` (Fase 3 di Claude Code) — INVARIATO
- `app/pricing/*` e `app/valuation/*` (Fase 2) — INVARIATO
- 4 file di spec autorevoli, DECISIONS.md, ROADMAP.md — INVARIATI

## Non incluso (volutamente fuori scope)
- Reward NACKL (Fase 5)
- Eventuale persistenza del rank storico utente
- Notifiche push su variazioni equity (richiede dev build)
