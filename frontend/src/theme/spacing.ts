import type { TextStyle } from 'react-native';

import { fonts } from './tokens';

/** Tipa ogni preset come TextStyle (evita union ViewStyle|TextStyle in StyleSheet.create). */
const t = (s: TextStyle): TextStyle => s;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radius = {
  sm: 6,
  md: 10,
  lg: 14,
  card: 16,    // card standard (DESIGN_SYSTEM: finestra radius 16)
  window: 16,  // card "finestra" top-level (bordo lime 2px)
  pill: 999,
} as const;

/** Spessore bordo box standard (sotto-elementi/subtle). */
export const borderW = 1.75;
/** Spessore bordo finestra (card top-level, lime). */
export const borderWindowW = 2;

/**
 * Tipografia. Tre famiglie (DESIGN_SPEC):
 *  - mono  → header/label/numeri (JetBrains Mono)
 *  - serif → titoli editoriali occasionali (Fraunces)
 *  - sans  → corpo (Inter)
 */
export const typography = {
  // titoli di pagina (Space Grotesk bold)
  pageTitle: t({ fontFamily: fonts.title, fontSize: 28, fontWeight: '700', letterSpacing: -0.5 }),
  h1: t({ fontFamily: fonts.title, fontSize: 28, fontWeight: '700', letterSpacing: -0.5 }),
  h2: t({ fontFamily: fonts.title, fontSize: 22, fontWeight: '700' }),
  h3: t({ fontFamily: fonts.title, fontSize: 18, fontWeight: '600' }),
  // serif editoriale (accento occasionale)
  display: t({ fontFamily: fonts.serif, fontSize: 30, fontWeight: '600', letterSpacing: -0.5 }),
  // corpo (sans)
  body: t({ fontFamily: fonts.sans, fontSize: 14, fontWeight: '400', lineHeight: 20 }),
  bodyBold: t({ fontFamily: fonts.sans, fontSize: 14, fontWeight: '600', lineHeight: 20 }),
  small: t({ fontFamily: fonts.sans, fontSize: 12, fontWeight: '400', lineHeight: 16 }),
  // label/numeri (mono)
  caption: t({ fontFamily: fonts.mono, fontSize: 11, fontWeight: '400', letterSpacing: 0.4, textTransform: 'uppercase' }),
  mono: t({ fontFamily: fonts.mono, fontSize: 14, fontWeight: '500', fontVariant: ['tabular-nums'] }),
  // header/nav: mono maiuscolo, ampio tracking
  monoLabel: t({ fontFamily: fonts.mono, fontSize: 11, fontWeight: '600', letterSpacing: 1.6, textTransform: 'uppercase' }),
  wordmark: t({ fontFamily: fonts.mono, fontSize: 15, fontWeight: '700', letterSpacing: 2 }),
} as const;
