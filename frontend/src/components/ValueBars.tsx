import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { radius, spacing, typography } from '@/src/theme/spacing';

export interface BarItem { label: string; value: number; ref?: number; tint?: string; }

/**
 * Barre orizzontali per la scomposizione del valore (score/età/minuti/squadra/ruolo).
 * `value` normalizzato su `ref` (default 1.0 = neutro). Sobrio, colore dal token.
 */
export function ValueBars({ items, neutral = 1.0 }: { items: BarItem[]; neutral?: number }) {
  const { colors } = useTheme();
  const maxV = Math.max(neutral, ...items.map((i) => i.value)) * 1.05;
  return (
    <View style={{ gap: spacing.sm }}>
      {items.map((it) => {
        const tint = it.tint ?? (it.value >= neutral ? colors.cyan : colors.amber);
        const pct = Math.max(0.02, Math.min(1, it.value / maxV));
        return (
          <View key={it.label} style={styles.row}>
            <Text style={[typography.caption, styles.label, { color: colors.muted }]}>{it.label}</Text>
            <View style={[styles.track, { backgroundColor: colors.surfaceAlt }]}>
              <View style={[styles.fill, { width: `${pct * 100}%`, backgroundColor: tint }]} />
            </View>
            <Text style={[typography.mono, styles.val, { color: colors.text }]}>{it.value.toFixed(2)}</Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  label: { width: 64 },
  track: { flex: 1, height: 8, borderRadius: radius.pill, overflow: 'hidden' },
  fill: { height: 8, borderRadius: radius.pill },
  val: { width: 44, textAlign: 'right', fontSize: 12 },
});
