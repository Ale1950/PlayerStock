import * as AuthSession from 'expo-auth-session';
import { useRouter } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { exchangeGoogleCode } from '@/src/services/auth.service';
import { translateError } from '@/src/services/api';
import { useAuth } from '@/src/hooks/useAuth';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';

WebBrowser.maybeCompleteAuthSession();

const GOOGLE_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_OAUTH_CLIENT_ID ?? '';

const discovery = {
  authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
};

export default function Login() {
  const { t } = useTranslation();
  const router = useRouter();
  const { refresh } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const redirectUri = AuthSession.makeRedirectUri({ scheme: 'frontend' });
  if (__DEV__) console.log('[PlayerStock] OAuth redirectUri =', redirectUri);

  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: GOOGLE_CLIENT_ID,
      scopes: ['openid', 'email', 'profile'],
      redirectUri,
      responseType: 'code',
      usePKCE: true,
    },
    discovery,
  );

  useEffect(() => {
    (async () => {
      if (response?.type === 'success') {
        const code = response.params.code;
        const verifier = request?.codeVerifier;
        if (!code || !verifier) {
          setError(t('login.error_generic'));
          return;
        }
        try {
          setBusy(true);
          await exchangeGoogleCode(code, verifier, redirectUri, 'it');
          await refresh();  // aggiorna lo stato auth condiviso → il guard porta a home/consent
          router.replace('/(tabs)/home');
        } catch (e) {
          setError(translateError(e));
        } finally {
          setBusy(false);
        }
      } else if (response?.type === 'error') {
        setError(t('login.error_generic'));
      }
    })();
  }, [response]);

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.container}>
        <Text style={styles.title}>{t('login.title')}</Text>

        {GOOGLE_CLIENT_ID ? (
          <Pressable
            testID="login-google-button"
            disabled={!request || busy}
            style={({ pressed }) => [styles.button, (!request || busy) && { opacity: 0.5 }, pressed && { opacity: 0.85 }]}
            onPress={() => promptAsync()}
          >
            {busy ? (
              <ActivityIndicator color={colors.onAccent} />
            ) : (
              <Text style={styles.buttonText}>{t('login.googleButton')}</Text>
            )}
          </Pressable>
        ) : (
          <View style={styles.configError} testID="login-config-error">
            <Text style={styles.configErrorTitle}>Configurazione mancante</Text>
            <Text style={styles.configErrorText}>
              Variabile EXPO_PUBLIC_GOOGLE_OAUTH_CLIENT_ID non impostata nel .env del frontend.
            </Text>
          </View>
        )}

        {!!error && (
          <View style={styles.errorBox} testID="login-error">
            <Text style={styles.errorTitle}>{t('login.errorTitle')}</Text>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {__DEV__ && (
          <View style={styles.devBox} testID="login-redirect-uri">
            <Text style={styles.devLabel}>DEV · Redirect URI da registrare in Google Cloud:</Text>
            <Text selectable style={styles.devValue}>{redirectUri}</Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1, padding: spacing.lg, justifyContent: 'center' },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.xl, textAlign: 'center' },
  button: {
    backgroundColor: colors.accent, paddingVertical: 16, borderRadius: radius.md,
    alignItems: 'center', minHeight: 52, justifyContent: 'center',
  },
  buttonText: { ...typography.h3, color: colors.onAccent, fontWeight: '600' },
  configError: { padding: spacing.md, backgroundColor: colors.bannerBg, borderRadius: radius.md, borderWidth: 1, borderColor: colors.bannerBorder },
  configErrorTitle: { ...typography.bodyBold, color: colors.warning, marginBottom: spacing.xs },
  configErrorText: { ...typography.small, color: colors.bannerText },
  errorBox: { marginTop: spacing.lg, padding: spacing.md, backgroundColor: colors.surfaceAlt, borderRadius: radius.md, borderWidth: 1, borderColor: colors.danger },
  errorTitle: { ...typography.bodyBold, color: colors.danger, marginBottom: spacing.xs },
  errorText: { ...typography.small, color: colors.danger },
  devBox: { marginTop: spacing.xl, padding: spacing.md, backgroundColor: colors.bgElevated, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border },
  devLabel: { ...typography.small, color: colors.textMuted, marginBottom: spacing.xs },
  devValue: { ...typography.small, color: colors.accent, fontFamily: 'monospace' },
});
