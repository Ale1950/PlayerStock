import { Stack, useRouter, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { useIconFonts } from '@/src/hooks/use-icon-fonts';
import { useAuth } from '@/src/hooks/useAuth';
import '@/src/i18n';

SplashScreen.preventAutoHideAsync();

function RootNavigator() {
  const { isLoading, isAuthenticated, user } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const [fontsLoaded, fontsError] = useIconFonts();

  useEffect(() => {
    if (fontsLoaded || fontsError) SplashScreen.hideAsync();
  }, [fontsLoaded, fontsError]);

  useEffect(() => {
    if (isLoading) return;
    const inAuthGroup = segments[0] === '(auth)';
    const inTabs = segments[0] === '(tabs)' || segments[0] === 'player';
    const needsConsent = isAuthenticated && user && (!user.terms_accepted_at || !user.privacy_accepted_at);
    if (!isAuthenticated && !inAuthGroup) {
      router.replace('/(auth)/welcome');
    } else if (isAuthenticated && needsConsent && segments[1] !== 'consent') {
      router.replace('/(auth)/consent');
    } else if (isAuthenticated && !needsConsent && (inAuthGroup || segments[0] === undefined)) {
      router.replace('/(tabs)/home');
    }
  }, [isLoading, isAuthenticated, user, segments, router]);

  if (!fontsLoaded && !fontsError) return null;
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#0B0F19' } }} />;
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <RootNavigator />
    </SafeAreaProvider>
  );
}
