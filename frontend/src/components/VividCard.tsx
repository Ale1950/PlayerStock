import { LinearGradient } from 'expo-linear-gradient';
import { type ReactNode } from 'react';
import { StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { gradients } from '@/src/theme/tokens';

/**
 * Card VIVIDA (schermate reward/engage). Riempimento a gradiente + bordo
 * luminescente (glow SOLO su dark) + pill di stato opzionale.
 * Su CHIARO: niente glow (neon non rende su bianco), gradiente pieno.
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
  const { colors, isDark } = useTheme();
  const grad = variant === 'cyan' ? gradients.cyanTeal : gradients[variant];
  const glowColor = grad[0];
  const glow = isDark
    ? { shadowColor: glowColor, shadowOpacity: 0.55, shadowRadius: 20, shadowOffset: { width: 0, height: 0 }, elevation: 14 }
    : null;

  return (
    <View style={[styles.wrap, glow, style]}>
      <LinearGradient
        colors={grad}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.card, { borderColor: isDark ? glowColor : 'transparent' }]}
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

const INK = '#05070A';
const styles = StyleSheet.create({
  wrap: { borderRadius: radius.card },
  card: { borderRadius: radius.card, borderWidth: borderW, padding: spacing.lg, overflow: 'hidden' },
  pill: {
    alignSelf: 'flex-start', borderRadius: radius.pill, borderWidth: borderW,
    paddingHorizontal: 10, paddingVertical: 4, marginBottom: spacing.sm,
  },
  body: { gap: 6 },
  vTitle: { ...typography.h2, color: INK },
  vBody: { ...typography.bodyBold, color: INK },
  vSmall: { ...typography.small, color: INK, opacity: 0.8 },
});
