# Luxury Identity Re-theme — Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Applicare la nuova identità visiva "Luxury" (carbone+oro, bordo finestra lime 2px, font Manrope) a TUTTE le schermate esistenti, rimappando i token del tema scuro e collassando a un singolo tema. Nessuna nuova feature, nessun bento.

**Architecture:** Il tema è già centralizzato (`src/theme/tokens.ts` → `useTheme().colors` + preset `typography`). Si rimappano i VALORI dei token mantenendo le CHIAVI esistenti (così le ~20 schermate che leggono `colors.*`/`typography.*` si aggiornano a cascata senza toccare i call-site). Si rimuove il tema chiaro e il toggle. Si introduce il trattamento card "finestra" (bordo lime 2px, radius 16) sui pannelli top-level; i sotto-elementi restano su `border-subtle`.

**Tech Stack:** Expo / React Native / expo-router, TypeScript, tema custom, Manrope via Google Fonts (web) + `@expo-google-fonts/manrope` (native).

**Vincoli:** branch `feat/run-app-web`, niente merge. Responsive web+mobile. 269 test backend verdi. Nessuna regressione funzionale.

---

## File Structure

**Creati:**
- `docs/DESIGN_SYSTEM.md` — nuova fonte di verità (token + bento "impaginazione B" + Manrope + regola finestra).

**Modificati (tema/infra):**
- `frontend/src/theme/tokens.ts` — remap valori, font Manrope, nuovi token (`borderWindow`, `barBg`, `avatarBg`, `avatarFg`), rimozione `lightRaw`/`themes.light`, remap `gradients` su palette oro.
- `frontend/src/theme/spacing.ts` — `radius.card` 18→16, `radius.window` 16; typography invariata (eredita Manrope dai `fonts`).
- `frontend/src/theme/ThemeProvider.tsx` — tema singolo: rimuove `scheme`/`toggle`/`setScheme`/storage; `colors` fisso, `isDark` sempre true (compat).
- `frontend/app/+html.tsx` — Google Fonts → Manrope; `body` bg `#0E1320`→`#12110f`.
- `frontend/app/_layout.tsx` — carica Manrope (native), StatusBar fisso `light`.
- `frontend/src/hooks/use-icon-fonts.ts` — aggiunge Manrope alla mappa font caricata.

**Modificati (chrome single-theme + finestra):**
- `frontend/src/components/chrome/ThemeToggle.tsx` — RIMOSSO (file eliminato).
- `frontend/src/components/chrome/AppHeader.tsx` — rimuove `ThemeToggle`; bar usa `barBg`; login button `accent`.
- `frontend/app/(tabs)/_layout.tsx` — tabbar/header usano `barBg`; `tabBarActiveTintColor` = `accent`.
- `frontend/src/components/Card.tsx` — prop `window?: boolean` (lime 2px / radius 16).
- `frontend/src/components/StatTile.tsx` — finestra lime + topBar gradiente oro.
- `frontend/src/components/VividCard.tsx` — finestra lime, glow ammorbidito (Luxury piatto).

**Modificati (audit hex hardcoded):**
- `frontend/app/(auth)/login.tsx`, `frontend/app/(tabs)/engage.tsx`, `frontend/app/player/[id].tsx`, `frontend/src/components/TeamBadge.tsx` — sostituire hex con token.

**Modificati (docs):**
- `DESIGN_SPEC.md` (banner SUPERSEDED), `PROJECT_SPEC.md`, `ROADMAP.md`, `DECISIONS.md` (D11, D12).

---

## Palette — mappa token vecchio→nuovo (chiave invariata, valore nuovo)

