import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { PriceChart } from '@/src/components/PriceChart';
import { StateView } from '@/src/components/StateView';
import { TeamBadge } from '@/src/components/TeamBadge';
import { useResponsive } from '@/src/hooks/use-responsive';
import { translateError } from '@/src/services/api';
import { getPortfolio, type PortfolioResponse, type Position } from '@/src/services/portfolio.service';
import { getPortfolioAnalytics, type Indices, type Period, type PortfolioAnalytics, type PositionAnalytics } from '@/src/services/stats.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { type ThemeColors } from '@/src/theme/tokens';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { formatCredits, formatPrice } from '@/src/utils/formatters';

const PERIODS: { key: Period; label: string }[] = [
  { key: '1S', label: '1S' }, { key: '1M', label: '1M' }, { key: '3M', label: '3M' }, { key: 'all', label: 'TUTTO' },
];
const signColor = (c: ThemeColors, n: number | null | undefined) => (n ?? 0) >= 0 ? c.green : c.red;

export default function Portfolio() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useTheme();
  const { isDesktop } = useResponsive();
  const styles = useMemo(() => makeStyles(colors), [colors]);

  const [data, setData] = useState<PortfolioResponse | null>(null);
  const [an, setAn] = useState<PortfolioAnalytics | null>(null);
  const [period, setPeriod] = useState<Period>('1M');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (p: Period) => {
    setError(null);
    try {
      const [pf, a] = await Promise.all([getPortfolio(), getPortfolioAnalytics(p)]);
      setData(pf); setAn(a);
    } catch (e) { setError(translateError(e)); }
    finally { setLoading(false); }
  }, []);

  useFocusEffect(useCallback(() => { setLoading(true); load(period); }, [load, period]));
  const onPeriod = (p: Period) => { setPeriod(p); setLoading(true); load(p); };

  const anById = useMemo(() => {
    const m: Record<string, PositionAnalytics> = {};
    an?.positions.forEach((p) => { m[p.athlete_id] = p; });
    return m;
  }, [an]);

  const totals = data?.totals;
  const equityVals = an?.equity.points.map((p) => p.equity) ?? [];
  const bestUserVals = an?.best_user?.equity.points.map((p) => p.equity) ?? [];
  const bestPlayerSeries = an?.market_best_player?.series.map((p) => p.price) ?? [];

  return (
    <View style={styles.safe}>
      <GeometricBackground />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('portfolio.title')}</Text>

        {/* HERO patrimonio */}
        {totals && (
          <View style={styles.hero}>
            <Text style={styles.heroLabel}>{t('portfolio.total_equity')}</Text>
            <Text style={styles.heroValue}>{formatCredits(totals.total_equity)} <Text style={styles.heroUnit}>{t('common.currency_unit')}</Text></Text>
            <View style={styles.heroRow}>
              <Break label={t('portfolio.cash')} value={formatCredits(totals.cash_eur)} c={colors} styles={styles} />
              <View style={styles.divider} />
              <Break label={t('portfolio.positions_value')} value={formatCredits(totals.positions_value)} c={colors} styles={styles} />
              <View style={styles.divider} />
              <Break label={t('portfolio.pnl')} value={`${totals.total_pnl_abs >= 0 ? '+' : ''}${formatCredits(totals.total_pnl_abs)}`}
                tint={signColor(colors, totals.total_pnl_abs)} c={colors} styles={styles} />
            </View>
          </View>
        )}

        {/* PERIODO + grafico equity */}
        <View style={styles.periodRow}>
          {PERIODS.map((p) => (
            <Pressable key={p.key} onPress={() => onPeriod(p.key)} testID={`period-${p.key}`}
              style={[styles.periodBtn, period === p.key && { backgroundColor: colors.cyan, borderColor: colors.cyan }]}>
              <Text style={[styles.periodText, { color: period === p.key ? colors.onAccent : colors.muted }]}>{p.label}</Text>
            </Pressable>
          ))}
        </View>

        <View style={styles.card}>
          <View style={styles.cardHead}>
            <Text style={styles.cardLabel}>{t('portfolio.total_equity')} · {an?.granularity === 'week' ? 'sett.' : 'giorni'}</Text>
            {an?.best_user && (
              <Text style={styles.compareTag}>vs <Text style={{ color: colors.cyan }}>{an.best_user.pseudonym}</Text> (tratteggio)</Text>
            )}
          </View>
          {equityVals.length >= 2
            ? <PriceChart prices={equityVals} overlay={bestUserVals.length >= 2 ? bestUserVals : undefined} width={isDesktop ? 760 : 300} height={140} testID="equity-chart" />
            : <Text style={styles.nd}>{t('home.empty')} — storico insufficiente</Text>}
        </View>

        {/* INDICI di portafoglio */}
        {an && (
          <View style={styles.card}>
            <Text style={styles.cardLabel}>INDICI PORTAFOGLIO ({period})</Text>
            <IndexGrid ix={an.portfolio_indices} c={colors} styles={styles} isDesktop={isDesktop} />
            {an.best_user && (
              <Text style={styles.compareLine}>
                Tu {an.portfolio_indices.return_pct >= 0 ? '+' : ''}{an.portfolio_indices.return_pct.toFixed(1)}%
                {'  ·  '}miglior utente <Text style={{ color: colors.cyan }}>{an.best_user.pseudonym}</Text> {an.best_user.return_pct >= 0 ? '+' : ''}{an.best_user.return_pct.toFixed(1)}%
              </Text>
            )}
          </View>
        )}

        {/* POSIZIONI */}
        <Text style={styles.section}>POSIZIONI</Text>
        {loading || error || !data?.positions.length ? (
          <StateView loading={loading} error={error} empty={!loading && !error && !data?.positions.length}
            emptyLabel={t('portfolio.empty_title')} icon="briefcase-outline" />
        ) : (
          data.positions.map((pos) => (
            <PositionItem key={pos.athlete_id} pos={pos} a={anById[pos.athlete_id]} bestPlayer={bestPlayerSeries}
              bestPlayerLabel={an?.market_best_player?.display_label ?? null}
              expanded={expanded === pos.athlete_id} onToggle={() => setExpanded(expanded === pos.athlete_id ? null : pos.athlete_id)}
              onOpen={() => router.push(`/player/${pos.athlete_id}`)} c={colors} styles={styles} isDesktop={isDesktop} />
          ))
        )}
      </ScrollView>
    </View>
  );
}

