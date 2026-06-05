import { useRouter } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';

export default function Welcome() {
  const { t } = useTranslation();
  const router = useRouter();
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.brandBlock}>
          <View style={styles.logo} testID="welcome-logo">
            <Text style={styles.logoLetter}>P</Text>
          </View>
          <Text style={styles.brand}>{t('app.name')}</Text>
          <Text style={styles.tagline}>{t('app.tagline')}</Text>
        </View>

        <View style={styles.hero}>
          <Text style={styles.heroTitle}>{t('welcome.title')}</Text>
          <Text style={styles.heroSubtitle}>{t('welcome.subtitle')}</Text>
        </View>

        <View style={styles.bullets}>
          {[t('welcome.bullet1'), t('welcome.bullet2'), t('welcome.bullet3')].map((b, i) => (
            <View key={i} style={styles.bulletRow}>
              <View style={styles.bulletDot} />
              <Text style={styles.bulletText}>{b}</Text>
            </View>
          ))}
        </View>

        <View style={styles.cta}>
          <Pressable
            testID="welcome-cta-google"
            style={({ pressed }) => [styles.button, pressed && { opacity: 0.85 }]}
            onPress={() => router.push('/(auth)/login')}
          >
            <Text style={styles.buttonText}>{t('welcome.cta')}</Text>
          </Pressable>
          <Text style={styles.terms}>{t('welcome.terms')}</Text>
        </View>

        <View style={styles.disclaimer} testID="welcome-disclaimer">
          <Text style={styles.disclaimerText}>{t('disclaimer.long')}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl },
  brandBlock: { alignItems: 'center', marginTop: spacing.xl },
  logo: {
    width: 64, height: 64, borderRadius: radius.lg,
    backgroundColor: colors.accent, justifyContent: 'center', alignItems: 'center',
    marginBottom: spacing.md,
  },
  logoLetter: { ...typography.h1, color: colors.bg, fontSize: 36 },
  brand: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.xs },
  tagline: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  hero: { marginTop: spacing.xl, marginBottom: spacing.lg },
  heroTitle: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.sm },
  heroSubtitle: { ...typography.body, color: colors.textSecondary, lineHeight: 22 },
  bullets: { marginVertical: spacing.lg },
  bulletRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md },
  bulletDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.up, marginRight: spacing.md },
  bulletText: { ...typography.body, color: colors.textPrimary, flex: 1 },
  cta: { marginTop: spacing.lg },
  button: {
    backgroundColor: colors.accent, paddingVertical: 16, borderRadius: radius.md,
    alignItems: 'center', justifyContent: 'center', minHeight: 52,
  },
  buttonText: { ...typography.h3, color: '#FFFFFF', fontWeight: '600' },
  terms: { ...typography.small, color: colors.textMuted, textAlign: 'center', marginTop: spacing.md },
  disclaimer: {
    marginTop: spacing.xl, padding: spacing.md, borderRadius: radius.md,
    backgroundColor: colors.bannerBg, borderWidth: 1, borderColor: colors.bannerBorder,
  },
  disclaimerText: { ...typography.small, color: colors.bannerText, lineHeight: 16 },
});
