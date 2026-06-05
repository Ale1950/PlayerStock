import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors } from '@/src/theme/colors';
import { spacing, typography } from '@/src/theme/spacing';

export default function Portfolio() {
  const { t } = useTranslation();
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}><Text style={styles.title}>{t('portfolio.title')}</Text></View>
      <View style={styles.empty} testID="portfolio-empty">
        <Ionicons name="briefcase-outline" size={64} color={colors.textMuted} />
        <Text style={styles.emptyTitle}>{t('portfolio.empty_title')}</Text>
        <Text style={styles.emptySub}>{t('portfolio.empty_subtitle')}</Text>
        <Text style={styles.phase}>{t('portfolio.phase4_note')}</Text>
      </View>
    </SafeAreaView>
  );
}
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, paddingBottom: spacing.sm },
  title: { ...typography.h1, color: colors.textPrimary },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: spacing.lg, gap: spacing.md },
  emptyTitle: { ...typography.h2, color: colors.textPrimary, marginTop: spacing.md },
  emptySub: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  phase: { ...typography.caption, color: colors.accent, marginTop: spacing.lg },
});
