import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { translateError } from '@/src/services/api';
import { getLeaderboard, type LeaderboardItem, type LeaderboardResponse } from '@/src/services/portfolio.service';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';
import { formatCredits } from '@/src/utils/formatters';

export default function Leaderboard() {
  const { t } = useTranslation();
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const lb = await getLeaderboard(50);
      setData(lb);
    } catch (e) { setError(translateError(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useFocusEffect(useCallback(() => { setLoading(true); load(); }, [load]));

  const renderRow = useCallback(({ item }: { item: LeaderboardItem }) => (
    <Row item={item} />
  ), []);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>{t('leaderboard.title')}</Text>
        <Text style={styles.subtitle}>
          {data ? `${data.total_users} ${t('leaderboard.users_count')}` : ''}
        </Text>
      </View>

      {data?.self && data.self.rank > (data.items.find(i => i.is_self)?.rank ?? 999) && (
        // self è fuori dal top → mostralo in cima come "la tua posizione"
        <View style={styles.selfBanner} testID="leaderboard-self-banner">
          <Text style={styles.selfBannerLabel}>{t('leaderboard.your_rank')}</Text>
          <Text style={styles.selfBannerRank}>#{data.self.rank}</Text>
          <Text style={styles.selfBannerEquity}>{formatCredits(data.self.total_equity)} {t('common.currency_unit')}</Text>
        </View>
      )}

      {loading && !data ? (
        <View style={styles.loading}><ActivityIndicator color={colors.accent} size="large" /></View>
      ) : (
        <FlatList
          testID="leaderboard-list"
          data={data?.items ?? []}
          keyExtractor={(it) => `${it.rank}-${it.display_name}`}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.accent} />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons name="trophy-outline" size={56} color={colors.textMuted} />
              <Text style={styles.emptyText}>{t('leaderboard.empty')}</Text>
            </View>
          }
          renderItem={renderRow}
        />
      )}
      {!!error && <Text style={styles.errorText}>{error}</Text>}
    </SafeAreaView>
  );
}

function Row({ item }: { item: LeaderboardItem }) {
  const { t } = useTranslation();
  const medal = item.rank === 1 ? '🥇' : item.rank === 2 ? '🥈' : item.rank === 3 ? '🥉' : null;
  return (
    <View style={[styles.row, item.is_self && styles.rowSelf]} testID={`leaderboard-row-${item.rank}`}>
      <View style={styles.rankBox}>
        {medal ? <Text style={styles.medal}>{medal}</Text> : <Text style={styles.rank}>#{item.rank}</Text>}
      </View>
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={styles.name} numberOfLines={1}>
          {item.display_name}
          {item.is_self && <Text style={styles.selfTag}>  · {t('leaderboard.you')}</Text>}
        </Text>
        <Text style={styles.subline} numberOfLines={1}>
          {t('leaderboard.positions_value')}: {formatCredits(item.positions_value)} · {t('leaderboard.cash')}: {formatCredits(item.cash_credits)}
        </Text>
      </View>
      <Text style={[styles.equity, item.is_self && { color: colors.accent }]}>
        {formatCredits(item.total_equity)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, paddingBottom: spacing.sm },
  title: { ...typography.h1, color: colors.textPrimary },
  subtitle: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  listContent: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxl + 60 },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  selfBanner: {
    marginHorizontal: spacing.lg, marginVertical: spacing.sm,
    padding: spacing.md, backgroundColor: colors.accent + '22',
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.accent,
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
  },
  selfBannerLabel: { ...typography.caption, color: colors.accent, flex: 1 },
  selfBannerRank: { ...typography.h3, color: colors.accent, fontVariant: ['tabular-nums'] },
  selfBannerEquity: { ...typography.bodyBold, color: colors.textPrimary, fontVariant: ['tabular-nums'] },
  row: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  rowSelf: { backgroundColor: colors.accent + '11', borderRadius: radius.md, paddingHorizontal: spacing.sm },
  rankBox: { width: 44, alignItems: 'center' },
  rank: { ...typography.bodyBold, color: colors.textSecondary, fontVariant: ['tabular-nums'] },
  medal: { fontSize: 22 },
  name: { ...typography.bodyBold, color: colors.textPrimary },
  selfTag: { ...typography.caption, color: colors.accent },
  subline: { ...typography.small, color: colors.textMuted, marginTop: 2, fontVariant: ['tabular-nums'] },
  equity: { ...typography.bodyBold, color: colors.textPrimary, fontVariant: ['tabular-nums'] },
  empty: { padding: spacing.xl, alignItems: 'center', gap: spacing.md },
  emptyText: { ...typography.body, color: colors.textSecondary, marginTop: spacing.sm },
  errorText: { color: colors.danger, padding: spacing.md, textAlign: 'center' },
});
