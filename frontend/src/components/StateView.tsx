import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { spacing, typography } from '@/src/theme/spacing';

/** Stato loading / vuoto / errore coerente coi token (Atlas può sfarfallare). */
export function StateView({
  loading, error, empty, emptyLabel, icon = 'cube-outline',
}: {
  loading?: boolean; error?: string | null; empty?: boolean; emptyLabel?: string; icon?: keyof typeof Ionicons.glyphMap;
}) {
  const { colors } = useTheme();
  if (loading) {
    return <View style={styles.box}><ActivityIndicator color={colors.cyan} size="large" /></View>;
  }
  if (error) {
    return (
      <View style={styles.box}>
        <Ionicons name="cloud-offline-outline" size={40} color={colors.red} />
        <Text style={[typography.small, { color: colors.red, textAlign: 'center', marginTop: spacing.sm }]}>{error}</Text>
      </View>
    );
  }
  if (empty) {
    return (
      <View style={styles.box}>
        <Ionicons name={icon} size={40} color={colors.muted} />
        <Text style={[typography.body, { color: colors.muted, marginTop: spacing.sm }]}>{emptyLabel ?? '—'}</Text>
      </View>
    );
  }
  return null;
}

const styles = StyleSheet.create({
  box: { paddingVertical: spacing.xxl, alignItems: 'center', justifyContent: 'center', gap: 4 },
});
