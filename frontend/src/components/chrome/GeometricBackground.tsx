import { StyleSheet, View } from 'react-native';
import { Defs, Line, Pattern, Rect, Svg } from 'react-native-svg';

import { useTheme } from '@/src/theme/ThemeProvider';

/**
 * Texture geometrica generica (griglia sottile) a bassissima opacità.
 * NON è un marchio. Riempie il padre (absolute fill); va dietro al contenuto.
 */
export function GeometricBackground({ tile = 28 }: { tile?: number }) {
  const { colors } = useTheme();
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <Svg width="100%" height="100%">
        <Defs>
          <Pattern id="grid" width={tile} height={tile} patternUnits="userSpaceOnUse">
            <Line x1={0} y1={0} x2={tile} y2={0} stroke={colors.grid} strokeWidth={1} />
            <Line x1={0} y1={0} x2={0} y2={tile} stroke={colors.grid} strokeWidth={1} />
          </Pattern>
        </Defs>
        <Rect width="100%" height="100%" fill="url(#grid)" />
      </Svg>
    </View>
  );
}
