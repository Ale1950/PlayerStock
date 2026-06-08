import { Stack, useRouter, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { useIconFonts } from '@/src/hooks/use-icon-fonts';
import { AuthProvider, useAuth } from '@/src/hooks/useAuth';
import { ThemeProvider, useTheme } from '@/src/theme/ThemeProvider';
import '@/src/i18n';

SplashScreen.preventAutoHideAsync();

function RootNavigator() {
  const { isLoading, isAuthenticated, user } = useAuth();
  const { colors } = useTheme();
  const segments = useSegments();
  const router = useRouter();
  const [fontsLoaded, fontsError] = useIconFonts();

  useEffect(() => {
    if (fontsLoaded || fontsError) SplashScreen.hideAsync();
  }, [fontsLoaded, fontsError]);

  useEffect(() => {
    if (isLoading) return;
    const inAuthGroup = segments[0] === '(auth)';
    const inGuide = segments[0] === 'how-it-works';  // guida raggiungibile anche senza login
    const inTabs = segments[0] === '(tabs)' || segments[0] === 'player';
    const needsConsent = isAuthenticated && user && (!user.terms_accepted_at || !user.privacy_accepted_at);
    if (!isAuthenticated && !inAuthGroup && !inGuide) {
      router.replace('/(auth)/welcome');
    } else if (isAuthenticated && needsConsent && segments[1] !== 'consent') {
      router.replace('/(auth)/consent');
    } else if (isAuthenticated && !needsConsent && (inAuthGroup || segments[0] === undefined)) {
      router.replace('/(tabs)/home');
    }
  }, [isLoading, isAuthenticated, user, segments, router]);

  if (!fontsLoaded && !fontsError) return null;
  return (
    <>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.bg } }} />
    </>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AuthProvider>
          <RootNavigator />
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