| chiave token | valore nuovo | nota |
|---|---|---|
| `bg` | `#12110f` | carbone |
| `surface` | `#1d1a16` | |
| `surfaceAlt` | `#26221b` | = surface-2 |
| `border` | `#34302a` | = border-subtle (DEFAULT) |
| `text` | `#f3eee4` | |
| `muted` | `#9a907f` | |
| `cyan` | `#cda24f` | ex-primario → oro |
| `teal` | `#cda24f` | accento oro |
| `purple` | `#b8893f` | bronzo (distinzione tenue per tint ruoli/chart) |
| `green` | `#9bc08a` | = up |
| `amber` | `#cda24f` | prezzo/valore = oro (coerente con accent) |
| `red` | `#cf8170` | = down |
| `chartBlue` | `#9a907f` | neutro caldo |

**Nuovi token (in `Extra`):** `barBg #1a1813`, `borderWindow #c6ff00` (lime), `avatarBg #2c281f`, `avatarFg #cda24f`.
**Alias:** `accent=#cda24f`, `gold=#cda24f`, `onAccent=#1d1a16`, `onGold=#1d1a16`, `up=#9bc08a`, `down=#cf8170`.
**Gradients** (Luxury piatto, niente neon): tutti → coppie oro/bronzo, es. `['#cda24f','#b8893f']`; `green`→`['#9bc08a','#7fa06f']`; `pink`/`red`→`['#cf8170','#b86a5a']`.

---

## Task 1 — `docs/DESIGN_SYSTEM.md` (fonte di verità)

**Files:** Create `docs/DESIGN_SYSTEM.md`

