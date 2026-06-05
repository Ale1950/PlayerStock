import { useRouter } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useAuth } from '@/src/hooks/useAuth';
import api, { translateError } from '@/src/services/api';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';

export default function Consent() {
  const { t } = useTranslation();
  const router = useRouter();
  const { refresh } = useAuth();
  const [terms, setTerms] = useState(false);
  const [privacy, setPrivacy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const enabled = terms && privacy;

  const onSubmit = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.post('/users/me/accept-terms', { terms, privacy });
      await refresh();
      router.replace('/(tabs)/home');
    } catch (e) {
      setError(translateError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('consent.title')}</Text>
        <Text style={styles.subtitle}>{t('consent.subtitle')}</Text>

        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerText}>{t('disclaimer.long')}</Text>
        </View>

        <View style={styles.row} testID="consent-terms-row">
          <Switch value={terms} onValueChange={setTerms} testID="consent-terms-switch" />
          <Text style={styles.rowText}>{t('consent.termsLabel')}</Text>
        </View>
        <View style={styles.row} testID="consent-privacy-row">
          <Switch value={privacy} onValueChange={setPrivacy} testID="consent-privacy-switch" />
          <Text style={styles.rowText}>{t('consent.privacyLabel')}</Text>
        </View>

        {error && <Text style={styles.error}>{error}</Text>}

        <Pressable
          testID="consent-submit"
          disabled={!enabled || busy}
          onPress={onSubmit}
          style={({ pressed }) => [styles.button, (!enabled || busy) && { opacity: 0.5 }, pressed && { opacity: 0.85 }]}
        >
          <Text style={styles.buttonText}>{t('consent.cta')}</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg },
  title: { ...typography.h1, color: colors.textPrimary, marginTop: spacing.lg },
  subtitle: { ...typography.body, color: colors.textSecondary, marginVertical: spacing.md },
  disclaimer: {
    padding: spacing.md, marginVertical: spacing.lg,
    backgroundColor: colors.bannerBg, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.bannerBorder,
  },
  disclaimerText: { ...typography.small, color: colors.bannerText, lineHeight: 18 },
  row: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md, gap: spacing.md },
  rowText: { ...typography.body, color: colors.textPrimary, flex: 1 },
  button: {
    backgroundColor: colors.accent, paddingVertical: 16, borderRadius: radius.md,
    alignItems: 'center', marginTop: spacing.xl, minHeight: 52, justifyContent: 'center',
  },
  buttonText: { ...typography.h3, color: '#FFFFFF', fontWeight: '600' },
  error: { ...typography.small, color: colors.danger, marginTop: spacing.md, textAlign: 'center' },
});
