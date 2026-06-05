import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ActivityIndicator, FlatList, Pressable, RefreshControl,
  StyleSheet, Text, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Sparkline } from '@/src/components/Sparkline';
import { translateError } from '@/src/services/api';
import {
  getPortfolio, getPriceHistory, type Position, type PortfolioResponse,
} from '@/src/services/portfolio.service';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';
import { formatCredits, formatPrice } from '@/src/utils/formatters';

export default function Portfolio() {
  const { t } = useTranslation();
  const router = useRouter();
  const [data, setData] = useState<PortfolioResponse | null>(null);
  const [sparklines, setSparklines] = useState<Record<string, number[]>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const p = await getPortfolio();
      setData(p);
      // sparkline in parallelo per le prime 10 posizioni
      const tasks = p.positions.slice(0, 10).map(async (pos) => {
        try {
          const h = await getPriceHistory(pos.athlete_id, 30);
          return [pos.athlete_id, h.points.map((x) => x.price)] as const;
        } catch { return [pos.athlete_id, []] as const; }
      });
      const results = await Promise.all(tasks);
      const map: Record<string, number[]> = {};
      results.forEach(([id, arr]) => { map[id] = arr; });
      setSparklines(map);
    } catch (e) { setError(translateError(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useFocusEffect(useCallback(() => { setLoading(true); load(); }, [load]));

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>{t('portfolio.title')}</Text>
      </View>

      {loading && !data ? (
        <View style={styles.loading}><ActivityIndicator color={colors.accent} size="large" /></View>
      ) : (
        <FlatList
          testID="portfolio-positions-list"
          data={data?.positions ?? []}
          keyExtractor={(p) => p.athlete_id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.accent} />
          }
          ListHeaderComponent={data ? <TotalsCard totals={data.totals} /> : null}
          ListEmptyComponent={
            <View style={styles.empty} testID="portfolio-empty">
              <Ionicons name="briefcase-outline" size={56} color={colors.textMuted} />
              <Text style={styles.emptyTitle}>{t('portfolio.empty_title')}</Text>
              <Text style={styles.emptySub}>{t('portfolio.empty_subtitle')}</Text>
            </View>
          }
          renderItem={({ item }) => (
            <PositionRow
              position={item}
              spark={sparklines[item.athlete_id]}
              onPress={() => router.push(`/player/${item.athlete_id}`)}
            />
          )}
        />
      )}

      {!!error && (
        <View style={styles.errorBar} testID="portfolio-error">
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

function TotalsCard({ totals }: { totals: PortfolioResponse['totals'] }) {
  const { t } = useTranslation();
  const isUp = (totals.total_pnl_abs ?? 0) >= 0;
  const pnlColor = isUp ? colors.up : colors.down;
  return (
    <View style={styles.totalsCard} testID="portfolio-totals-card">
      <Text style={styles.totalsLabel}>{t('portfolio.total_equity')}</Text>
      <Text style={styles.totalsValue} testID="portfolio-total-equity">
        {formatCredits(totals.total_equity)} <Text style={styles.totalsUnit}>{t('common.currency_unit')}</Text>
      </Text>
      <View style={styles.totalsBreakdown}>
        <BreakdownCell label={t('portfolio.cash')} value={formatCredits(totals.cash_credits)} />
        <View style={styles.divider} />
        <BreakdownCell label={t('portfolio.positions_value')} value={formatCredits(totals.positions_value)} />
        <View style={styles.divider} />
        <BreakdownCell
          label={t('portfolio.pnl')}
          value={`${isUp ? '+' : ''}${formatCredits(totals.total_pnl_abs)}`}
          valueColor={pnlColor}
          extra={totals.total_pnl_pct != null ? `${isUp ? '+' : ''}${totals.total_pnl_pct.toFixed(2)}%` : '—'}
          extraColor={pnlColor}
        />
      </View>
    </View>
  );
}

function BreakdownCell({ label, value, valueColor, extra, extraColor }: {
  label: string; value: string; valueColor?: string; extra?: string; extraColor?: string;
}) {
  return (
    <View style={styles.breakdownCell}>
      <Text style={styles.breakdownLabel}>{label}</Text>
      <Text style={[styles.breakdownValue, valueColor ? { color: valueColor } : null]}>{value}</Text>
      {!!extra && <Text style={[styles.breakdownExtra, extraColor ? { color: extraColor } : null]}>{extra}</Text>}
    </View>
  );
}

function PositionRow({ position, spark, onPress }: { position: Position; spark?: number[]; onPress: () => void }) {
  const isUp = (position.pnl_abs ?? 0) >= 0;
  const initials = (position.display_initial[0] || '?').toUpperCase();
  return (
    <Pressable
      onPress={onPress}
      testID={`portfolio-position-${position.athlete_id}`}
      style={({ pressed }) => [styles.row, pressed && styles.rowPressed]}
    >
      <View style={[styles.avatar, { backgroundColor: position.team_color_primary ?? colors.borderStrong }]}>
        <Text style={styles.avatarText}>{initials}</Text>
      </View>
      <View style={styles.rowMain}>
        <Text style={styles.rowName} numberOfLines={1}>{position.display_label}</Text>
        <Text style={styles.rowMeta} numberOfLines={1}>
          {position.role} · {position.nationality_iso3} · {position.team_fantasy_name}
        </Text>
        <Text style={styles.rowQty}>
          {position.quantity.toLocaleString('it-IT')} q × €{formatPrice(position.current_price)} = €{formatPrice(position.current_value)}
        </Text>
      </View>
      <View style={styles.rowRight}>
        {spark && spark.length > 1 && <Sparkline prices={spark} positive={isUp} testID={`spark-${position.athlete_id}`} />}
        <Text style={[styles.pnlText, { color: isUp ? colors.up : colors.down }]} testID={`pnl-pct-${position.athlete_id}`}>
          {isUp ? '+' : ''}{position.pnl_pct != null ? position.pnl_pct.toFixed(2) + '%' : '—'}
        </Text>
        <Text style={[styles.pnlAbs, { color: isUp ? colors.up : colors.down }]}>
          {isUp ? '+' : ''}€{formatPrice(position.pnl_abs)}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, paddingBottom: spacing.sm },
  title: { ...typography.h1, color: colors.textPrimary },
  listContent: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxl + 60 },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },

  totalsCard: {
    padding: spacing.lg, backgroundColor: colors.card,
    borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border,
    marginBottom: spacing.md, marginTop: spacing.sm,
  },
  totalsLabel: { ...typography.caption, color: colors.textSecondary },
  totalsValue: { ...typography.h1, color: colors.textPrimary, marginTop: spacing.xs, fontVariant: ['tabular-nums'] },
  totalsUnit: { ...typography.h3, color: colors.textSecondary, fontWeight: '500' },
  totalsBreakdown: {
    flexDirection: 'row', marginTop: spacing.md,
    borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.md,
    alignItems: 'flex-start',
  },
  breakdownCell: { flex: 1, alignItems: 'flex-start' },
  breakdownLabel: { ...typography.caption, color: colors.textMuted },
  breakdownValue: { ...typography.bodyBold, color: colors.textPrimary, marginTop: 2, fontVariant: ['tabular-nums'] },
  breakdownExtra: { ...typography.small, marginTop: 2, fontVariant: ['tabular-nums'] },
  divider: { width: 1, backgroundColor: colors.border, marginHorizontal: spacing.sm },

  row: {
    flexDirection: 'row', paddingVertical: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border, gap: spacing.md,
  },
  rowPressed: { opacity: 0.7, backgroundColor: colors.cardHover },
  avatar: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  avatarText: { color: '#FFF', fontWeight: '700', fontSize: 16 },
  rowMain: { flex: 1, minWidth: 0 },
  rowName: { ...typography.bodyBold, color: colors.textPrimary },
  rowMeta: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  rowQty: { ...typography.small, color: colors.textMuted, marginTop: 4, fontVariant: ['tabular-nums'] },
  rowRight: { alignItems: 'flex-end', minWidth: 90, gap: 2 },
  pnlText: { ...typography.bodyBold, fontVariant: ['tabular-nums'] },
  pnlAbs: { ...typography.small, fontVariant: ['tabular-nums'] },

  empty: { padding: spacing.xl, alignItems: 'center', gap: spacing.sm },
  emptyTitle: { ...typography.h2, color: colors.textPrimary, marginTop: spacing.md },
  emptySub: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  errorBar: {
    position: 'absolute', bottom: 80, left: spacing.lg, right: spacing.lg,
    backgroundColor: '#2D0F12', padding: spacing.md, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.danger,
  },
  errorText: { ...typography.small, color: '#FFC9CC' },
});
