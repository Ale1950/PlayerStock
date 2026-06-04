# i18n Guide — PlayerStock

Spec autorevole: `PROJECT_SPEC.md`. Architettura: `ARCHITECTURE.md` §7.

---

## Stack
- `i18next` + `react-i18next` + `expo-localization`.
- Default locale **`it`**. Fallback **`it`** se la chiave manca.

## Struttura file
```
frontend/src/i18n/locales/
├── it/common.json     # ← unica popolata in MVP
├── en/common.json     # {} + TODO
├── es/common.json     # {}
├── fr/common.json     # {}
├── de/common.json     # {}
├── pt/common.json     # {}
├── nl/common.json     # {}
├── pl/common.json     # {}
├── ro/common.json     # {}
└── ar/common.json     # {} — RTL
```

10 lingue: **IT · EN · ES · FR · DE · PT · NL · PL · RO · AR**.

## Regole MVP
- Scrivi tutte le chiavi **solo** in `it/common.json`.
- Gli altri JSON esistono ma sono `{}` con un commento `TODO: traduzione`.
- **Nessuna stringa hardcoded** nei componenti: sempre via `t('chiave')`.

## Backend → i18n
- Gli errori API restituiscono `error_code` machine-readable + `message_it`.
- Il client mappa `error_code` → chiave i18n. Non mostrare `message_it` raw in produzione
  multilingua (è fallback/log).

## Date e numeri
- Numeri/valute via `Intl.NumberFormat` (locale corrente).
- Date via `date-fns` con locale (`date-fns/locale/it` in MVP).
- Prezzi: **4 decimali** (`DISPLAY_DECIMALS`).

## RTL
- L'arabo (`ar`) richiede RTL. Pre-configura `I18nManager` di RN ma **non forzare** in MVP.
- Evita layout che si rompono con `flexDirection` invertito: testare quando si attiva `ar`.

## Aggiungere una lingua (post-MVP)
1. Popola `locales/<lang>/common.json` con le chiavi di `it`.
2. Verifica che la lingua sia nella lista `supportedLngs` di i18next.
3. Per RTL: verificare `I18nManager.isRTL` e gli stili speculari.
