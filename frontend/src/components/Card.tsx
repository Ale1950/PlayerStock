import { type ReactNode } from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, radius, spacing } from '@/src/theme/spacing';

/**
 * Card base (DESIGN_SPEC): radius 18, surface, border 1px.
 * `accent` opzionale = barra sinistra 4px colorata (ruolo/tier/severità).
 */
export function Card({
  children, accent, style,
}: { children: ReactNode; accent?: string; style?: ViewStyle }) {
  const { colors } = useTheme();
  return (
    <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }, style]}>
      {accent ? <View style={[styles.accentBar, { backgroundColor: accent }]} /> : null}
      <View style={[styles.body, accent ? { paddingLeft: spacing.md + 4 } : null]}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.card, borderWidth: borderW, overflow: 'hidden' },
  accentBar: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4 },
  body: { padding: spacing.md },
});
