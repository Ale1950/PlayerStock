import { useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ActivityIndicator, FlatList, Pressable, RefreshControl, ScrollView, StyleSheet,
  Text, TextInput, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { listPlayers, type AthletePublic } from '@/src/services/players.service';
import { translateError } from '@/src/services/api';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';
import { formatPrice } from '@/src/utils/formatters';

const FILTERS = [
  { key: 'all', i18n: 'home.filter_all', role: undefined },
  { key: 'POR', i18n: 'home.filter_por', role: 'POR' },
  { key: 'DIF', i18n: 'home.filter_dif', role: 'DIF' },
  { key: 'CC',  i18n: 'home.filter_cc',  role: 'CC'  },
  { key: 'ATT', i18n: 'home.filter_att', role: 'ATT' },
] as const;

export default function Home() {
  const { t } = useTranslation();
  const router = useRouter();
  const [players, setPlayers] = useState<AthletePublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<typeof FILTERS[number]['key']>('all');
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchPlayers = useCallback(async (pageNum: number, append = false) => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const roleParam = FILTERS.find(f => f.key === filter)?.role;
      const data = await listPlayers({
        role: roleParam, q: search || undefined,
        page: pageNum, page_size: 30,
      });
      setTotal(data.total);
      setPlayers(prev => append ? [...prev, ...data.items] : data.items);
      setPage(data.page);
    } catch (e) {
      setError(translateError(e));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filter, search, loading]);

  useEffect(() => {
    fetchPlayers(1, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, search]);

  const onRefresh = () => { setRefreshing(true); fetchPlayers(1, false); };
  const onEndReached = () => {
    if (!loading && players.length < total) fetchPlayers(page + 1, true);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>{t('home.title')}</Text>
          <Text style={styles.subtitle}>{t('home.subtitle')} · {total} {t('common.currency_unit') ? '' : ''}</Text>
        </View>
      </View>

      <View style={styles.searchRow}>
        <TextInput
          testID="home-search-input"
          placeholder={t('home.search_placeholder')}
          placeholderTextColor={colors.textMuted}
          style={styles.search}
          value={search}
          onChangeText={setSearch}
          returnKeyType="search"
        />
      </View>

      <ScrollView
        horizontal showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chipsRow}
        style={styles.chipsScroll}
        testID="home-filters-scroll"
      >
        {FILTERS.map(f => {
          const active = filter === f.key;
          return (
            <Pressable
              key={f.key}
              testID={`home-filter-${f.key.toLowerCase()}`}
              onPress={() => setFilter(f.key)}
              style={[styles.chip, active && styles.chipActive]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{t(f.i18n)}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <FlatList
        testID="home-players-list"
        data={players}
        keyExtractor={(p) => p._id}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
        onEndReached={onEndReached}
        onEndReachedThreshold={0.5}
        ListEmptyComponent={
          loading ? (
            <View style={styles.empty}><ActivityIndicator color={colors.accent} /></View>
          ) : (
            <View style={styles.empty}><Text style={styles.emptyText}>{t('home.empty')}</Text></View>
          )
        }
        ListFooterComponent={
          loading && players.length > 0 ? (
            <View style={styles.footerLoading}><ActivityIndicator color={colors.accent} /></View>
          ) : null
        }
        renderItem={({ item }) => <PlayerRow player={item} onPress={() => router.push(`/player/${item._id}`)} />}
      />

      {!!error && (
        <View style={styles.errorBar} testID="home-error-bar">
          <Text style={styles.errorBarText}>{error}</Text>
        </View>
      )}

      <View style={styles.disclaimer}>
        <Text style={styles.disclaimerText} testID="home-disclaimer">{t('disclaimer.short')}</Text>
      </View>
    </SafeAreaView>
  );
}

function PlayerRow({ player, onPress }: { player: AthletePublic; onPress: () => void }) {
  const { t } = useTranslation();
  const initials = (player.display_initial[0] || '?').toUpperCase();
  return (
    <Pressable onPress={onPress} testID={`player-row-${player._id}`} style={({ pressed }) => [styles.row, pressed && styles.rowPressed]}>
      <View style={[styles.avatar, { backgroundColor: player.team_color_primary ?? colors.borderStrong }]}>
        <Text style={styles.avatarText}>{initials}</Text>
      </View>
      <View style={styles.rowMain}>
        <Text style={styles.rowName} numberOfLines={1}>{player.display_label}</Text>
        <Text style={styles.rowMeta} numberOfLines={1}>
          {player.role} · {player.nationality_iso3} · {player.age ?? '?'} · {player.team_fantasy_name}
        </Text>
      </View>
      <View style={styles.rowRight}>
        <Text style={styles.rowPrice}>€{formatPrice(player.prezzo_corrente_crediti)}</Text>
        <Text style={styles.rowPriceLabel}>{t('player.price_current')}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, paddingBottom: spacing.sm,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' },
  title: { ...typography.h1, color: colors.textPrimary },
  subtitle: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  searchRow: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm },
  search: {
    backgroundColor: colors.card, borderRadius: radius.md, paddingHorizontal: spacing.md,
    paddingVertical: 10, color: colors.textPrimary, borderWidth: 1, borderColor: colors.border,
    fontSize: 14,
  },
  chipsScroll: { maxHeight: 56 },
  chipsRow: { paddingHorizontal: spacing.lg, gap: spacing.sm, paddingVertical: spacing.md, alignItems: 'center' },
  chip: {
    paddingHorizontal: spacing.md, height: 36, justifyContent: 'center', alignItems: 'center',
    borderRadius: radius.pill, backgroundColor: colors.card,
    borderWidth: 1, borderColor: colors.border, flexShrink: 0,
  },
  chipActive: { backgroundColor: colors.accent + '22', borderColor: colors.accent },
  chipText: { ...typography.small, color: colors.textSecondary, fontWeight: '600' },
  chipTextActive: { color: colors.accent },
  listContent: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxl + 80 },
  row: {
    flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border, gap: spacing.md,
  },
  rowPressed: { opacity: 0.7, backgroundColor: colors.cardHover },
  avatar: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  avatarText: { color: '#FFF', fontWeight: '700', fontSize: 16 },
  rowMain: { flex: 1, minWidth: 0 },
  rowName: { ...typography.bodyBold, color: colors.textPrimary },
  rowMeta: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  rowRight: { alignItems: 'flex-end', minWidth: 90 },
  rowPrice: { ...typography.mono, color: colors.textPrimary, fontWeight: '700' },
  rowPriceLabel: { ...typography.caption, color: colors.textMuted },
  empty: { paddingVertical: spacing.xxl, alignItems: 'center' },
  emptyText: { ...typography.body, color: colors.textSecondary },
  footerLoading: { paddingVertical: spacing.lg, alignItems: 'center' },
  errorBar: {
    position: 'absolute', bottom: 80, left: spacing.lg, right: spacing.lg,
    backgroundColor: '#2D0F12', padding: spacing.md, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.danger,
  },
  errorBarText: { ...typography.small, color: '#FFC9CC' },
  disclaimer: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    paddingHorizontal: spacing.md, paddingVertical: 6,
    backgroundColor: colors.bgElevated, borderTopWidth: 1, borderTopColor: colors.border,
  },
  disclaimerText: { ...typography.caption, color: colors.textMuted, textAlign: 'center' },
});