function Break({ label, value, tint, c, styles }: { label: string; value: string; tint?: string; c: ThemeColors; styles: any }) {
  return (
    <View style={styles.break}>
      <Text style={styles.breakLabel}>{label}</Text>
      <Text style={[styles.breakValue, tint ? { color: tint } : null]}>{value}</Text>
    </View>
  );
}

function IndexGrid({ ix, c, styles, isDesktop }: { ix: Indices; c: ThemeColors; styles: any; isDesktop: boolean }) {
  const items = [
    { l: 'RENDIMENTO', v: `${ix.return_pct >= 0 ? '+' : ''}${ix.return_pct.toFixed(1)}%`, t: ix.return_pct >= 0 ? c.green : c.red },
    { l: 'VOLATILITÀ', v: `${ix.volatility.toFixed(1)}%`, t: c.amber },
    { l: 'MAX DD', v: `${ix.max_drawdown.toFixed(1)}%`, t: c.red },
    { l: 'BETA', v: ix.beta.toFixed(2), t: c.cyan },
    { l: 'SHARPE', v: ix.sharpe.toFixed(2), t: c.purple },
  ];
  return (
    <View style={styles.ixGrid}>
      {items.map((it) => (
        <View key={it.l} style={[styles.ixCell, isDesktop && { flexBasis: '18%' }]}>
          <Text style={[styles.ixVal, { color: it.t }]}>{it.v}</Text>
          <Text style={styles.ixLabel}>{it.l}</Text>
        </View>
      ))}
    </View>
  );
}

