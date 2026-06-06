import { Defs, LinearGradient, Path, Stop, Svg } from 'react-native-svg';

import { useTheme } from '@/src/theme/ThemeProvider';

function linePath(vals: number[], width: number, height: number, pad: number): string {
  if (vals.length < 2) return '';
  const min = Math.min(...vals), max = Math.max(...vals), range = max - min || 1;
  const h = height - pad * 2, step = width / (vals.length - 1);
  return vals.map((p, i) => `${i === 0 ? 'M' : 'L'}${(i * step).toFixed(1)},${(pad + h - ((p - min) / range) * h).toFixed(1)}`).join(' ');
}

/**
 * Grafico prezzo/equity SOBRIO: linea + area a gradiente. Niente glow.
 * `overlay` (opzionale) = seconda serie NORMALIZZATA indipendente (confronto), cyan tratteggiata.
 */
export function PriceChart({
  prices, overlay, width = 320, height = 120, testID,
}: { prices: number[]; overlay?: number[]; width?: number; height?: number; testID?: string }) {
  const { colors } = useTheme();
  if (!prices || prices.length < 2) {
    return <Svg width={width} height={height} testID={testID} />;
  }
  const up = prices[prices.length - 1] >= prices[0];
  const stroke = up ? colors.green : colors.red;
  const pad = 6;
  const line = linePath(prices, width, height, pad);
  const area = `${line} L${width},${height} L0,${height} Z`;
  const gid = `pc-${testID ?? 'x'}`;

  return (
    <Svg width={width} height={height} testID={testID}>
      <Defs>
        <LinearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={stroke} stopOpacity={0.28} />
          <Stop offset="1" stopColor={stroke} stopOpacity={0} />
        </LinearGradient>
      </Defs>
      <Path d={area} fill={`url(#${gid})`} />
      <Path d={line} stroke={stroke} strokeWidth={2} fill="none" strokeLinejoin="round" strokeLinecap="round" />
      {overlay && overlay.length >= 2 && (
        <Path d={linePath(overlay, width, height, pad)} stroke={colors.cyan} strokeWidth={1.5} fill="none"
          strokeDasharray="4 3" strokeLinejoin="round" strokeLinecap="round" opacity={0.85} />
      )}
    </Svg>
  );
}
