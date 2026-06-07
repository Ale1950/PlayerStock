import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { spacing, typography } from '@/src/theme/spacing';

export interface TickerItem {
  label: string;
  value: string;
  tone?: 'gold' | 'green' | 'red' | 'cyan' | 'muted';
}

/** Striscia di stato mono sotto l'header: "LABEL: valore · LABEL: valore". */
export function StatusTicker({ items }: { items?: TickerItem[] }) {
  const { colors } = useTheme();
  const tone = (t?: TickerItem['tone']) =>
    t === 'green' ? colors.green
    : t === 'red' ? colors.red
    : t === 'cyan' ? colors.cyan
    : t === 'muted' ? colors.muted
    : colors.gold;

  const data: TickerItem[] = items ?? [
    { label: 'MERCATO', value: 'APERTO', tone: 'green' },
    { label: 'VALUTA', value: '€ (VIRTUALE)', tone: 'gold' },
    { label: 'NACKL', value: 'PLACEHOLDER', tone: 'muted' },
  ];

  return (
    <View style={[styles.bar, { backgroundColor: colors.bg, borderBottomColor: colors.border }]}>
      {data.map((it, i) => (
        <View key={it.label} style={styles.group}>
          {i > 0 && <Text style={[styles.sep, { color: colors.border }]}>·</Text>}
          <Text style={[typography.caption, { color: colors.muted }]}>{it.label}: </Text>
          <Text style={[typography.caption, { color: tone(it.tone) }]}>{it.value}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap',
    paddingHorizontal: spacing.md, paddingVertical: 6, borderBottomWidth: 1, gap: spacing.xs,
  },
  group: { flexDirection: 'row', alignItems: 'center' },
  sep: { marginHorizontal: spacing.xs },
});
