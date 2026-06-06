import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { AppHeader } from '@/src/components/chrome/AppHeader';
import { StatusTicker } from '@/src/components/chrome/StatusTicker';
import { useTheme } from '@/src/theme/ThemeProvider';
import { fonts } from '@/src/theme/tokens';

type IconName = keyof typeof Ionicons.glyphMap;

const TAB_ICON: Record<string, IconName> = {
  home: 'stats-chart-outline',
  portfolio: 'briefcase-outline',
  leaderboard: 'trophy-outline',
  engage: 'flame-outline',
  wallet: 'wallet-outline',
  reward: 'gift-outline',
  profile: 'person-circle-outline',
};

export default function TabsLayout() {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  const screen = (name: string, label: string) => (
    <Tabs.Screen
      name={name}
      options={{
        title: label,
        tabBarIcon: ({ color, size }) => <Ionicons name={TAB_ICON[name]} size={size} color={color} />,
      }}
    />
  );

  // Rotte raggiungibili ma NON nella bottom-nav (accorpamento 7→5):
  //  - reward: dentro l'hub Wallet
  //  - profile: dall'icona in header
  const hidden = (name: string) => <Tabs.Screen name={name} options={{ href: null }} />;

  return (
    <View style={{ flex: 1, backgroundColor: colors.bg }}>
      <Tabs
        screenOptions={{
          header: () => (
            <SafeAreaView edges={['top']} style={{ backgroundColor: colors.surface }}>
              <AppHeader />
              <StatusTicker />
            </SafeAreaView>
          ),
          headerShown: true,
          tabBarActiveTintColor: colors.gold,
          tabBarInactiveTintColor: colors.muted,
          tabBarStyle: {
            backgroundColor: colors.surface,
            borderTopColor: colors.border,
            borderTopWidth: 1,
            paddingTop: 6,
            paddingBottom: Math.max(insets.bottom, 8),
            height: 58 + insets.bottom,
          },
          tabBarLabelStyle: {
            fontFamily: fonts.mono,
            fontSize: 8.5,
            fontWeight: '600',
            letterSpacing: 0.8,
            textTransform: 'uppercase',
          },
        }}
      >
        {screen('home', t('tabs.home'))}
        {screen('portfolio', t('tabs.portfolio'))}
        {screen('leaderboard', t('tabs.leaderboard'))}
        {screen('engage', t('tabs.engage'))}
        {screen('wallet', t('tabs.wallet'))}
        {hidden('reward')}
        {hidden('profile')}
      </Tabs>
    </View>
  );
}
