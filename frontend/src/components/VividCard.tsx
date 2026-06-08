import { LinearGradient } from 'expo-linear-gradient';
import { type ReactNode } from 'react';
import { StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { borderWindowW, radius, spacing, typography } from '@/src/theme/spacing';
import { gradients } from '@/src/theme/tokens';

/**
 * Card VIVIDA (schermate reward/engage). Riempimento a gradiente oro/bronzo +
 * bordo FINESTRA lime 2px + pill di stato opzionale. Luxury PIATTO: glow tenue.
 *
 * NACKL: passare `pill="PLACEHOLDER"` per etichettare il reward come
 * segnaposto interno (NON on-chain), coerente con Fase 5.
 */
export function VividCard({
  children, variant = 'cyan', pill, pillTone, style,
}: {
  children: ReactNode;
  variant?: 'cyan' | 'teal' | 'purple' | 'green' | 'amber' | 'pink';
  pill?: string;
  pillTone?: string;
  style?: ViewStyle;
}) {
  const { colors } = useTheme();
  const grad = variant === 'cyan' ? gradients.cyanTeal : gradients[variant];
  const glow = { shadowColor: '#000', shadowOpacity: 0.25, shadowRadius: 12, shadowOffset: { width: 0, height: 4 }, elevation: 6 };

  return (
    <View style={[styles.wrap, glow, style]}>
      <LinearGradient
        colors={grad}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.card, { borderColor: colors.borderWindow }]}
      >
        {!!pill && (
          <View style={[styles.pill, { backgroundColor: 'rgba(5,7,10,0.28)', borderColor: 'rgba(255,255,255,0.35)' }]}>
            <Text style={[typography.monoLabel, { color: pillTone ?? '#FFFFFF' }]}>{pill}</Text>
          </View>
        )}
        <View style={styles.body}>{children}</View>
      </LinearGradient>
    </View>
  );
}

/** Riga di testo su card vivida (inchiostro scuro per contrasto sul gradiente). */
export function VividText({ children, size = 'body' }: { children: ReactNode; size?: 'title' | 'body' | 'small' }) {
  const style = size === 'title' ? styles.vTitle : size === 'small' ? styles.vSmall : styles.vBody;
  return <Text style={style}>{children}</Text>;
}

const INK = '#1d1a16';
const styles = StyleSheet.create({
  wrap: { borderRadius: radius.window },
  card: { borderRadius: radius.window, borderWidth: borderWindowW, padding: spacing.lg, overflow: 'hidden' },
  pill: {
    alignSelf: 'flex-start', borderRadius: radius.pill, borderWidth: borderWindowW,
    paddingHorizontal: 10, paddingVertical: 4, marginBottom: spacing.sm,
  },
  body: { gap: 6 },
  vTitle: { ...typography.h2, color: INK },
  vBody: { ...typography.bodyBold, color: INK },
  vSmall: { ...typography.small, color: INK, opacity: 0.8 },
});
