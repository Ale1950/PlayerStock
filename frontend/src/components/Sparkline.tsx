import { Polyline, Svg } from 'react-native-svg';

import { colors } from '@/src/theme/colors';

interface SparklineProps {
  prices: number[];
  width?: number;
  height?: number;
  positive?: boolean;
  testID?: string;
}

/**
 * Minimal sparkline. Pure SVG, no dipendenze grafiche pesanti.
 * `positive=true` → linea verde (up); `false` → rossa.
 */
export function Sparkline({ prices, width = 80, height = 24, positive = true, testID }: SparklineProps) {
  if (!prices || prices.length < 2) {
    return <Svg width={width} height={height} testID={testID} />;
  }
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const step = width / (prices.length - 1);
  const points = prices
    .map((p, i) => `${(i * step).toFixed(2)},${(height - ((p - min) / range) * height).toFixed(2)}`)
    .join(' ');
  return (
    <Svg width={width} height={height} testID={testID}>
      <Polyline
        points={points}
        stroke={positive ? colors.up : colors.down}
        strokeWidth={1.5}
        fill="none"
      />
    </Svg>
  );
}
