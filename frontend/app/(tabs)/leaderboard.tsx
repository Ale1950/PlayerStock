import { useFocusEffect } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { ResponsiveTable, type Column, type SortState } from '@/src/components/ResponsiveTable';
import { Sparkline } from '@/src/components/Sparkline';
import { StateView } from '@/src/components/StateView';
import { translateError } from '@/src/services/api';
import { getLeaderboardAnalytics, type LeaderItem, type LeaderboardAnalytics, type Period } from '@/src/services/stats.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { type ThemeColors } from '@/src/theme/tokens';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { formatCredits } from '@/src/utils/formatters';

const PERIODS: { key: Period; label: string }[] = [
  { key: '1S', label: '1S' }, { key: '1M', label: '1M' }, { key: '3M', label: '3M' }, { key: 'all', label: 'TUTTO' },
];
const TABS: { key: string; label: string }[] = [
  { key: 'equity', label: 'PATRIMONIO' }, { key: 'return_pct', label: 'RENDIMENTO' }, { key: 'return_week_pct', label: 'SETTIMANA' },
];
const MEDAL = ['🥇', '🥈', '🥉'];
const sgn = (c: ThemeColors, n: number | null | undefined) => (n ?? 0) >= 0 ? c.green : c.red;
const pct = (n: number | null | undefined) => n == null ? '—' : `${n >= 0 ? '+' : ''}${n.toFixed(1)}%`;

export default function Leaderboard() {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);

  const [data, setData] = useState<LeaderboardAnalytics | null>(null);
  const [period, setPeriod] = useState<Period>('1M');
  const [sort, setSort] = useState<SortState>({ key: 'equity', dir: 'desc' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (p: Period) => {
    setError(null);
    try { setData(await getLeaderboardAnalytics(p)); }
    catch (e) { setError(translateError(e)); }
    finally { setLoading(false); }
  }, []);

  useFocusEffect(useCallback(() => { setLoading(true); load(period); }, [load, period]));

  const items = useMemo(() => {
    const list = [...(data?.items ?? [])];
    if (sort) {
      const dir = sort.dir === 'asc' ? 1 : -1;
      const val = (i: LeaderItem): number => {
        const v = (i as unknown as Record<string, number | null>)[sort.key];
        return v == null ? -Infinity : v;
      };
      list.sort((a, b) => (val(a) - val(b)) * dir);
    }
    return list;
  }, [data, sort]);

  const onSort = (key: string) => setSort((s) => s?.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' });

  const Pseudo = (i: LeaderItem) => (
    <View style={styles.pseudoCell}>
      <Text style={[styles.pseudo, i.is_self && { color: colors.cyan }]} numberOfLines={1}>{i.pseudonym}</Text>
      {i.is_self && <View style={styles.youTag}><Text style={styles.youTxt}>TU</Text></View>}
    </View>
  );
  const rankLabel = (pos: number) => (pos < 3 && sort?.dir === 'desc' ? MEDAL[pos] : `#${pos + 1}`);

  const columns: Column<LeaderItem>[] = [
    { key: '_rank', label: '#', width: 44, render: (i) => <Text style={styles.rank}>{rankLabel(items.indexOf(i))}</Text> },
    { key: 'pseudonym', label: 'PSEUDONIMO', flex: 1.4, render: Pseudo },
    { key: 'equity', label: 'PATRIMONIO', width: 110, align: 'right', sortable: true, render: (i) => <Text style={styles.num}>€{formatCredits(i.equity)}</Text> },
    { key: 'return_pct', label: 'REND.', width: 78, align: 'right', sortable: true, render: (i) => <Text style={[styles.num, { color: sgn(colors, i.return_pct) }]}>{pct(i.return_pct)}</Text> },
    { key: 'roi_vs_market_pct', label: 'ROI/MKT', width: 84, align: 'right', sortable: true, render: (i) => <Text style={[styles.num, { color: sgn(colors, i.roi_vs_market_pct) }]}>{pct(i.roi_vs_market_pct)}</Text> },
    { key: 'win_rate', label: 'WIN%', width: 64, align: 'right', sortable: true, render: (i) => <Text style={styles.num}>{i.win_rate == null ? '—' : `${i.win_rate.toFixed(0)}%`}</Text> },
    { key: 'volatility', label: 'VOL', width: 56, align: 'right', sortable: true, render: (i) => <Text style={[styles.num, { color: colors.amber }]}>{i.volatility.toFixed(1)}</Text> },
    { key: '_trend', label: 'TREND', width: 64, render: (i) => i.trend.length > 1 ? <Sparkline prices={i.trend} positive={i.trend[i.trend.length - 1] >= i.trend[0]} width={56} height={22} /> : <Text style={styles.dim}>—</Text> },
  ];

  const Card = (i: LeaderItem) => {
    const pos = items.indexOf(i);
    return (
      <View style={[styles.card, i.is_self && { borderColor: colors.cyan, borderWidth: 1.5 }]}>
        <View style={styles.cardTop}>
          <Text style={styles.cardRank}>{rankLabel(pos)}</Text>
          {Pseudo(i)}
          <View style={{ flex: 1 }} />
          <Text style={styles.cardEquity}>€{formatCredits(i.equity)}</Text>
        </View>
        <View style={styles.cardMetrics}>
          <Metric label="REND." value={pct(i.return_pct)} tint={sgn(colors, i.return_pct)} styles={styles} />
          <Metric label="ROI/MKT" value={pct(i.roi_vs_market_pct)} tint={sgn(colors, i.roi_vs_market_pct)} styles={styles} />
          <Metric label="WIN%" value={i.win_rate == null ? '—' : `${i.win_rate.toFixed(0)}%`} styles={styles} />
          <Metric label="VOL" value={i.volatility.toFixed(1)} tint={colors.amber} styles={styles} />
          {i.trend.length > 1 && <Sparkline prices={i.trend} positive={i.trend[i.trend.length - 1] >= i.trend[0]} width={52} height={22} />}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.safe}>
      <GeometricBackground />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('leaderboard.title')}</Text>
        {data && <Text style={styles.sub}>{data.total_users} trader · mercato {pct(data.market_return_pct)}</Text>}

        <View style={styles.rowControls}>
          {PERIODS.map((p) => (
            <Pressable key={p.key} onPress={() => { setPeriod(p.key); setLoading(true); load(p.key); }}
              style={[styles.pill, period === p.key && styles.pillActive]}>
              <Text style={[styles.pillTxt, { color: period === p.key ? colors.onAccent : colors.muted }]}>{p.label}</Text>
            </Pressable>
          ))}
        </View>
        <View style={styles.rowControls}>
          {TABS.map((tb) => (
            <Pressable key={tb.key} onPress={() => setSort({ key: tb.key, dir: 'desc' })}
              style={[styles.tab, sort?.key === tb.key && { borderColor: colors.cyan, backgroundColor: colors.surfaceAlt }]}>
              <Text style={[styles.tabTxt, { color: sort?.key === tb.key ? colors.cyan : colors.muted }]}>{tb.label}</Text>
            </Pressable>
          ))}
        </View>

        {loading || error || items.length === 0 ? (
          <StateView loading={loading} error={error} empty={!loading && !error && items.length === 0} emptyLabel="Nessun trader" icon="trophy-outline" />
        ) : (
          <ResponsiveTable
            data={items}
            columns={columns}
            renderCard={Card}
            keyExtractor={(i) => i.pseudonym + i.rank}
            sort={sort}
            onSort={onSort}
            rowStyle={(i) => i.is_self ? { backgroundColor: colors.cyan + '18' } : undefined}
          />
        )}
      </ScrollView>
    </View>
  );
}

