import { useRouter } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useAuth } from '@/src/hooks/useAuth';
import { deleteAccount } from '@/src/services/auth.service';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';
import { formatDate } from '@/src/utils/formatters';

export default function Profile() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  const onLogout = () => {
    Alert.alert(t('profile.logout_confirm_title'), '', [
      { text: t('profile.logout_confirm_no'), style: 'cancel' },
      {
        text: t('profile.logout_confirm_yes'),
        style: 'destructive',
        onPress: async () => { await logout(); router.replace('/(auth)/welcome'); },
      },
    ]);
  };

  const onDelete = () => {
    Alert.alert(
      t('profile.delete_account_confirm_title'),
      t('profile.delete_account_confirm_msg'),
      [
        { text: t('profile.delete_account_confirm_no'), style: 'cancel' },
        {
          text: t('profile.delete_account_confirm_yes'),
          style: 'destructive',
          onPress: async () => {
            try {
              setBusy(true);
              await deleteAccount();
              await logout();
              router.replace('/(auth)/welcome');
            } finally { setBusy(false); }
          },
        },
      ],
    );
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('profile.title')}</Text>

        <View style={styles.card} testID="profile-card">
          <View style={styles.avatar}><Text style={styles.avatarText}>{(user?.name?.[0] ?? '?').toUpperCase()}</Text></View>
          <View style={{ flex: 1, minWidth: 0 }}>
            <Text style={styles.name} numberOfLines={1}>{user?.name ?? '—'}</Text>
            <Text style={styles.email} numberOfLines={1}>{user?.email ?? '—'}</Text>
            {user?.role === 'admin' && <Text style={styles.adminBadge}>ADMIN</Text>}
          </View>
        </View>

        <View style={styles.row}>
          <Text style={styles.rowLabel}>{t('profile.language')}</Text>
          <Text style={styles.rowValue}>🇮🇹 Italiano</Text>
        </View>

        <Pressable testID="profile-logout" onPress={onLogout} style={({ pressed }) => [styles.button, pressed && { opacity: 0.85 }]}>
          <Text style={styles.buttonText}>{t('profile.logout')}</Text>
        </Pressable>

        <Pressable testID="profile-delete" disabled={busy} onPress={onDelete} style={({ pressed }) => [styles.buttonDanger, pressed && { opacity: 0.85 }]}>
          <Text style={styles.buttonDangerText}>{t('profile.delete_account')}</Text>
        </Pressable>

        <Text style={styles.version}>PlayerStock v0.1.0 — Fase 1 (Emergent)</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 60 },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.lg },
  card: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    padding: spacing.lg, backgroundColor: colors.card,
    borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border,
  },
  avatar: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.accent, justifyContent: 'center', alignItems: 'center' },
  avatarText: { color: '#FFF', fontWeight: '700', fontSize: 22 },
  name: { ...typography.h3, color: colors.textPrimary },
  email: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  adminBadge: { ...typography.caption, color: colors.warning, marginTop: 4 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border,
    marginTop: spacing.lg },
  rowLabel: { ...typography.body, color: colors.textSecondary },
  rowValue: { ...typography.body, color: colors.textPrimary },
  button: {
    marginTop: spacing.xl, backgroundColor: colors.card,
    paddingVertical: 14, borderRadius: radius.md, alignItems: 'center',
    borderWidth: 1, borderColor: colors.border,
  },
  buttonText: { ...typography.bodyBold, color: colors.textPrimary },
  buttonDanger: {
    marginTop: spacing.md, backgroundColor: 'transparent',
    paddingVertical: 14, borderRadius: radius.md, alignItems: 'center',
    borderWidth: 1, borderColor: colors.danger,
  },
  buttonDangerText: { ...typography.bodyBold, color: colors.danger },
  version: { ...typography.caption, color: colors.textMuted, textAlign: 'center', marginTop: spacing.xl },
});
