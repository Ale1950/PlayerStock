import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/src/hooks/useAuth';
import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, spacing, typography } from '@/src/theme/spacing';
import { BrandMark } from './BrandMark';
import { LanguageSelector } from './LanguageSelector';
import { ThemeToggle } from './ThemeToggle';

/** Chrome globale: wordmark + dot stato + lingua + tema + profilo/login. */
export function AppHeader() {
  const { colors } = useTheme();
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  return (
    <View style={[styles.bar, { backgroundColor: colors.surface, borderBottomColor: colors.border }]}>
      <Pressable style={styles.brand} onPress={() => router.push('/(tabs)/home')} testID="header-brand">
        <BrandMark size={24} />
        <Text style={[typography.wordmark, { color: colors.text }]}>PLAYERSTOCK</Text>
        <View style={styles.statusDot}>
          <View style={[styles.dot, { backgroundColor: colors.green }]} />
        </View>
      </Pressable>

      <View style={styles.actions}>
        <Pressable
          testID="header-help"
          onPress={() => router.push('/how-it-works')}
          hitSlop={8}
          style={({ pressed }) => [styles.iconBtn, { borderColor: colors.border, backgroundColor: colors.surfaceAlt }, pressed && { opacity: 0.7 }]}
        >
          <Ionicons name="help-circle-outline" size={20} color={colors.text} />
        </Pressable>
        <LanguageSelector />
        <ThemeToggle />
        {isAuthenticated ? (
          <Pressable
            testID="header-profile"
            onPress={() => router.push('/(tabs)/profile')}
            hitSlop={8}
            style={({ pressed }) => [styles.iconBtn, { borderColor: colors.border, backgroundColor: colors.surfaceAlt }, pressed && { opacity: 0.7 }]}
          >
            <Ionicons name="person-outline" size={20} color={colors.text} />
          </Pressable>
        ) : (
          <Pressable
            testID="header-login"
            onPress={() => router.push('/(auth)/welcome')}
            style={({ pressed }) => [styles.loginBtn, { backgroundColor: colors.cyan }, pressed && { opacity: 0.85 }]}
          >
            <Text style={[typography.monoLabel, { color: colors.onAccent }]}>LOGIN</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.md, height: 52, borderBottomWidth: 1,
  },
  brand: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  statusDot: { marginLeft: 2, justifyContent: 'center' },
  dot: { width: 7, height: 7, borderRadius: 4 },
  actions: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  iconBtn: { width: 36, height: 36, borderRadius: 10, borderWidth: borderW, justifyContent: 'center', alignItems: 'center' },
  loginBtn: { height: 36, paddingHorizontal: 14, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
});
