import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { HOW_IT_WORKS_INTRO, HOW_IT_WORKS_SECTIONS } from '@/src/content/howItWorks';
import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { type ThemeColors } from '@/src/theme/tokens';

/**
 * Guida in-app "Come funziona" — SOLO UI (nessuna logica/motore/economia).
 * Testo centralizzato in `src/content/howItWorks.ts`. Raggiungibile da header "?" e da Profilo.
 */
export default function HowItWorks() {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const router = useRouter();
  const tones = [colors.cyan, colors.teal, colors.purple, colors.green, colors.amber, colors.chartBlue];

  // un paio di sezioni aperte di default
  const [open, setOpen] = useState<Record<string, boolean>>({
    [HOW_IT_WORKS_SECTIONS[0].key]: true,
    [HOW_IT_WORKS_SECTIONS[2].key]: true,
  });
  const toggle = (k: string) => setOpen((o) => ({ ...o, [k]: !o[k] }));

  return (
    <View style={styles.safe} testID="how-it-works-screen">
      <GeometricBackground />

      <View style={styles.topbar}>
        <Text style={styles.title} testID="guide-title">{t('guide.title')}</Text>
        <Pressable testID="guide-close" onPress={() => router.back()} hitSlop={10}
          style={({ pressed }) => [styles.closeBtn, pressed && { opacity: 0.7 }]}>
          <Ionicons name="close" size={22} color={colors.text} />
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        {/* intro */}
        <View style={styles.intro} testID="guide-intro">
          <Text style={styles.introTitle}>{HOW_IT_WORKS_INTRO.title}</Text>
          <Text style={styles.introBody}>{HOW_IT_WORKS_INTRO.body}</Text>
        </View>

        {HOW_IT_WORKS_SECTIONS.map((s, i) => {
          const tint = tones[i % tones.length];
          const isOpen = !!open[s.key];
          return (
            <View key={s.key} style={styles.section}>
              <Pressable testID={`guide-section-${s.key}`} onPress={() => toggle(s.key)}
                style={({ pressed }) => [styles.secHeader, pressed && { opacity: 0.8 }]}>
                <View style={[styles.iconChip, { backgroundColor: tint + '22' }]}>
                  <Ionicons name={s.icon} size={18} color={tint} />
                </View>
                <Text style={styles.secTitle}>{s.title}</Text>
                <Ionicons name={isOpen ? 'chevron-up' : 'chevron-down'} size={18} color={colors.muted} />
              </Pressable>

              {isOpen && (
                <View style={styles.secBody} testID={`guide-body-${s.key}`}>
                  <Text style={styles.bodyText}>{s.body}</Text>
                  {!!s.example && (
                    <Text style={styles.example}>
                      <Text style={styles.exampleLabel}>{t('guide.example_label')} </Text>
                      {s.example}
                    </Text>
                  )}
                </View>
              )}
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  topbar: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingTop: spacing.lg, paddingBottom: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  title: { ...typography.pageTitle, color: colors.text },
  closeBtn: {
    width: 38, height: 38, borderRadius: 10, borderWidth: borderW, borderColor: colors.border,
    backgroundColor: colors.surfaceAlt, justifyContent: 'center', alignItems: 'center',
  },
  container: {
    padding: spacing.lg, paddingBottom: spacing.xxl + 40,
    maxWidth: 760, width: '100%', alignSelf: 'center',
  },
  intro: {
    padding: spacing.lg, backgroundColor: colors.surface, borderRadius: radius.card,
    borderWidth: borderW, borderColor: colors.cyan, marginBottom: spacing.lg,
  },
  introTitle: { ...typography.h3, color: colors.text, marginBottom: spacing.xs },
  introBody: { ...typography.body, color: colors.muted },
  section: {
    backgroundColor: colors.surface, borderRadius: radius.card,
    borderWidth: borderW, borderColor: colors.border, marginBottom: spacing.md, overflow: 'hidden',
  },
  secHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md },
  iconChip: { width: 34, height: 34, borderRadius: 9, justifyContent: 'center', alignItems: 'center' },
  secTitle: { ...typography.bodyBold, color: colors.text, flex: 1 },
  secBody: {
    paddingHorizontal: spacing.md, paddingBottom: spacing.md, paddingTop: spacing.xs,
    gap: spacing.sm,
  },
  bodyText: { ...typography.body, color: colors.text },
  example: { ...typography.small, color: colors.muted },
  exampleLabel: { ...typography.small, color: colors.amber, fontWeight: '700' },
});
