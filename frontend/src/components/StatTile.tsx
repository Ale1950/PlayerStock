import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';

type IconName = keyof typeof Ionicons.glyphMap;

/**
 * Stat tile SOBRIO (schermate dati). Card nera, bordo-superiore 2px a gradiente
 * nel colore della metrica, chip icona tinta, numero grande mono nel colore
 * metrica, label MAIUSCOLA muted + sotto-caption. Niente glow.
 */
export function StatTile({
  icon, value, label, sub, tint, gradient, style, testID,
}: {
  icon: IconName;
  value: string;
  label: string;
  sub?: string;
  tint: string;
  gradient?: [string, string];
  style?: ViewStyle;
  testID?: string;
}) {
  const { colors } = useTheme();
  const grad = gradient ?? [tint, tint];
  return (
    <View testID={testID} style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }, style]}>
      <LinearGradient colors={grad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.topBar} />
      <View style={styles.body}>
        <View style={[styles.iconChip, { backgroundColor: tint + '22' }]}>
          <Ionicons name={icon} size={18} color={tint} />
        </View>
        <Text style={[styles.value, { color: tint }]}>{value}</Text>
        <Text style={[styles.label, { color: colors.muted }]}>{label}</Text>
        {!!sub && <Text style={[styles.sub, { color: colors.muted }]}>{sub}</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.card, borderWidth: borderW, overflow: 'hidden', minWidth: 150, flex: 1 },
  topBar: { height: 2, width: '100%' },
  body: { padding: spacing.md, gap: 6 },
  iconChip: { width: 34, height: 34, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  value: { ...typography.mono, fontSize: 26, fontWeight: '700', marginTop: 4 },
  label: { ...typography.caption },
  sub: { ...typography.small },
});
