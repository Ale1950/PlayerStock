import { useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { BentoCard } from '@/src/components/BentoCard';
import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { NewsThumb } from '@/src/components/NewsThumb';
import { Sparkline } from '@/src/components/Sparkline';
import { NEWS_PLACEHOLDER } from '@/src/content/newsPlaceholder';
import { useResponsive } from '@/src/hooks/use-responsive';
import {
  getLeaderboard, getPortfolio, getPriceHistory,
  type LeaderboardResponse, type PortfolioResponse,
} from '@/src/services/portfolio.service';
import { getMarketOverview, type MarketOverview } from '@/src/services/stats.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { type ThemeColors } from '@/src/theme/tokens';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { formatInt } from '@/src/utils/formatters';

const compact = (n: number) => n >= 1e9 ? `${(n / 1e9).toFixed(1)}B` : n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}K` : `${Math.round(n)}`;

export default function Home() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useTheme();
  const { isDesktop } = useResponsive();
  const styles = useMemo(() => makeStyles(colors), [colors]);

  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [rank, setRank] = useState<LeaderboardResponse | null>(null);
  const [market, setMarket] = useState<MarketOverview | null>(null);
  const [talentSpark, setTalentSpark] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getPortfolio().then((d) => active && setPortfolio(d)).catch(() => {});
    getLeaderboard(50).then((d) => active && setRank(d)).catch(() => {});
    getMarketOverview().then(async (d) => {
      if (!active) return;
      setMarket(d);
      const tal = d.top_gainers?.[0];
      if (tal) {
        try { const h = await getPriceHistory(tal.athlete_id, 14); if (active) setTalentSpark(h.points.map((p) => p.price)); } catch {}
      }
    }).catch(() => {}).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const talent = market?.top_gainers?.[0] ?? null;
  const fallback = () => <Text style={styles.fallback}>{loading ? '…' : '—'}</Text>;

  // ── moduli ──────────────────────────────────────────────────────────────
  const MatchDayHero = (
    <BentoCard testID="home-matchday">
      <View style={styles.soonRow}>
        <View style={styles.soonPill}><Text style={styles.soonTxt}>{t('home.matchday_soon')}</Text></View>
      </View>
      <Text style={styles.heroTitle}>{t('home.matchday_title')}</Text>
      <Text style={styles.heroSub}>{t('home.matchday_subtitle')}</Text>
    </BentoCard>
  );

  const PortfolioMini = (
    <BentoCard
      title={t('home.portfolio')} action={t('home.open')}
      onAction={() => router.push('/(tabs)/portfolio')}
      testID="home-portfolio" style={isDesktop ? { flex: 1 } : undefined}
    >
      {portfolio ? (() => {
        const tot = portfolio.totals; const up = (tot.total_pnl_abs ?? 0) >= 0;
        const c = up ? colors.up : colors.down; const sign = up ? '+' : '−';
        return (
          <>
            <Text style={styles.bigNum}>€{formatInt(tot.total_equity)}</Text>
            <Text style={[styles.delta, { color: c }]}>
              {sign}{Math.abs(tot.total_pnl_pct ?? 0).toFixed(2)}% · {sign}€{formatInt(Math.abs(tot.total_pnl_abs ?? 0))}
            </Text>
          </>
        );
      })() : fallback()}
    </BentoCard>
  );

  const RankMini = (
    <BentoCard
      title={t('home.position')} action={t('home.leaderboard')}
      onAction={() => router.push('/(tabs)/leaderboard')}
      testID="home-rank" style={isDesktop ? { flex: 1 } : undefined}
    >
      {rank?.self ? (
        <>
          <Text style={styles.bigNum}>#{rank.self.rank}</Text>
          <Text style={styles.subMuted}>{t('home.of')} {rank.total_users}</Text>
        </>
      ) : fallback()}
    </BentoCard>
  );

  const MarketMini = (
    <BentoCard
      title={t('home.market')} action={t('home.see_all')}
      onAction={() => router.push('/(tabs)/market')} testID="home-market"
    >
      {market ? (
        <>
          <View style={styles.statRow}>
            <View style={styles.stat}><Text style={styles.statVal}>€{compact(market.total_market_cap)}</Text><Text style={styles.statLbl}>CAP</Text></View>
            <View style={styles.stat}><Text style={styles.statVal}>{compact(market.volume_24h)}</Text><Text style={styles.statLbl}>VOL 24H</Text></View>
            <View style={styles.stat}><Text style={styles.statVal}>{market.active_count}</Text><Text style={styles.statLbl}>ATTIVI</Text></View>
          </View>
          {market.top_gainers.slice(0, 3).map((m, i, arr) => {
            const up = (m.var_pct ?? 0) >= 0;
            return (
              <Pressable
                key={m.athlete_id} onPress={() => router.push(`/player/${m.athlete_id}`)}
                style={[styles.moverRow, i < arr.length - 1 && styles.moverBorder]}
              >
                <Text style={styles.moverName} numberOfLines={1}>{m.display_label ?? '—'}</Text>
                <Text style={[styles.delta, { color: up ? colors.up : colors.down }]}>{up ? '+' : ''}{(m.var_pct ?? 0).toFixed(1)}%</Text>
              </Pressable>
            );
          })}
        </>
      ) : fallback()}
    </BentoCard>
  );

  const TalentCard = (
    <BentoCard
      title={t('home.talent')} action={t('home.detail')}
      onAction={() => talent && router.push(`/player/${talent.athlete_id}`)} testID="home-talent"
    >
      {talent ? (
        <View style={styles.talentRow}>
          <View style={{ flex: 1, gap: 2 }}>
            <Text style={styles.talentName} numberOfLines={1}>{talent.display_label ?? '—'}</Text>
            <Text style={[styles.delta, { color: colors.up }]}>{(talent.var_pct ?? 0) >= 0 ? '+' : ''}{(talent.var_pct ?? 0).toFixed(1)}%</Text>
            <Text style={styles.subMuted}>{t('home.talent_hint')}</Text>
          </View>
          {talentSpark.length > 1 && <Sparkline prices={talentSpark} positive width={76} height={34} />}
        </View>
      ) : fallback()}
    </BentoCard>
  );

  const NewsColumn = (
    <BentoCard title={t('home.news_title')} testID="home-news">
      <View style={styles.previewPill}><Text style={styles.soonTxt}>{t('home.news_preview')}</Text></View>
      {NEWS_PLACEHOLDER.map((n, i, arr) => (
        <Pressable
          key={i} onPress={() => Linking.openURL(n.url)}
          style={[styles.newsRow, i < arr.length - 1 && styles.moverBorder]}
        >
          <NewsThumb icon={n.icon} index={i} />
          <View style={styles.newsText}>
            <Text style={styles.newsSource}>{n.source}</Text>
            <Text style={styles.newsTitle}>{n.title}</Text>
          </View>
        </Pressable>
      ))}
    </BentoCard>
  );

  return (
    <View style={styles.safe}>
      <GeometricBackground />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('home.dashboard_title')}</Text>
        <View style={[styles.cols, isDesktop && styles.colsRow]}>
          <View style={[styles.main, isDesktop && { flex: 2 }]}>
            {MatchDayHero}
            <View style={[styles.pair, isDesktop && styles.pairRow]}>
              {PortfolioMini}
              {RankMini}
            </View>
            {MarketMini}
            {TalentCard}
          </View>
          <View style={[styles.newsCol, isDesktop && { flex: 1 }]}>
            {NewsColumn}
          </View>
        </View>
        <Text style={styles.disclaimer} testID="home-disclaimer">{t('disclaimer.short')}</Text>
      </ScrollView>
    </View>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 40, gap: spacing.md, maxWidth: 1200, width: '100%', alignSelf: 'center' },
  title: { ...typography.pageTitle, color: colors.text },
  cols: { gap: spacing.md },
  colsRow: { flexDirection: 'row', alignItems: 'flex-start' },
  main: { gap: spacing.md },
  newsCol: {},
  pair: { gap: spacing.md },
  pairRow: { flexDirection: 'row' },
  // hero match day
  soonRow: { flexDirection: 'row' },
  soonPill: { backgroundColor: colors.surfaceAlt, borderRadius: radius.pill, paddingHorizontal: 10, paddingVertical: 3, borderWidth: borderW, borderColor: colors.border },
  soonTxt: { ...typography.monoLabel, fontSize: 9, color: colors.muted },
  heroTitle: { ...typography.h2, color: colors.text },
  heroSub: { ...typography.small, color: colors.muted },
  // metriche
  bigNum: { ...typography.mono, fontSize: 26, fontWeight: '700', color: colors.text },
  delta: { ...typography.monoLabel, letterSpacing: 0.5 },
  subMuted: { ...typography.small, color: colors.muted },
  fallback: { ...typography.mono, fontSize: 22, color: colors.muted },
  // mercato mini
  statRow: { flexDirection: 'row', gap: spacing.md },
  stat: { flex: 1 },
  statVal: { ...typography.mono, fontWeight: '700', color: colors.text },
  statLbl: { ...typography.caption, color: colors.muted },
  moverRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 8 },
  moverBorder: { borderBottomWidth: 1, borderBottomColor: colors.border },
  moverName: { ...typography.body, color: colors.text, flex: 1, marginRight: spacing.sm },
  // talento
  talentRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  talentName: { ...typography.bodyBold, color: colors.text },
  // news
  previewPill: { alignSelf: 'flex-start', backgroundColor: colors.surfaceAlt, borderRadius: radius.pill, paddingHorizontal: 10, paddingVertical: 3, borderWidth: borderW, borderColor: colors.border },
  newsRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: 10 },
  newsText: { flex: 1, gap: 2 },
  newsSource: { ...typography.monoLabel, fontSize: 10, color: colors.accent },
  newsTitle: { ...typography.body, color: colors.text },
  disclaimer: { ...typography.caption, color: colors.muted, textAlign: 'center', marginTop: spacing.md },
});
