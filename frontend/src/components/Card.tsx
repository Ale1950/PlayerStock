import { type ReactNode } from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, borderWindowW, radius, spacing } from '@/src/theme/spacing';

/**
 * Card base (DESIGN_SYSTEM). `window` = card "finestra" top-level: bordo LIME 2px,
 * radius 16. Default (sotto-elemento) = bordo subtle. `accent` opzionale = barra
 * sinistra 4px colorata (ruolo/tier/severità).
 */
export function Card({
  children, accent, window, style,
}: { children: ReactNode; accent?: string; window?: boolean; style?: ViewStyle }) {
  const { colors } = useTheme();
  const frame = window
    ? { borderColor: colors.borderWindow, borderWidth: borderWindowW, borderRadius: radius.window }
    : { borderColor: colors.border, borderWidth: borderW, borderRadius: radius.card };
  return (
    <View style={[styles.card, { backgroundColor: colors.surface }, frame, style]}>
      {accent ? <View style={[styles.accentBar, { backgroundColor: accent }]} /> : null}
      <View style={[styles.body, accent ? { paddingLeft: spacing.md + 4 } : null]}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { overflow: 'hidden' },
  accentBar: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4 },
  body: { padding: spacing.md },
});
