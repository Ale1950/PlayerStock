/**
 * PlayerStock — Colori (compat layer).
 *
 * Sorgente unica dei token: ./tokens.ts. Questo modulo esporta il tema SCURO
 * come `colors` per le schermate ANCORA statiche (import { colors }). Le
 * schermate convertite leggono i colori reattivi da useTheme().colors.
 * NON aggiungere colori qui: aggiungili in tokens.ts.
 */
import { themes } from './tokens';

export const colors = themes.dark;

export type AppColors = typeof colors;
