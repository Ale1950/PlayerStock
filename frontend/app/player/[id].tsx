import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PriceChart } from '@/src/components/PriceChart';
import { StatTile } from '@/src/components/StatTile';
import { ValueBars } from '@/src/components/ValueBars';
import { translateError } from '@/src/services/api';
import { getMyHoldings, getQuote, placeOrder, type QuoteResponse } from '@/src/services/market.service';
import { getPlayer, type AthletePublic } from '@/src/services/players.service';
import { getPriceHistory } from '@/src/services/portfolio.service';
import { getAthleteStats, type AthleteStats } from '@/src/services/stats.service';
import { getBalance } from '@/src/services/wallet.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { gradients, type ThemeColors } from '@/src/theme/tokens';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { formatCredits, formatEuroM, formatInt, formatPrice } from '@/src/utils/formatters';

const PERIODS = [{ key: '24h', limit: 24 }, { key: '7d', limit: 56 }, { key: '30d', limit: 90 }] as const;
const compact = (n: number) => n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}K` : `${Math.round(n)}`;
const roleTint = (c: ThemeColors, r?: string) => r === 'ATT' ? c.red : r === 'CC' ? c.purple : r === 'DIF' ? c.cyan : c.chartBlue;

export default function PlayerDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { t } = useTranslation();
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);

  const [player, setPlayer] = useState<AthletePublic | null>(null);
  const [stats, setStats] = useState<AthleteStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<typeof PERIODS[number]['key']>('7d');
  const [prices, setPrices] = useState<number[]>([]);

  const [balance, setBalance] = useState<number | null>(null);
  const [owned, setOwned] = useState(0);
  const [qty, setQty] = useState('1');
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [submitting, setSubmitting] = useState<null | 'buy' | 'sell'>(null);
  const [tradeError, setTradeError] = useState<string | null>(null);
  const [tradeOk, setTradeOk] = useState<string | null>(null);
  const qtyNum = Math.max(0, Math.floor(Number(qty) || 0));

  const loadHistory = useCallback(async (athleteId: string, lim: number) => {
    try { const h = await getPriceHistory(athleteId, lim); setPrices(h.points.map((p) => p.price)); }
    catch { setPrices([]); }
  }, []);

  const loadTrade = useCallback(async (athleteId: string) => {
    const [bal, holdings] = await Promise.allSettled([getBalance(), getMyHoldings()]);
    if (bal.status === 'fulfilled') setBalance(bal.value.balance_eur);
    if (holdings.status === 'fulfilled') setOwned(holdings.value.find((x) => x.athlete_id === athleteId)?.quantity ?? 0);
  }, []);

  useEffect(() => {
    (async () => {
      if (!id) return;
      try {
        setLoading(true);
        const p = await getPlayer(id);
        setPlayer(p);
        getAthleteStats(id).then(setStats).catch(() => setStats(null));
        await Promise.all([loadHistory(id, 56), loadTrade(id)]);
      } catch (e) { setError(translateError(e)); }
      finally { setLoading(false); }
    })();
  }, [id, loadHistory, loadTrade]);

  useEffect(() => {
    if (!id) return;
    const lim = PERIODS.find((p) => p.key === period)!.limit;
    loadHistory(id, lim);
  }, [id, period, loadHistory]);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (!id || qtyNum < 1) { setQuote(null); return; }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try { setQuote(await getQuote(id, qtyNum)); } catch { setQuote(null); }
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [id, qtyNum]);

  const onTrade = useCallback(async (side: 'buy' | 'sell') => {
    if (!id || qtyNum < 1 || submitting) return;
    setSubmitting(side); setTradeError(null); setTradeOk(null);
    try {
      const res = await placeOrder(id, side, qtyNum);
      setBalance(res.new_balance);
      setOwned((prev) => (side === 'buy' ? prev + qtyNum : Math.max(0, prev - qtyNum)));
      setTradeOk(t(side === 'buy' ? 'player.buy_success' : 'player.sell_success'));
      try { setQuote(await getQuote(id, qtyNum)); } catch { /* noop */ }
      try { setPlayer(await getPlayer(id)); } catch { /* noop */ }
      try { getAthleteStats(id).then(setStats); } catch { /* noop */ }
      const lim = PERIODS.find((p) => p.key === period)!.limit;
      loadHistory(id, lim);
    } catch (e) { setTradeError(translateError(e)); }
    finally { setSubmitting(null); }
  }, [id, qtyNum, submitting, t, period, loadHistory]);

  const stepQty = (d: number) => { setQty(String(Math.max(1, qtyNum + d))); setTradeOk(null); };
  const pool = quote?.primary_pool_qty ?? player?.float_quote ?? 0;
  const soldOut = (stats?.sold_out ?? false) || pool <= 0;
  const var24 = stats?.var_24h_pct ?? null;
  const up24 = (var24 ?? 0) >= 0;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.headerBar}>
        <Pressable testID="player-back" onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={24} color={colors.text} />
          <Text style={styles.backText}>{t('player.back')}</Text>
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        {loading && <ActivityIndicator color={colors.cyan} size="large" style={{ marginTop: spacing.xxl }} />}
        {error && <Text style={styles.error}>{error}</Text>}
        {player && (
          <View testID={`player-detail-${player._id}`}>
            {/* hero compatto */}
            <View style={styles.hero}>
              <View style={[styles.roleBar, { backgroundColor: roleTint(colors, player.role) }]} />
              <View style={[styles.avatar, { backgroundColor: player.team_color_primary ?? roleTint(colors, player.role) + '22' }]}>
                <Text style={styles.avatarText}>{player.display_initial[0]}</Text>
              </View>
              <View style={{ flex: 1, minWidth: 0 }}>
                <Text style={styles.name} numberOfLines={1}>{player.display_label}</Text>
                <Text style={styles.meta}>{t(`player.role_${player.role}`)} · {player.nationality_iso3} · {player.age ?? '?'} · {player.team_fantasy_name}</Text>
              </View>
            </View>

            {/* prezzo + var */}
            <View style={styles.priceHead}>
              <Text style={{ fontSize: 11, letterSpacing: 1, color: colors.textSecondary, marginBottom: 2 }} testID="price-quote-label">PREZZO QUOTA (€)</Text>
              <Text style={styles.priceBig} testID="price-quote">€{formatPrice(player.prezzo_corrente_eur)}</Text>
              {var24 != null && (
                <Text style={[styles.priceVar, { color: up24 ? colors.green : colors.red }]}>
                  {up24 ? '▲' : '▼'} {up24 ? '+' : ''}{var24.toFixed(2)}% · 24h
                </Text>
              )}
            </View>

            {/* grafico prezzo + toggle periodo */}
            <View style={styles.chartCard}>
              <View style={styles.periodRow}>
                {PERIODS.map((p) => {
                  const active = period === p.key;
                  return (
                    <Pressable key={p.key} onPress={() => setPeriod(p.key)} testID={`period-${p.key}`}
                      style={[styles.periodBtn, active && { backgroundColor: colors.cyan, borderColor: colors.cyan }]}>
                      <Text style={[styles.periodText, { color: active ? colors.onAccent : colors.muted }]}>{p.key.toUpperCase()}</Text>
                    </Pressable>
                  );
                })}
              </View>
              {prices.length >= 2
                ? <PriceChart prices={prices} width={300} height={120} testID="player-chart" />
                : <View style={styles.chartEmpty}><Text style={styles.chartEmptyTxt}>{t('player.trend')} — n/d</Text></View>}
            </View>

            {/* tessere stat */}
            {stats && (
              <>
                <View style={styles.tilesRow}>
                  <StatTile icon="server-outline" value={`€${compact(stats.market_cap)}`} label="MARKET CAP" tint={colors.amber} gradient={gradients.amber} />
                  <StatTile icon="people-outline" value={formatInt(stats.n_holders)} label="POSSESSORI" tint={colors.cyan} gradient={gradients.cyanTeal} />
                </View>
                <View style={styles.tilesRow}>
                  <StatTile icon="trending-up-outline" value={stats.var_7d_pct != null ? `${stats.var_7d_pct >= 0 ? '+' : ''}${stats.var_7d_pct.toFixed(1)}%` : '—'} label="VAR 7G"
                    tint={(stats.var_7d_pct ?? 0) >= 0 ? colors.green : colors.red} gradient={gradients.cyanTeal} />
                  <StatTile icon="swap-horizontal-outline" value={compact(stats.volume_7d)} label="VOLUME 7G" sub="quote" tint={colors.teal} gradient={gradients.cyanTeal} />
                </View>
                <View style={styles.tilesRow}>
                  <StatTile icon="arrow-up-outline" value={`€${formatPrice(stats.max)}`} label="MAX" tint={colors.green} gradient={gradients.cyanTeal} />
                  <StatTile icon="arrow-down-outline" value={`€${formatPrice(stats.min)}`} label="MIN" tint={colors.red} gradient={gradients.amber} />
                </View>
                <View style={styles.tilesRow}>
                  <StatTile testID="player-market-value" icon="diamond-outline" value={formatEuroM(stats.market_value_eur)} label="VAL. MERCATO" sub="valore €" tint={colors.amber} gradient={gradients.amber} />
                  <StatTile icon="layers-outline"
                    value={stats.sold_out ? 'ESAURITO' : compact(stats.disponibili)}
                    label="DISPONIBILI" sub={`${stats.posseduta_pct.toFixed(1)}% poss.`}
                    tint={stats.sold_out ? colors.red : colors.cyan} gradient={gradients.cyanTeal} />
                </View>

                <View style={styles.card}>
                  <Text style={styles.cardLabel}>SCOSTAMENTO VS VALORE EQUO</Text>
                  <Text style={[styles.scost, { color: (stats.scostamento_vs_equo_pct ?? 0) >= 0 ? colors.green : colors.red }]}>
                    {(stats.scostamento_vs_equo_pct ?? 0) >= 0 ? '+' : ''}{(stats.scostamento_vs_equo_pct ?? 0).toFixed(2)}%
                  </Text>
                  <Text style={styles.cardHint}>deviazione trading {stats.deviazione >= 0 ? '+' : ''}{(stats.deviazione * 100).toFixed(1)}%</Text>
                </View>

                <View style={styles.card}>
                  <Text style={styles.cardLabel}>SCOMPOSIZIONE VALORE</Text>
                  <ValueBars items={[
                    { label: 'RUOLO', value: stats.value_decomposition.base_ruolo },
                    { label: 'SCORE', value: stats.value_decomposition.f_score },
                    { label: 'ETÀ', value: stats.value_decomposition.f_eta },
                    { label: 'MINUTI', value: stats.value_decomposition.f_minutaggio },
                    { label: 'SQUADRA', value: stats.value_decomposition.f_squadra },
                  ]} />
                </View>
              </>
            )}

            {/* compra / vendi (wirato) */}
            <View style={styles.tradeCard} testID="player-trade">
              <Text style={styles.tradeTitle}>{t('player.trade_title')}</Text>
              <View style={styles.tradeInfoRow}>
                <TradeStat label={t('player.balance')} value={balance != null ? `€${formatCredits(balance)}` : '—'} styles={styles} />
                <TradeStat label={t('player.owned')} value={`${formatInt(owned)} q`} styles={styles} />
                <TradeStat label={t('player.pool_available')} value={formatInt(pool)} styles={styles} />
              </View>
              <Text style={styles.qtyLabel}>{t('player.quantity')}</Text>
              <View style={styles.qtyRow}>
                <Pressable testID="trade-qty-minus" onPress={() => stepQty(-1)} style={styles.stepBtn}><Ionicons name="remove" size={20} color={colors.text} /></Pressable>
                <TextInput testID="trade-qty-input" style={styles.qtyInput} value={qty}
                  onChangeText={(v) => { setQty(v.replace(/[^0-9]/g, '')); setTradeOk(null); }} keyboardType="number-pad" inputMode="numeric" selectTextOnFocus />
                <Pressable testID="trade-qty-plus" onPress={() => stepQty(1)} style={styles.stepBtn}><Ionicons name="add" size={20} color={colors.text} /></Pressable>
              </View>
              <View style={styles.previewBox}>
                <View style={styles.previewRow}><Text style={styles.previewLabel}>{t('player.est_cost')}</Text><Text style={styles.previewValue} testID="trade-est-cost">{quote ? `€${formatCredits(quote.buy_cost)}` : '—'}</Text></View>
                <View style={styles.previewRow}><Text style={styles.previewLabel}>{t('player.est_proceeds')}</Text><Text style={styles.previewValue} testID="trade-est-proceeds">{quote ? `€${formatCredits(quote.sell_proceeds)}` : '—'}</Text></View>
              </View>
              {soldOut && <Text style={styles.soldBanner} testID="trade-soldout">Esaurito sul mercato finché qualcuno non vende — l'acquisto è bloccato, la vendita resta possibile.</Text>}
              {!!tradeError && <Text style={styles.feedbackErr} testID="trade-error">{tradeError}</Text>}
              {!!tradeOk && <Text style={styles.feedbackOk} testID="trade-success">{tradeOk}</Text>}
              <View style={styles.actionRow}>
                <Pressable testID="trade-buy" disabled={qtyNum < 1 || submitting != null || soldOut} onPress={() => onTrade('buy')}
                  style={({ pressed }) => [styles.actionBtn, styles.buyBtn, (pressed || submitting === 'buy') && styles.btnPressed, (qtyNum < 1 || submitting != null || soldOut) && styles.btnDisabled]}>
                  {submitting === 'buy' ? <ActivityIndicator color={colors.onAccent} size="small" /> : <Text style={styles.actionText}>{t('player.buy')}</Text>}
                </Pressable>
                <Pressable testID="trade-sell" disabled={qtyNum < 1 || owned < 1 || submitting != null} onPress={() => onTrade('sell')}
                  style={({ pressed }) => [styles.actionBtn, styles.sellBtn, (pressed || submitting === 'sell') && styles.btnPressed, (qtyNum < 1 || owned < 1 || submitting != null) && styles.btnDisabled]}>
                  {submitting === 'sell' ? <ActivityIndicator color={colors.onAccent} size="small" /> : <Text style={styles.actionText}>{t('player.sell')}</Text>}
                </Pressable>
              </View>
            </View>

            <Text style={styles.disclaimer}>{t('disclaimer.long')}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function TradeStat({ label, value, styles }: { label: string; value: string; styles: ReturnType<typeof makeStyles> }) {
  return (
    <View style={styles.tradeStat}><Text style={styles.tradeStatLabel}>{label}</Text><Text style={styles.tradeStatValue}>{value}</Text></View>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  headerBar: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  backBtn: { flexDirection: 'row', alignItems: 'center', padding: spacing.sm, alignSelf: 'flex-start' },
  backText: { ...typography.body, color: colors.text, marginLeft: 2 },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  hero: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.md, overflow: 'hidden' },
  roleBar: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 4 },
  avatar: { width: 56, height: 56, borderRadius: 28, justifyContent: 'center', alignItems: 'center', marginLeft: 4 },
  avatarText: { color: '#FFF', fontSize: 24, fontWeight: '700', fontFamily: typography.bodyBold.fontFamily },
  name: { ...typography.h3, color: colors.text },
  meta: { ...typography.small, color: colors.muted, marginTop: 2 },
  priceHead: { alignItems: 'flex-start' },
  priceBig: { ...typography.mono, fontSize: 34, fontWeight: '700', color: colors.amber },
  priceVar: { ...typography.monoLabel, marginTop: 2 },
  chartCard: { backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.md, alignItems: 'center', gap: spacing.sm },
  periodRow: { flexDirection: 'row', gap: spacing.sm, alignSelf: 'flex-start' },
  periodBtn: { paddingHorizontal: spacing.md, height: 30, justifyContent: 'center', borderRadius: radius.pill, borderWidth: borderW, borderColor: colors.border, backgroundColor: colors.surfaceAlt },
  periodText: { ...typography.monoLabel },
  chartEmpty: { height: 120, justifyContent: 'center' },
  chartEmptyTxt: { ...typography.small, color: colors.muted },
  tilesRow: { flexDirection: 'row', gap: spacing.md },
  card: { backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.md },
  cardLabel: { ...typography.caption, color: colors.muted, marginBottom: spacing.sm },
  scost: { ...typography.mono, fontSize: 22, fontWeight: '700' },
  cardHint: { ...typography.small, color: colors.muted, marginTop: 2 },
  tradeCard: { backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.md },
  tradeTitle: { ...typography.h3, color: colors.text, marginBottom: spacing.md },
  tradeInfoRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  tradeStat: { flex: 1 },
  tradeStatLabel: { ...typography.caption, color: colors.muted },
  tradeStatValue: { ...typography.bodyBold, color: colors.text, marginTop: 2, fontVariant: ['tabular-nums'] },
  qtyLabel: { ...typography.caption, color: colors.muted, marginBottom: spacing.xs },
  qtyRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.md },
  stepBtn: { width: 44, height: 44, borderRadius: radius.md, backgroundColor: colors.bg, borderWidth: borderW, borderColor: colors.border, justifyContent: 'center', alignItems: 'center' },
  qtyInput: { flex: 1, height: 44, backgroundColor: colors.bg, borderWidth: borderW, borderColor: colors.border, borderRadius: radius.md, textAlign: 'center', ...typography.bodyBold, color: colors.text, fontVariant: ['tabular-nums'] },
  previewBox: { backgroundColor: colors.bg, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderWidth: borderW, borderColor: colors.border, marginBottom: spacing.md },
  previewRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  previewLabel: { ...typography.small, color: colors.muted },
  previewValue: { ...typography.bodyBold, color: colors.text, fontVariant: ['tabular-nums'] },
  soldBanner: { ...typography.small, color: colors.red, marginBottom: spacing.sm, backgroundColor: colors.red + '14', borderWidth: borderW, borderColor: colors.red, borderRadius: radius.md, padding: spacing.sm },
  feedbackErr: { ...typography.small, color: colors.red, marginBottom: spacing.sm },
  feedbackOk: { ...typography.small, color: colors.green, marginBottom: spacing.sm },
  actionRow: { flexDirection: 'row', gap: spacing.md },
  actionBtn: { flex: 1, height: 50, borderRadius: radius.md, justifyContent: 'center', alignItems: 'center' },
  buyBtn: { backgroundColor: colors.cyan },
  sellBtn: { backgroundColor: colors.red },
  btnPressed: { opacity: 0.8 },
  btnDisabled: { opacity: 0.4 },
  actionText: { ...typography.bodyBold, color: colors.onAccent },
  disclaimer: { ...typography.caption, color: colors.muted, marginTop: spacing.md, textAlign: 'center' },
  error: { color: colors.red, padding: spacing.lg, textAlign: 'center' },
});
