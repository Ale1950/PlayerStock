import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors } from '@/src/theme/colors';

export default function TabsLayout() {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.bgElevated,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          paddingTop: 6,
          paddingBottom: Math.max(insets.bottom, 8),
          height: 60 + insets.bottom,
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
      }}
    >
      <Tabs.Screen name="home" options={{
        title: t('tabs.home'),
        tabBarIcon: ({ color, size }) => <Ionicons name="stats-chart" size={size} color={color} />,
      }} />
      <Tabs.Screen name="portfolio" options={{
        title: t('tabs.portfolio'),
        tabBarIcon: ({ color, size }) => <Ionicons name="briefcase" size={size} color={color} />,
      }} />
      <Tabs.Screen name="leaderboard" options={{
        title: t('tabs.leaderboard'),
        tabBarIcon: ({ color, size }) => <Ionicons name="trophy" size={size} color={color} />,
      }} />
      <Tabs.Screen name="wallet" options={{
        title: t('tabs.wallet'),
        tabBarIcon: ({ color, size }) => <Ionicons name="wallet" size={size} color={color} />,
      }} />
      <Tabs.Screen name="reward" options={{
        title: t('tabs.reward'),
        tabBarIcon: ({ color, size }) => <Ionicons name="gift" size={size} color={color} />,
      }} />
      <Tabs.Screen name="profile" options={{
        title: t('tabs.profile'),
        tabBarIcon: ({ color, size }) => <Ionicons name="person-circle" size={size} color={color} />,
      }} />
    </Tabs>
  );
}
