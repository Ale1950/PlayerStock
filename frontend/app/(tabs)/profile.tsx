import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { LanguageSelector } from '@/src/components/chrome/LanguageSelector';
import { ThemeToggle } from '@/src/components/chrome/ThemeToggle';
import { StateView } from '@/src/components/StateView';
import { useAuth } from '@/src/hooks/useAuth';
import { deleteAccount } from '@/src/services/auth.service';
import { getMyStats, type MyStats } from '@/src/services/stats.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { type ThemeColors } from '@/src/theme/tokens';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { formatCredits } from '@/src/utils/formatters';

const eur = (v: number | null | undefined) => (v == null ? '—' : `${v >= 0 ? '+' : ''}€${formatCredits(v)}`);

export default function Profile() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const { colors, isDark } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [stat, setStat] = useState<MyStats | null>(null);
  const [statLoading, setStatLoading] = useState(true);
  const [statErr, setStatErr] = useState<string | null>(null);

  useFocusEffect(useCallback(() => {
    let active = true;
    setStatLoading(true); setStatErr(null);
    getMyStats()
      .then((d) => { if (active) setStat(d); })
      .catch(() => { if (active) setStatErr('—'); })
      .finally(() => { if (active) setStatLoading(false); });
    return () => { active = false; };
  }, []));

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
    <View style={styles.safe}>
      <GeometricBackground />
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

        {/* Riepilogo statistiche personali */}
        <View style={styles.statsCard} testID="profile-stats">
          <View style={styles.statsHead}>
            <Text style={styles.statsTitle}>{t('profile.stats_title')}</Text>
            <Pressable testID="profile-leaderboard-link" onPress={() => router.push('/(tabs)/leaderboard')}
              style={({ pressed }) => [styles.statLink, pressed && { opacity: 0.7 }]}>
              <Text style={styles.statLinkText}>{t('profile.view_leaderboard')}</Text>
              <Text style={styles.statLinkChevron}>›</Text>
            </Pressable>
          </View>
          {statLoading || statErr || !stat ? (
            <StateView loading={statLoading} error={statErr}
              empty={!statLoading && !statErr && !stat} emptyLabel={t('profile.stats_empty')} icon="stats-chart-outline" />
          ) : (
            <View style={styles.statRow}>
              <View style={styles.statItem}>
                <Text style={[styles.statVal, { color: colors.amber }]} numberOfLines={1}>€{formatCredits(stat.equity)}</Text>
                <Text style={styles.statKey}>{t('profile.stat_equity')}</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={[styles.statVal, { color: stat.unrealized_pnl >= 0 ? colors.green : colors.red }]} numberOfLines={1}>{eur(stat.unrealized_pnl)}</Text>
                <Text style={styles.statKey}>{t('profile.stat_unrealized')}</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={[styles.statVal, { color: stat.realized_pnl >= 0 ? colors.green : colors.red }]} numberOfLines={1}>{eur(stat.realized_pnl)}</Text>
                <Text style={styles.statKey}>{t('profile.stat_realized')}</Text>
              </View>
            </View>
          )}
        </View>

        {/* Impostazioni */}
        <Text style={styles.groupLabel}>{t('profile.settings')}</Text>
        <View style={styles.row}>
          <Text style={styles.rowLabel}>{t('profile.language')}</Text>
          <LanguageSelector />
        </View>
        <Text style={styles.settingHint}>{t('profile.lang_active')}</Text>

        <View style={styles.row}>
          <Text style={styles.rowLabel}>{isDark ? t('profile.theme_dark') : t('profile.theme_light')}</Text>
          <ThemeToggle />
        </View>

        <Pressable testID="profile-how-it-works" onPress={() => router.push('/how-it-works')} style={({ pressed }) => [styles.linkRow, pressed && { opacity: 0.85 }]}>
          <Text style={styles.linkRowText}>{t('guide.open')}</Text>
          <Text style={styles.linkRowChevron}>›</Text>
        </Pressable>

        <Pressable testID="profile-logout" onPress={onLogout} style={({ pressed }) => [styles.button, pressed && { opacity: 0.85 }]}>
          <Text style={styles.buttonText}>{t('profile.logout')}</Text>
        </Pressable>

        <Pressable testID="profile-delete" disabled={busy} onPress={onDelete} style={({ pressed }) => [styles.buttonDanger, pressed && { opacity: 0.85 }]}>
          <Text style={styles.buttonDangerText}>{t('profile.delete_account')}</Text>
        </Pressable>

        <Text style={styles.version}>PlayerStock v0.1.0 — Fase Design</Text>
      </ScrollView>
    </View>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 60 },
  title: { ...typography.pageTitle, color: colors.text, marginBottom: spacing.lg },
  card: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    padding: spacing.lg, backgroundColor: colors.surface,
    borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border,
  },
  avatar: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.cyan, justifyContent: 'center', alignItems: 'center' },
  avatarText: { color: colors.onAccent, fontWeight: '700', fontSize: 22, fontFamily: typography.bodyBold.fontFamily },
  name: { ...typography.h3, color: colors.text },
  email: { ...typography.small, color: colors.muted, marginTop: 2 },
  adminBadge: { ...typography.caption, color: colors.gold, marginTop: 4 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border,
    marginTop: spacing.lg },
  rowLabel: { ...typography.body, color: colors.muted },
  button: {
    marginTop: spacing.xl, backgroundColor: colors.surface,
    paddingVertical: 14, borderRadius: radius.md, alignItems: 'center',
    borderWidth: borderW, borderColor: colors.border,
  },
  buttonText: { ...typography.bodyBold, color: colors.text },
  linkRow: {
    marginTop: spacing.xl, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: colors.surface, paddingVertical: 14, paddingHorizontal: spacing.lg,
    borderRadius: radius.md, borderWidth: borderW, borderColor: colors.border,
  },
  linkRowText: { ...typography.bodyBold, color: colors.text },
  linkRowChevron: { ...typography.h3, color: colors.muted },
  statsCard: {
    marginTop: spacing.lg, padding: spacing.lg, backgroundColor: colors.surface,
    borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border,
  },
  statsHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md },
  statsTitle: { ...typography.h3, color: colors.text },
  statLink: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  statLinkText: { ...typography.monoLabel, color: colors.cyan },
  statLinkChevron: { ...typography.h3, color: colors.cyan },
  statRow: { flexDirection: 'row', justifyContent: 'space-between' },
  statItem: { alignItems: 'center', flex: 1 },
  statVal: { ...typography.h2, fontVariant: ['tabular-nums'] },
  statKey: { ...typography.small, color: colors.muted, marginTop: 2, textAlign: 'center' },
  groupLabel: { ...typography.caption, color: colors.muted, marginTop: spacing.xl },
  settingHint: { ...typography.small, color: colors.muted, marginTop: spacing.xs },
  buttonDanger: {
    marginTop: spacing.md, backgroundColor: 'transparent',
    paddingVertical: 14, borderRadius: radius.md, alignItems: 'center',
    borderWidth: borderW, borderColor: colors.red,
  },
  buttonDangerText: { ...typography.bodyBold, color: colors.red },
  version: { ...typography.caption, color: colors.muted, textAlign: 'center', marginTop: spacing.xl },
});