function Metric({ label, value, tint, styles }: { label: string; value: string; tint?: string; styles: ReturnType<typeof makeStyles> }) {
  return (
    <View style={styles.metric}>
      <Text style={[styles.metricVal, tint ? { color: tint } : null]}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 60, gap: spacing.md, maxWidth: 1000, width: '100%', alignSelf: 'center' },
  title: { ...typography.pageTitle, color: colors.text },
  sub: { ...typography.caption, color: colors.muted },
  rowControls: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  pill: { paddingHorizontal: spacing.md, height: 30, justifyContent: 'center', borderRadius: radius.pill, borderWidth: borderW, borderColor: colors.border, backgroundColor: colors.surfaceAlt },
  pillActive: { backgroundColor: colors.cyan, borderColor: colors.cyan },
  pillTxt: { ...typography.monoLabel },
  tab: { paddingHorizontal: spacing.md, height: 30, justifyContent: 'center', borderRadius: radius.md, borderWidth: borderW, borderColor: colors.border, backgroundColor: colors.surface },
  tabTxt: { ...typography.monoLabel },
  rank: { ...typography.mono, fontSize: 15, color: colors.text },
  pseudoCell: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  pseudo: { ...typography.bodyBold, color: colors.text },
  youTag: { backgroundColor: colors.cyan, borderRadius: radius.sm, paddingHorizontal: 5, paddingVertical: 1 },
  youTxt: { ...typography.monoLabel, fontSize: 9, color: colors.onAccent },
  num: { ...typography.mono, color: colors.text, fontWeight: '700' },
  dim: { ...typography.small, color: colors.muted },
  card: { backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.md, gap: spacing.sm },
  cardTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  cardRank: { ...typography.mono, fontSize: 18, color: colors.text, minWidth: 28 },
  cardEquity: { ...typography.mono, color: colors.text, fontWeight: '700' },
  cardMetrics: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, flexWrap: 'wrap' },
  metric: { alignItems: 'flex-start' },
  metricVal: { ...typography.mono, fontSize: 14, fontWeight: '700', color: colors.text },
  metricLabel: { ...typography.caption, color: colors.muted },
});
