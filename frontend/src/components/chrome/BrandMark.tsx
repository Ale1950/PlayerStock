import { Circle, Polyline, Svg } from 'react-native-svg';

import { useTheme } from '@/src/theme/ThemeProvider';

/**
 * Marchio PlayerStock — proprietario, tema calcio + mercato.
 * Cerchio (pallone) inscritto con una linea di trend ascendente (mercato).
 * NESSUN richiamo ad ape/nido d'ape o loghi altrui.
 */
export function BrandMark({ size = 24, color }: { size?: number; color?: string }) {
  const { colors } = useTheme();
  const c = color ?? colors.cyan;
  return (
    <Svg width={size} height={size} viewBox="0 0 32 32">
      <Circle cx={16} cy={16} r={13} stroke={c} strokeWidth={2} fill="none" />
      <Polyline
        points="8,21 14,15 18,18 24,10"
        stroke={c}
        strokeWidth={2.2}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <Polyline points="24,15 24,10 19,10" stroke={c} strokeWidth={2.2} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}
