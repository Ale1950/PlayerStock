# Home Bento (impaginazione B) — Implementation Plan

**Goal:** Trasformare la home nella dashboard "bento" Luxury (2 colonne web / 1 mobile), spostando l'attuale tabella mercato in una tab "Mercato" dedicata. Solo dati già esistenti; Match day + News = placeholder.

**Architecture:** `home.tsx` diventa l'orchestratore (carica i dati e impagina il bento); la tabella mercato si sposta verbatim in `market.tsx`. Frame "finestra" condiviso via nuovo `BentoCard`. Nessun nuovo endpoint backend (Talento = best gainer da `/stats/market`).

**Tech Stack:** Expo/expo-router, React Native, tema Luxury (`useTheme().colors`), `useResponsive` (breakpoint 760).

**Vincoli:** branch `feat/run-app-web`, niente merge. Responsive web+mobile. Backend test verdi (270, invariati). Nessuna regressione. Niente hex nuovi.

---

## Dati disponibili → modulo (nessun endpoint nuovo)

| Modulo bento | Fonte esistente | Campi |
|---|---|---|
| Hero Match day | — (PLACEHOLDER statico) | nessuno |
| Portafoglio | `getPortfolio()` | `totals.total_equity`, `total_pnl_abs`, `total_pnl_pct` |
| Posizione | `getLeaderboard()` | `self.rank`, `total_users` |
| Mercato | `getMarketOverview()` | `top_gainers/losers`, `total_market_cap`, `volume_24h`, `active_count` |
| Talento del giorno | `getMarketOverview().top_gainers[0]` + `getPriceHistory(id)` | best gainer: `display_label`, `var_pct`, sparkline |
| News del giorno | — (3 card PLACEHOLDER) | sorgente+titolo+link segnaposto |

