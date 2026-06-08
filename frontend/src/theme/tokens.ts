/**
 * PlayerStock — Design tokens.
 * Identità: LUXURY — carbone + oro. Finestre con BORDO LIME 2px. Tema UNICO scuro.
 * ACCENTO = ORO (#cda24f): prezzo/valore, stato attivo, CTA. Lime (#c6ff00) = SOLO
 * bordo delle card "finestra" top-level (mai sui sotto-elementi).
 * Fonte di verità: docs/DESIGN_SYSTEM.md (DESIGN_SPEC.md è SUPERSEDED — D11/D12).
 * Le schermate NON hardcodano colori: useTheme().colors (o `@/src/theme/colors`).
 */

export type Scheme = 'dark';

interface RawColors {
  bg: string; surface: string; surfaceAlt: string; border: string;
  text: string; muted: string;
  cyan: string; teal: string; purple: string;
  green: string; amber: string; red: string; chartBlue: string;
}

// Tema unico Luxury. NB: le CHIAVI storiche (cyan/teal/purple/amber…) sono mantenute
// per compat con i call-site, ma i VALORI sono rimappati sulla palette carbone+oro.
const darkRaw: RawColors = {
  bg: '#12110f',        // carbone
  surface: '#1d1a16',
  surfaceAlt: '#26221b', // surface-2
  border: '#34302a',     // border-subtle (DEFAULT, NON lime)
  text: '#f3eee4',
  muted: '#9a907f',
  cyan: '#cda24f',    // ex-primario → oro
  teal: '#cda24f',    // accento oro
  purple: '#b8893f',  // bronzo (distinzione tenue per tint ruoli/chart)
  green: '#9bc08a',   // positivo / up
  amber: '#cda24f',   // prezzo / valore = oro (coerente con accent)
  red: '#cf8170',     // negativo / down
  chartBlue: '#9a907f', // neutro caldo
};

interface Extra {
  scheme: Scheme;
  isDark: boolean;
  onAccent: string;      // inchiostro scuro su riempimenti oro
  barBg: string;         // header + bottom tab bar
  borderWindow: string;  // LIME — bordo finestra 2px (solo card top-level)
  avatarBg: string;
  avatarFg: string;
  borderStrong: string;
  grid: string;          // texture geometrica (bassissima opacità)
  overlay: string;       // velo stati premuti
  bannerBg: string;
  bannerBorder: string;
  bannerText: string;
  // alias semantici / legacy
  accent: string;        // ORO
  accentHover: string;
  gold: string;          // = accent
  goldDim: string;
  onGold: string;        // = onAccent
  up: string;
  down: string;
  success: string;
  danger: string;
  warning: string;
  bgElevated: string;
  card: string;
  cardHover: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  textInverted: string;
}

function build(raw: RawColors, scheme: Scheme): RawColors & Extra {
  return {
    ...raw,
    scheme,
    isDark: true,
    onAccent: '#1d1a16',
    barBg: '#1a1813',
    borderWindow: '#c6ff00',
    avatarBg: '#2c281f',
    avatarFg: '#cda24f',
    borderStrong: '#403a31',
    grid: 'rgba(243,238,228,0.04)',
    overlay: 'rgba(243,238,228,0.06)',
    bannerBg: '#1f1a10',
    bannerBorder: '#3a2e12',
    bannerText: '#cda24f',
    // alias
    accent: raw.amber,        // oro
    accentHover: raw.amber,
    gold: raw.amber,
    goldDim: '#a8843f',
    onGold: '#1d1a16',
    up: raw.green,
    down: raw.red,
    success: raw.green,
    danger: raw.red,
    warning: raw.amber,
    bgElevated: raw.surface,
    card: raw.surface,
    cardHover: raw.surfaceAlt,
    textPrimary: raw.text,
    textSecondary: raw.muted,
    textMuted: raw.muted,
    textInverted: raw.bg,
  };
}

export const themes = {
  dark: build(darkRaw, 'dark'),
} as const;

export type ThemeColors = typeof themes.dark;

/** Gradienti di brand — Luxury PIATTO (oro/bronzo), niente neon/glow forte. */
export const gradients = {
  cyanTeal: ['#cda24f', '#b8893f'] as [string, string],
  teal: ['#cda24f', '#b8893f'] as [string, string],
  purple: ['#b8893f', '#cda24f'] as [string, string],
  green: ['#9bc08a', '#7fa06f'] as [string, string],
  amber: ['#cda24f', '#b8893f'] as [string, string],
  pink: ['#cf8170', '#b86a5a'] as [string, string],
};

/** Font: Manrope (web via app/+html.tsx; @expo-google-fonts/manrope su nativo). */
export const fonts = {
  title: '"Manrope", system-ui, -apple-system, sans-serif',
  sans: '"Manrope", system-ui, -apple-system, sans-serif',
  mono: '"Manrope", ui-monospace, system-ui, sans-serif',
  serif: '"Manrope", system-ui, -apple-system, sans-serif',
} as const;