function PositionItem({ pos, a, bestPlayer, bestPlayerLabel, expanded, onToggle, onOpen, c, styles, isDesktop }: {
  pos: Position; a?: PositionAnalytics; bestPlayer: number[]; bestPlayerLabel: string | null;
  expanded: boolean; onToggle: () => void; onOpen: () => void; c: ThemeColors; styles: any; isDesktop: boolean;
}) {
  const up = (pos.pnl_abs ?? 0) >= 0;
  const series = a?.series.map((p) => p.price) ?? [];
  const dW = a?.delta_week_pct;
  return (
    <View style={styles.posCard}>
      <Pressable onPress={onToggle} style={styles.posHead}>
        <TeamBadge primary={pos.team_color_primary} name={pos.team_fantasy_name} size={36} />
        <View style={{ flex: 1, minWidth: 0 }}>
          <Text style={styles.posName} numberOfLines={1}>{pos.display_label}</Text>
          <Text style={styles.posMeta} numberOfLines={1}>{pos.quantity.toLocaleString('it-IT')} q · €{formatPrice(pos.current_price)}{dW != null ? ` · 1S ${dW >= 0 ? '+' : ''}${dW.toFixed(1)}%` : ''}</Text>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text style={styles.posValue}>€{formatCredits(pos.current_value)}</Text>
          <Text style={[styles.posPnl, { color: up ? c.green : c.red }]}>{up ? '+' : ''}{pos.pnl_pct != null ? pos.pnl_pct.toFixed(1) + '%' : '—'}</Text>
        </View>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={18} color={c.muted} />
      </Pressable>

      {expanded && (
        <View style={styles.posBody}>
          {series.length >= 2
            ? <PriceChart prices={series} overlay={bestPlayer.length >= 2 ? bestPlayer : undefined} width={isDesktop ? 720 : 290} height={110} />
            : <Text style={styles.nd}>storico insufficiente</Text>}
          {bestPlayerLabel && <Text style={styles.overlayTag}>— — confronto col migliore: <Text style={{ color: c.cyan }}>{bestPlayerLabel}</Text></Text>}
          {a && <IndexGrid ix={a.indices} c={c} styles={styles} isDesktop={isDesktop} />}
          <Pressable onPress={onOpen} style={styles.openBtn}><Text style={styles.openTxt}>APRI DETTAGLIO →</Text></Pressable>
        </View>
      )}
    </View>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 60, gap: spacing.md, maxWidth: 900, width: '100%', alignSelf: 'center' },
  title: { ...typography.pageTitle, color: colors.text },
  hero: { backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.lg },
  heroLabel: { ...typography.caption, color: colors.muted },
  heroValue: { ...typography.mono, fontSize: 32, fontWeight: '700', color: colors.text, marginTop: 4 },
  heroUnit: { ...typography.h3, color: colors.muted },
  heroRow: { flexDirection: 'row', marginTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.md },
  break: { flex: 1 },
  breakLabel: { ...typography.caption, color: colors.muted },
  breakValue: { ...typography.bodyBold, color: colors.text, marginTop: 2, fontVariant: ['tabular-nums'] },
  divider: { width: 1, backgroundColor: colors.border, marginHorizontal: spacing.sm },
  periodRow: { flexDirection: 'row', gap: spacing.sm },
  periodBtn: { paddingHorizontal: spacing.md, height: 30, justifyContent: 'center', borderRadius: radius.pill, borderWidth: borderW, borderColor: colors.border, backgroundColor: colors.surfaceAlt },
  periodText: { ...typography.monoLabel },
  card: { backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.md, alignItems: 'center', gap: spacing.sm },
  cardHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', alignSelf: 'stretch' },
  cardLabel: { ...typography.caption, color: colors.muted, alignSelf: 'flex-start' },
  compareTag: { ...typography.small, color: colors.muted },
  nd: { ...typography.small, color: colors.muted, paddingVertical: spacing.lg },
  ixGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, alignSelf: 'stretch' },
  ixCell: { flexGrow: 1, flexBasis: '30%', backgroundColor: colors.bg, borderRadius: radius.md, borderWidth: borderW, borderColor: colors.border, padding: spacing.sm, alignItems: 'center' },
  ixVal: { ...typography.mono, fontSize: 16, fontWeight: '700' },
  ixLabel: { ...typography.caption, color: colors.muted, marginTop: 2 },
  compareLine: { ...typography.small, color: colors.text, alignSelf: 'flex-start', marginTop: 4 },
  section: { ...typography.caption, color: colors.muted, marginTop: spacing.sm },
  posCard: { backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, overflow: 'hidden' },
  posHead: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md },
  posName: { ...typography.bodyBold, color: colors.text },
  posMeta: { ...typography.small, color: colors.muted, marginTop: 2 },
  posValue: { ...typography.mono, color: colors.text, fontWeight: '700' },
  posPnl: { ...typography.monoLabel, marginTop: 1 },
  posBody: { padding: spacing.md, borderTopWidth: 1, borderTopColor: colors.border, gap: spacing.sm, alignItems: 'center' },
  overlayTag: { ...typography.small, color: colors.muted, alignSelf: 'flex-start' },
  openBtn: { alignSelf: 'flex-start', marginTop: 2 },
  openTxt: { ...typography.monoLabel, color: colors.cyan },
});
