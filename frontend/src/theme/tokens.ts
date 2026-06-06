/**
 * PlayerStock — Design tokens (Fase Design).
 * Direzione: DARK NATIVO, neon su nero. PRIMARIO = CYAN/TEAL, viola secondario,
 * AMBRA = accento prezzo/valore (oro NON più primario). Intensità MISTA:
 *   - schermate DATI → sobrie (nero pieno, niente glow)
 *   - schermate REWARD/ENGAGE → vivide (gradiente + glow)
 * Fonte di verità: DESIGN_SPEC.md. Due temi: SCURO (default) e CHIARO.
 * Le schermate NON hardcodano colori: useTheme().colors (o `@/src/theme/colors` = scuro).
 */

export type Scheme = 'dark' | 'light';

interface RawColors {
  bg: string; surface: string; surfaceAlt: string; border: string;
  text: string; muted: string;
  cyan: string; teal: string; purple: string;
  green: string; amber: string; red: string; chartBlue: string;
}

const darkRaw: RawColors = {
  bg: '#0E1320',        // slate-navy morbido (era #05070A quasi-nero, troppo duro)
  surface: '#171E2E',
  surfaceAlt: '#212B40',
  border: 'rgba(255,255,255,0.12)',  // più leggibile (con bordi ~1.75px)
  text: '#EAF2F7',
  muted: '#7E8A99',
  cyan: '#22D3EE',
  teal: '#2DD4BF',
  purple: '#A78BFA',
  green: '#4ADE80',   // positivo / live
  amber: '#F5B544',   // prezzo / valore
  red: '#FB7185',     // negativo
  chartBlue: '#5B8DEF',
};

const lightRaw: RawColors = {
  bg: '#F5F7F9',
  surface: '#FFFFFF',
  surfaceAlt: '#EEF1F4',
  border: 'rgba(0,0,0,0.14)',  // bordi ~1.75px, un filo più marcati
  text: '#121821',
  muted: '#5A6472',
  cyan: '#0E9BB5',
  teal: '#0D9488',
  purple: '#7C3AED',
  green: '#15A150',
  amber: '#B8860B',
  red: '#DC4C4C',
  chartBlue: '#3B6FD4',
};

interface Extra {
  scheme: Scheme;
  isDark: boolean;
  onAccent: string;      // inchiostro scuro su riempimenti cyan/amber/teal
  borderStrong: string;
  grid: string;          // texture geometrica (bassissima opacità)
  overlay: string;       // velo stati premuti
  bannerBg: string;
  bannerBorder: string;
  bannerText: string;
  // alias semantici / legacy
  accent: string;        // PRIMARIO = cyan
  accentHover: string;   // teal
  gold: string;          // compat → amber (prezzo/valore)
  goldDim: string;
  onGold: string;        // compat → onAccent
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
  const isDark = scheme === 'dark';
  return {
    ...raw,
    scheme,
    isDark,
    onAccent: '#05070A',
    borderStrong: isDark ? '#222B36' : 'rgba(0,0,0,0.18)',
    grid: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)',
    overlay: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)',
    bannerBg: isDark ? '#14110A' : '#FBF3DD',
    bannerBorder: isDark ? '#3A2E12' : '#E4CF92',
    bannerText: isDark ? '#F5D98C' : '#7A5B12',
    // alias
    accent: raw.cyan,
    accentHover: raw.teal,
    gold: raw.amber,
    goldDim: raw.amber,
    onGold: '#05070A',
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
  light: build(lightRaw, 'light'),
} as const;

export type ThemeColors = typeof themes.dark;

/** Gradienti di brand (per bordi-superiori sobri e card vivide). 6 varianti neon. */
export const gradients = {
  cyanTeal: ['#22D3EE', '#2DD4BF'] as [string, string],
  teal: ['#2DD4BF', '#22D3EE'] as [string, string],
  purple: ['#A78BFA', '#7C3AED'] as [string, string],
  green: ['#4ADE80', '#2DD4BF'] as [string, string],
  amber: ['#F5B544', '#B8860B'] as [string, string],
  pink: ['#FB7185', '#A78BFA'] as [string, string],
};

/** Font families (web via app/+html.tsx; expo-font su nativo). */
export const fonts = {
  title: '"Space Grotesk", "Inter", system-ui, sans-serif',
  sans: '"Inter", system-ui, -apple-system, sans-serif',
  mono: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
  serif: '"Fraunces", "Playfair Display", Georgia, serif',
} as const;