- [ ] **Step 1:** Creare il documento con: token colore (tabella sopra), regola FINESTRA (card = surface + bordo lime 2px + radius 16; sotto-elementi = border-subtle), font Manrope (400–800), nota "tema singolo scuro", e sezione "Bento — impaginazione B" (hero match day · portafoglio · posizione · mercato · talento + colonna destra News 1/3; mobile = 1 colonna) marcata **STEP FUTURO (dipende da match-day #2 e talento #6)**.
- [ ] **Step 2:** Commit `docs(design): DESIGN_SYSTEM.md fonte di verità (Luxury, lime, Manrope, bento B futuro)`.

## Task 2 — Remap token + font + single-theme (`tokens.ts`)

**Files:** Modify `frontend/src/theme/tokens.ts`

- [ ] **Step 1:** Sostituire `darkRaw` coi valori nuovi; ELIMINARE `lightRaw`. `RawColors` invariata (chiavi uguali).
- [ ] **Step 2:** In `Extra`/`build`: `onAccent='#1d1a16'`; aggiungere `barBg`, `borderWindow`, `avatarBg`, `avatarFg`; remap alias (`accent/gold`→`#cda24f`, `up/down`, `onGold='#1d1a16'`); `grid='rgba(243,238,228,0.04)'`, `overlay='rgba(243,238,228,0.06)'`, banner oro-tinto. Rimuovere i rami `isDark ? : ` legati a light (tema unico → ramo dark).
- [ ] **Step 3:** `themes = { dark: build(darkRaw,'dark') }` (rimuovere `light`). `Scheme` resta `'dark'` solo.
- [ ] **Step 4:** Remap `gradients` su coppie oro/bronzo (vedi sopra).
- [ ] **Step 5:** `fonts`: tutte le famiglie → Manrope (`'"Manrope", system-ui, -apple-system, sans-serif'`), inclusa `mono` (i numeri restano leggibili via `fontVariant:['tabular-nums']` già in `typography.mono`).
- [ ] **Step 6:** `npx tsc --noEmit` in `frontend` → deve passare (gli usi di `colors.light`/`themes.light` non esistono; verificare nessun riferimento residuo a `themes.light`).
- [ ] **Step 7:** Commit `feat(theme): remap token su identità Luxury + Manrope + tema unico`.

## Task 3 — `spacing.ts` (radius finestra)

**Files:** Modify `frontend/src/theme/spacing.ts`

- [ ] **Step 1:** `radius.card: 16` (era 18); aggiungere `window: 16`. Resto invariato.
- [ ] **Step 2:** Commit `feat(theme): radius finestra 16`.

## Task 4 — Collasso tema singolo (Provider, layout, toggle)

**Files:** Modify `ThemeProvider.tsx`, `app/_layout.tsx`; Delete `chrome/ThemeToggle.tsx`; Modify `chrome/AppHeader.tsx`, `(tabs)/_layout.tsx`

- [ ] **Step 1:** `ThemeProvider.tsx`: ridurre il context a `{ colors, isDark:true }` (mantenere `isDark` per compat con call-site). Rimuovere `scheme`, `toggle`, `setScheme`, storage, `useEffect`. `useTheme()` resta. NB: mantenere export `useTheme` e shape minima per non rompere chi destruttura `colors`.
- [ ] **Step 2:** `chrome/ThemeToggle.tsx`: eliminare il file.
- [ ] **Step 3:** `AppHeader.tsx`: rimuovere import+uso `<ThemeToggle/>`; `bar` → `colors.barBg`; bottone LOGIN → `colors.accent` + testo `colors.onAccent`.
- [ ] **Step 4:** `(tabs)/_layout.tsx`: header/tabbar `backgroundColor: colors.barBg`; `tabBarActiveTintColor: colors.accent`; bordi `colors.border`.
- [ ] **Step 5:** `_layout.tsx`: `StatusBar style="light"` fisso (rimuovere `isDark` ternario se si preferisce, oppure lasciare — `isDark` è true).
- [ ] **Step 6:** Grep di sicurezza: nessun residuo `toggle(`/`setScheme`/`ThemeToggle` nel codice. `npx tsc --noEmit` verde.
- [ ] **Step 7:** Commit `feat(theme): tema singolo Luxury — ritira toggle e tema chiaro`.

## Task 5 — Trattamento "finestra" lime sui pannelli top-level

**Files:** Modify `Card.tsx`, `StatTile.tsx`, `VividCard.tsx`

- [ ] **Step 1:** `Card.tsx`: aggiungere prop `window?: boolean`. Se `window`: `borderColor: colors.borderWindow, borderWidth: 2, borderRadius: radius.window`; altrimenti subtle come ora.
- [ ] **Step 2:** `StatTile.tsx`: card top-level → `borderColor: colors.borderWindow, borderWidth: 2, borderRadius: radius.window`; `topBar` resta gradiente (ora oro).
- [ ] **Step 3:** `VividCard.tsx`: bordo finestra lime 2px; ridurre `glow` (Luxury piatto: `shadowOpacity` ~0.2 o rimosso); `INK`/testi → restano scuri su riempimento oro (leggibilità ok).
- [ ] **Step 4:** `npx tsc --noEmit` verde.
- [ ] **Step 5:** Commit `feat(theme): card "finestra" bordo lime 2px (StatTile/VividCard/Card)`.

## Task 6 — Re-skin pannelli principali per schermata + audit hex

Regola: pannello/contenitore TOP-LEVEL di ogni schermata = finestra lime; righe lista / sotto-card = `border-subtle`.

**Files:** Modify `app/(tabs)/home.tsx`, `portfolio.tsx`, `leaderboard.tsx`, `wallet.tsx`, `engage.tsx`, `profile.tsx`, `how-it-works.tsx`, `player/[id].tsx`, `(auth)/{welcome,login,consent}.tsx`; `TeamBadge.tsx`

- [ ] **Step 1 (audit hex):** sostituire hex hardcoded con token: `+html.tsx` body `#12110f`; `engage.tsx` `INK` → `colors.onAccent`; `login.tsx` `errorBox`/`errorText` → `colors.danger`/token; `player/[id].tsx` `#FFF` → `colors.onAccent`/`colors.text`; `TeamBadge.tsx` fallback `#222A36`→`colors.avatarBg`, testo `#FFF`→`colors.text`. `VividCard` `INK` resta (inchiostro su oro).
- [ ] **Step 2:** Per ogni schermata: il pannello principale (es. tabella mercato in `home`, card totali in `portfolio`, hub in `wallet`) adotta il bordo finestra lime; chip/righe restano `colors.border`. Verificare che chip "attivo" usi `colors.accent` (oro) non più cyan.
- [ ] **Step 3:** `npx tsc --noEmit` verde.
- [ ] **Step 4:** Commit `feat(theme): re-skin Luxury di tutte le schermate + audit hex`.

## Task 7 — Manrope su native

**Files:** Modify `frontend/src/hooks/use-icon-fonts.ts` (o `_layout.tsx`), `frontend/package.json`

- [ ] **Step 1:** `npm install @expo-google-fonts/manrope` in `frontend`.
- [ ] **Step 2:** Caricare i pesi Manrope (400/500/600/700/800) via `useFonts` insieme alle icone (estendere la mappa in `use-icon-fonts.ts` o aggiungere `useFonts(Manrope_*)` in `_layout.tsx`, gating splash invariato).
- [ ] **Step 3:** Commit `feat(theme): bundle Manrope su native`.

## Task 8 — Docs di progetto

**Files:** Modify `DESIGN_SPEC.md`, `PROJECT_SPEC.md`, `ROADMAP.md`, `DECISIONS.md`

- [ ] **Step 1:** `DESIGN_SPEC.md`: banner in testa `> ⚠️ SUPERSEDED da docs/DESIGN_SYSTEM.md (vedi D12). Mantenuto come storico.`
- [ ] **Step 2:** `DECISIONS.md`: **D11** (identità visiva bloccata: Luxury carbone+oro, bordo finestra lime 2px, bento "impaginazione B", Manrope) e **D12** (tema singolo scuro; ritiro toggle/tema chiaro; DESIGN_SPEC superato).
- [ ] **Step 3:** `PROJECT_SPEC.md` e `ROADMAP.md`: aggiornare la riga "Design pass" → identità Luxury applicata a tutte le schermate; bento "impaginazione B" = step futuro (dipende da match-day #2 e talento #6).
- [ ] **Step 4:** Commit `docs: D11/D12 identità Luxury + tema unico; DESIGN_SPEC superseded`.

## Task 9 — Verifica finale

- [ ] **Step 1:** Backend test suite: `cd backend; python -m pytest -q` → **269 passed**, nessun fallimento (re-theme è frontend-only; deve restare verde).
- [ ] **Step 2:** `cd frontend; npx tsc --noEmit` → 0 errori.
- [ ] **Step 3:** Build web export di sanity: `cd frontend; npx expo export -p web` → completa senza errori.
- [ ] **Step 4:** Screenshot Playwright (msedge) di home + 2 schermate (mobile+desktop) per confronto visivo Luxury; salva in `.tmp_shots/`. Verificare: bordi finestra lime, accent oro, font Manrope, niente residui cyan/neon, niente toggle in header.
- [ ] **Step 5:** Aggiornare memoria `design-system.md` con la nuova identità (sostituisce direzione neon).

---

## Self-Review

- **Copertura spec:** (1) tema centralizzato Luxury ✔ T2–T3; (2) applicato a tutte le schermate ✔ T5–T6; tema singolo ✔ T4; Manrope web+native ✔ T2/T7; finestra lime ✔ T5–T6; DESIGN_SYSTEM.md ✔ T1; DESIGN_SPEC superseded ✔ T8; D11/D12/PROJECT_SPEC/ROADMAP ✔ T8; 269 test + responsive ✔ T9.
- **Rischi:** mappare `cyan/teal/amber`→stesso oro riduce la differenziazione cromatica dei tint ruolo (ATT/CC/DIF/POR) e delle stat tile → accettato per coerenza Luxury; differenziazione residua via `purple→bronzo`, `up/down`. Da validare visivamente in T9 Step 4.
- **Decisione aperta minore:** quali pannelli sono "finestre" vs sotto-elementi è giudizio per-schermata (T6 Step 2) → la regola è in DESIGN_SYSTEM.md; checkpoint visivo in T9.
