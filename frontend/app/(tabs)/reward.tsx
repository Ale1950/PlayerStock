import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';

export default function Reward() {
  const { t } = useTranslation();
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('reward.title')}</Text>
        <View style={styles.card} testID="reward-soon-card">
          <Ionicons name="gift-outline" size={56} color={colors.accent} />
          <Text style={styles.h2}>{t('reward.soon_title')}</Text>
          <Text style={styles.body}>{t('reward.soon_subtitle')}</Text>
        </View>
        <View style={styles.infoBox}>
          <Ionicons name="information-circle-outline" size={20} color={colors.accent} />
          <Text style={styles.infoText}>{t('reward.info_separated')}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.lg },
  card: {
    padding: spacing.xl, backgroundColor: colors.card,
    borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border,
    alignItems: 'center', gap: spacing.md,
  },
  h2: { ...typography.h2, color: colors.textPrimary, marginTop: spacing.sm },
  body: { ...typography.body, color: colors.textSecondary, textAlign: 'center', lineHeight: 22 },
  infoBox: {
    marginTop: spacing.lg, padding: spacing.md, borderRadius: radius.md,
    backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.border,
    flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start',
  },
  infoText: { ...typography.small, color: colors.textSecondary, flex: 1, lineHeight: 18 },
});