Auth: la home è raggiunta solo da autenticati (guard in `_layout`). Ogni card gestisce il proprio stato loading/empty/error **in isolamento** (un fallimento non sbianca l'intera dashboard).

---

## File Structure

**Creati:**
- `frontend/app/(tabs)/market.tsx` — tabella mercato (contenuto attuale di `home.tsx`, spostato).
- `frontend/src/components/BentoCard.tsx` — pannello "finestra" condiviso (titolo + azione opzionale + bordo lime 2px).
- `frontend/src/content/newsPlaceholder.ts` — 3 voci news statiche (segnaposto).

**Modificati:**
- `frontend/app/(tabs)/home.tsx` — riscritto: dashboard bento.
- `frontend/app/(tabs)/_layout.tsx` — aggiunta tab "Mercato" + icone + i18n.
- `frontend/src/i18n/locales/it/common.json` (+ `en`) — chiavi bento/tab.
- `PROJECT_SPEC.md`, `ROADMAP.md`, `docs/DESIGN_SYSTEM.md` (rimuove nota "step futuro").

---

## DECISIONE APERTA (mi serve il tuo OK)

La bottom-nav oggi ha **5** voci (Home, Portafoglio, Classifica, Engage, Wallet). Aggiungendo "Mercato" diventano **6**. Opzioni:
- **(A) 6 tab** — Home · Mercato · Portafoglio · Classifica · Engage · Wallet. Semplice, ma su telefoni stretti è denso (label 8.5px).
- **(B) 5 tab** — Home(bento) · Mercato · Portafoglio · Classifica · Wallet; **Engage** spostata in header (come Profilo) o dentro un hub. Meno denso, ma sposta Engage.

Procedo con **(A)** salvo tua diversa indicazione (reversibile).

---

## Task 1 — Sposta la tabella mercato in `market.tsx`

**Files:** Create `frontend/app/(tabs)/market.tsx`

- [ ] **Step 1:** Copiare **verbatim** l'attuale `home.tsx` in `market.tsx`, rinominando il componente `Home`→`Market`. Mantenere ricerca, filtri ruolo/nazione/squadra, `ResponsiveTable`, sparkline, navigazione riga→`/player/[id]`. Mantenere i testID esistenti (`home-search-input`, ecc.) per non rompere screenshot.
- [ ] **Step 2:** `npx tsc --noEmit` verde.
- [ ] **Step 3:** Commit `feat(nav): tabella mercato in tab dedicata /market`.

## Task 2 — `BentoCard` (frame finestra condiviso)

**Files:** Create `frontend/src/components/BentoCard.tsx`

- [ ] **Step 1:** Componente presentational, finestra lime 2px:
```tsx
import { type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';
import { useTheme } from '@/src/theme/ThemeProvider';
import { borderWindowW, radius, spacing, typography } from '@/src/theme/spacing';

export function BentoCard({
  title, action, onAction, children, style, testID,
}: { title?: string; action?: string; onAction?: () => void; children: ReactNode; style?: ViewStyle; testID?: string }) {
  const { colors } = useTheme();
  return (
    <View testID={testID} style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.borderWindow }, style]}>
      {(title || action) && (
        <View style={styles.head}>
          {!!title && <Text style={[typography.monoLabel, { color: colors.muted }]}>{title}</Text>}
          {!!action && (
            <Pressable onPress={onAction} hitSlop={8}>
              <Text style={[typography.monoLabel, { color: colors.accent }]}>{action} ›</Text>
            </Pressable>
          )}
        </View>
      )}
      {children}
    </View>
  );
}
const styles = StyleSheet.create({
  card: { borderRadius: radius.window, borderWidth: borderWindowW, padding: spacing.md, gap: spacing.sm, overflow: 'hidden' },
  head: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
});
```
- [ ] **Step 2:** `npx tsc --noEmit` verde. Commit `feat(ui): BentoCard finestra condivisa`.

## Task 3 — News placeholder

**Files:** Create `frontend/src/content/newsPlaceholder.ts`

- [ ] **Step 1:**
```ts
export interface NewsItem { source: string; title: string; url: string; }
// PLACEHOLDER statico — il feed RSS reale è uno step separato.
export const NEWS_PLACEHOLDER: NewsItem[] = [
  { source: 'PlayerStock', title: 'Il feed news arriva presto: qui le notizie del giorno.', url: 'https://example.com' },
  { source: 'Mercato', title: 'Analisi dei movimenti di prezzo della settimana.', url: 'https://example.com' },
  { source: 'Community', title: 'Le posizioni più seguite dai trader.', url: 'https://example.com' },
];
```
- [ ] **Step 2:** Commit `feat(ui): news placeholder statiche`.

## Task 4 — Riscrittura `home.tsx` (bento)

**Files:** Modify `frontend/app/(tabs)/home.tsx`

- [ ] **Step 1 — data loading:** `home.tsx` carica in parallelo, con stato per-sezione (loading/data/error indipendenti):
  `getMarketOverview()`, `getPortfolio()`, `getLeaderboard()`. Dal market overview deriva `talent = top_gainers[0]`; se presente, `getPriceHistory(talent.athlete_id, 14)` per la sparkline.
- [ ] **Step 2 — layout responsive:** `useResponsive().isDesktop`. ScrollView; contenitore con `maxWidth 1200, alignSelf center`.
  - Desktop: `flexDirection:'row', gap` — colonna principale `{ flex: 2 }` (bento) + colonna News `{ flex: 1 }`.
  - Mobile: `flexDirection:'column'` — bento, poi News in fondo.
- [ ] **Step 3 — moduli (componenti locali in home.tsx, dati passati per prop; finestra = `BentoCard`):**
  - **MatchDayHero**: `BentoCard` larghezza piena. Badge "IN ARRIVO" (pill `surfaceAlt`/`muted`), titolo "Match day", sottotesto "Presto: la giornata live muoverà i prezzi." Nessun onPress/logica.
  - **PortfolioMini**: `BentoCard title="PORTAFOGLIO" action="APRI" onAction→/(tabs)/portfolio`. Mostra `formatEuro(total_equity)` grande (`typography.mono`, `colors.text`) + `pnl_pct`/`pnl_abs` colorati `colors.up/down`. Fallback "—" se non caricato.
  - **RankMini**: `BentoCard title="POSIZIONE" action="CLASSIFICA" onAction→/(tabs)/leaderboard`. `#{self.rank}` grande + `su {total_users}`. Fallback "—".
  - **MarketMini**: `BentoCard title="MERCATO" action="VEDI TUTTO" onAction→/(tabs)/market`. Riga stat compatte (cap totale, volume 24h, attivi) + lista 3 top mover (nome + var% colorata). Le righe mover usano `borderBottomColor: colors.border` (sotto-elementi, NON lime).
  - **TalentCard**: `BentoCard title="TALENTO DEL GIORNO" action="DETTAGLIO" onAction→/player/[talent.athlete_id]`. Nome best gainer + `+{var_pct}%` (`colors.up`) + `Sparkline` (se serie disponibile). Nota "miglior variazione di oggi".
  - **NewsColumn**: `BentoCard title="NEWS DEL GIORNO"` contenente 3 righe da `NEWS_PLACEHOLDER`: sorgente in `colors.accent` (oro) + titolo `colors.text`, ogni riga `Pressable`→`Linking.openURL(item.url)`, separatore `colors.border`. Badge "ANTEPRIMA".
- [ ] **Step 4:** Stati: ogni `*Mini` mostra `StateView`/fallback testuale se la sua fetch fallisce (es. Atlas down) senza rompere le altre. `formatEuro`/`formatPrice` da `utils/formatters`.
- [ ] **Step 5:** `npx tsc --noEmit` verde. Commit `feat(home): dashboard bento Luxury (impaginazione B)`.

## Task 5 — Navigazione (`_layout.tsx`)

**Files:** Modify `frontend/app/(tabs)/_layout.tsx`

- [ ] **Step 1:** Aggiungere `market: 'stats-chart-outline'` a `TAB_ICON` e cambiare `home` → `'grid-outline'`.
- [ ] **Step 2:** Inserire `{screen('market', t('tabs.market'))}` subito dopo `home` (ordine opzione A).
- [ ] **Step 3:** `npx tsc --noEmit` verde. Commit `feat(nav): tab Mercato + icona bento home`.

## Task 6 — i18n

**Files:** Modify `frontend/src/i18n/locales/it/common.json`, `frontend/src/i18n/locales/en/common.json`

- [ ] **Step 1:** Aggiungere chiavi: `tabs.market`, `home.matchday_title/subtitle/soon`, `home.portfolio/position/market/talent/news_title`, `home.see_all/open/leaderboard/detail`, `home.talent_hint`, `home.news_preview`. (IT primario; le altre lingue fanno fallback — coerente con stato i18n attuale.)
- [ ] **Step 2:** Commit `i18n: chiavi home bento + tab mercato`.

## Task 7 — Docs

**Files:** Modify `PROJECT_SPEC.md`, `ROADMAP.md`, `docs/DESIGN_SYSTEM.md`

- [ ] **Step 1:** `DESIGN_SYSTEM.md` §3: rimuovere il blocco "STEP FUTURO …" e marcare il bento come **implementato** (Match day + News = placeholder in attesa di feature #2/#6 e feed RSS).
- [ ] **Step 2:** `PROJECT_SPEC.md`/`ROADMAP.md`: home = dashboard bento; tabella mercato in tab Mercato.
- [ ] **Step 3:** Commit `docs: bento home implementato; DESIGN_SYSTEM aggiornato`.

## Task 8 — Verifica

- [ ] **Step 1:** `cd backend; .venv\Scripts\python -m pytest -q` → **270 passed** (nessun endpoint nuovo → invariato).
- [ ] **Step 2:** `cd frontend; npx tsc --noEmit` → 0 errori.
- [ ] **Step 3:** `npx expo export -p web` → build pulita.
- [ ] **Step 4:** Screenshot (serve `dist` col backend reale, come già fatto): home **desktop** (2 colonne) + **mobile** (1 colonna, news in fondo) + tab Mercato. Salva in `.tmp_shots/`. Verifica: bordi finestra lime sui pannelli, sotto-elementi subtle, accento oro, Match day/News marcati placeholder.

---

## Self-Review
- **Copertura:** bento 2col/1col ✔ T4; market spostato ✔ T1; moduli reali (portafoglio/posizione/mercato/talento) ✔ T4; placeholder (matchday/news) marcati ✔ T3/T4; nav aggiornata ✔ T5; nessun endpoint nuovo → test backend invariati ✔ T8; docs + DESIGN_SYSTEM nota rimossa ✔ T7.
- **Regola finestra:** pannelli top-level via `BentoCard` (lime 2px); righe interne (mover, news) su `colors.border`. ✔
- **Rischi:** densità bottom-nav a 6 tab (decisione A/B aperta sopra). Talento dipende da `top_gainers` non vuoto → fallback "—" se mercato non carica.
