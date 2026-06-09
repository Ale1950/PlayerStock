import { type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { borderWindowW, radius, spacing, typography } from '@/src/theme/spacing';

/**
 * Pannello "finestra" del bento (DESIGN_SYSTEM): surface + bordo LIME 2px + radius 16.
 * Header opzionale = titolo (muted, mono) + azione (oro). I SOTTO-elementi interni
 * usano `colors.border` (subtle), MAI il lime.
 */
export function BentoCard({
  title, action, onAction, children, style, testID,
}: {
  title?: string;
  action?: string;
  onAction?: () => void;
  children: ReactNode;
  style?: ViewStyle;
  testID?: string;
}) {
  const { colors } = useTheme();
  return (
    <View testID={testID} style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.borderWindow }, style]}>
      {(title || action) && (
        <View style={styles.head}>
          {!!title && <Text style={[typography.monoLabel, { color: colors.muted }]}>{title}</Text>}
          {!!action && (
            <Pressable onPress={onAction} hitSlop={8}>
              <Text style={[typography.monoLabel, { color: colors.accent }]}>{action} ›</Text>
            </Pressable>
          )}
        </View>
      )}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.window, borderWidth: borderWindowW, padding: spacing.md, gap: spacing.sm, overflow: 'hidden' },
  head: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
});
