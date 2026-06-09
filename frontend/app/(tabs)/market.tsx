import { useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { ResponsiveTable, type Column, type SortState } from '@/src/components/ResponsiveTable';
import { Sparkline } from '@/src/components/Sparkline';
import { StateView } from '@/src/components/StateView';
import { StatTile } from '@/src/components/StatTile';
import { TeamBadge } from '@/src/components/TeamBadge';
import { useResponsive } from '@/src/hooks/use-responsive';
import { translateError } from '@/src/services/api';
import { listPlayers, listTeams, type AthletePublic, type TeamPublic } from '@/src/services/players.service';
import { getPriceHistory } from '@/src/services/portfolio.service';
import { getMarketOverview, type MarketOverview } from '@/src/services/stats.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { gradients, type ThemeColors } from '@/src/theme/tokens';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { flagEmoji } from '@/src/utils/flags';
import { formatEuroM, formatPrice } from '@/src/utils/formatters';

const ROLES = ['all', 'POR', 'DIF', 'CC', 'ATT'] as const;
const roleTint = (c: ThemeColors, r: string) => r === 'ATT' ? c.red : r === 'CC' ? c.purple : r === 'DIF' ? c.cyan : c.chartBlue;
const compact = (n: number) => n >= 1e9 ? `${(n / 1e9).toFixed(1)}B` : n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}K` : `${Math.round(n)}`;
const lastName = (p: AthletePublic) => p.display_lastname || p.display_label;
const dispOf = (p: AthletePublic) => p.primary_pool_qty ?? p.float_quote;
// Valore di mercato €M (Fase 2c): segue il prezzo via àncora del seed (lato backend).
const valoreOf = (p: AthletePublic) => p.market_value_eur ?? 0;
const possPct = (p: AthletePublic) => p.float_quote ? (p.float_quote - dispOf(p)) / p.float_quote * 100 : 0;
const isSoldOut = (p: AthletePublic) => dispOf(p) <= 0;
const miniStat = (p: AthletePublic) => {
  const w = p.weekly_stats; if (!w) return '—';
  return p.role === 'POR' ? `${w.parate ?? 0} parate` : `${w.gol}G · ${w.assist}A`;
};

export default function Market() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useTheme();
  const { isDesktop } = useResponsive();
  const styles = useMemo(() => makeStyles(colors), [colors]);

  const [players, setPlayers] = useState<AthletePublic[]>([]);
  const [teams, setTeams] = useState<TeamPublic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [market, setMarket] = useState<MarketOverview | null>(null);
  const [sparks, setSparks] = useState<Record<string, number[]>>({});

  const [role, setRole] = useState<typeof ROLES[number]>('all');
  const [teamId, setTeamId] = useState<string | null>(null);
  const [nat, setNat] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortState>({ key: 'prezzo', dir: 'desc' });

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await listPlayers({ role: role === 'all' ? undefined : role, team_id: teamId ?? undefined, page: 1, page_size: 120 });
      setPlayers(data.items);
      const tasks = data.items.slice(0, 24).map(async (p): Promise<[string, number[]]> => {
        try { const h = await getPriceHistory(p._id, 14); return [p._id, h.points.map((x) => x.price)]; } catch { return [p._id, []]; }
      });
      const res = await Promise.all(tasks);
      setSparks((prev) => { const m = { ...prev }; res.forEach(([id, arr]) => { m[id] = arr; }); return m; });
    } catch (e) { setError(translateError(e)); }
    finally { setLoading(false); }
  }, [role, teamId]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    getMarketOverview().then(setMarket).catch(() => setMarket(null));
    listTeams().then(setTeams).catch(() => setTeams([]));
  }, []);

  const varOf = useCallback((id: string): number | null => {
    const s = sparks[id]; return s && s.length >= 2 ? (s[s.length - 1] / s[0] - 1) * 100 : null;
  }, [sparks]);

  const nationalities = useMemo(() => Array.from(new Set(players.map((p) => p.nationality_iso3))).sort(), [players]);

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    let r = players.filter((p) => {
      if (nat && p.nationality_iso3 !== nat) return false;
      if (!q) return true;
      return [p.display_label, lastName(p), p.team_fantasy_name, p.nationality_iso3]
        .some((f) => (f ?? '').toLowerCase().includes(q));
    });
    if (sort) {
      const dir = sort.dir === 'asc' ? 1 : -1;
      const val = (p: AthletePublic): string | number => {
        switch (sort.key) {
          case 'cognome': return lastName(p).toLowerCase();
          case 'squadra': return (p.team_fantasy_name ?? '').toLowerCase();
          case 'nazione': return p.nationality_iso3;
          case 'prezzo': return p.prezzo_corrente_eur;
          case 'valore': return valoreOf(p);
          case 'disp': return dispOf(p);
          case 'var': return varOf(p._id) ?? -Infinity;
          default: return 0;
        }
      };
      r = [...r].sort((a, b) => { const va = val(a), vb = val(b); return va < vb ? -dir : va > vb ? dir : 0; });
    }
    return r;
  }, [players, search, nat, sort, varOf]);

  const onSort = (key: string) => setSort((s) => s?.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' });
  const biggest = market?.top_gainers?.[0];

  const PriceCell = (p: AthletePublic) => {
    const v = varOf(p._id); const up = (v ?? 0) >= 0;
    return (
      <View style={{ alignItems: 'flex-end' }}>
        <Text style={styles.price}>€{formatPrice(p.prezzo_corrente_eur)}</Text>
        {v != null && <Text style={[styles.var, { color: up ? colors.green : colors.red }]}>{up ? '+' : ''}{v.toFixed(1)}%</Text>}
      </View>
    );
  };

  const columns: Column<AthletePublic>[] = [
    { key: 'cognome', label: 'COGNOME', flex: 1.4, sortable: true, render: (p) => (
      <View>
        <Text style={styles.cName} numberOfLines={1}>{p.display_label}</Text>
        <Text style={styles.cMeta}>{p.role} · {p.age ?? '?'}</Text>
      </View>) },
    { key: 'squadra', label: 'SQUADRA', flex: 1.3, sortable: true, render: (p) => (
      <View style={styles.teamCell}>
        <TeamBadge primary={p.team_color_primary} secondary={p.team_color_secondary} name={p.team_fantasy_name} size={24} />
        <Text style={styles.cMeta} numberOfLines={1}>{p.team_fantasy_name}</Text>
      </View>) },
    { key: 'nazione', label: 'NAZ', width: 56, sortable: true, render: (p) => (
      <Text style={styles.flag}>{flagEmoji(p.nationality_iso3)} <Text style={styles.cMeta}>{p.nationality_iso3}</Text></Text>) },
    { key: 'var', label: 'PREZZO / VAR', width: 100, align: 'right', sortable: true, render: PriceCell },
    { key: 'valore', label: 'VAL. MERCATO', width: 100, align: 'right', sortable: true, render: (p) => <Text style={styles.num} testID={`market-value-${p._id}`}>{formatEuroM(p.market_value_eur)}</Text> },
    { key: 'disp', label: 'DISPONIBILI', width: 110, align: 'right', sortable: true, render: (p) => (
      isSoldOut(p)
        ? <View style={styles.soldTag}><Text style={styles.soldTxt}>ESAURITO</Text></View>
        : <View style={{ alignItems: 'flex-end' }}>
            <Text style={styles.num}>{compact(dispOf(p))}</Text>
            <Text style={styles.cMeta}>{possPct(p).toFixed(1)}% poss.</Text>
          </View>) },
    { key: 'spark', label: 'TREND', width: 64, render: (p) => {
      const s = sparks[p._id]; return s && s.length > 1 ? <Sparkline prices={s} positive={(varOf(p._id) ?? 0) >= 0} width={56} height={22} /> : <Text style={styles.cMeta}>—</Text>; } },
    { key: 'stats', label: 'STAGIONE', width: 96, align: 'right', render: (p) => <Text style={styles.statTxt}>{miniStat(p)}</Text> },
  ];

  const Card = (p: AthletePublic) => {
    const v = varOf(p._id); const up = (v ?? 0) >= 0; const s = sparks[p._id];
    return (
      <Pressable onPress={() => router.push(`/player/${p._id}`)} testID={`player-row-${p._id}`} style={({ pressed }) => [styles.card, pressed && { opacity: 0.7 }]}>
        <TeamBadge primary={p.team_color_primary} secondary={p.team_color_secondary} name={p.team_fantasy_name} size={40} />
        <View style={styles.cardMain}>
          <Text style={styles.cardName} numberOfLines={1}>{p.display_label}</Text>
          <Text style={styles.cMeta} numberOfLines={1}>{flagEmoji(p.nationality_iso3)} {p.role} · {p.team_fantasy_name}</Text>
          <Text style={styles.statTxt} numberOfLines={2}>
            {miniStat(p)} · Val. {formatEuroM(p.market_value_eur)}{isSoldOut(p) ? '' : ` · ${compact(dispOf(p))} disp (${possPct(p).toFixed(0)}%)`}
          </Text>
        </View>
        {s && s.length > 1 && <Sparkline prices={s} positive={up} width={52} height={24} />}
        <View style={{ alignItems: 'flex-end', minWidth: 66 }}>
          <Text style={styles.price}>€{formatPrice(p.prezzo_corrente_eur)}</Text>
          {isSoldOut(p)
            ? <View style={styles.soldTag}><Text style={styles.soldTxt}>ESAURITO</Text></View>
            : (v != null && <Text style={[styles.var, { color: up ? colors.green : colors.red }]}>{up ? '+' : ''}{v.toFixed(1)}%</Text>)}
        </View>
      </Pressable>
    );
  };

  return (
    <View style={styles.safe}>
      <GeometricBackground />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('home.title')}</Text>

        {market && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.moversRow}>
            {[...market.top_gainers.slice(0, 3), ...market.top_losers.slice(0, 3)].map((m) => {
              const up = (m.var_pct ?? 0) >= 0;
              return (
                <View key={m.athlete_id} style={[styles.moverChip, { borderColor: up ? colors.green : colors.red }]}>
                  <Text style={styles.moverName} numberOfLines={1}>{m.display_label ?? '—'}</Text>
                  <Text style={[typography.monoLabel, { color: up ? colors.green : colors.red }]}>{up ? '+' : ''}{(m.var_pct ?? 0).toFixed(1)}%</Text>
                </View>
              );
            })}
          </ScrollView>
        )}

        {market && (
          <View style={[styles.tilesWrap, isDesktop && { flexWrap: 'nowrap' }]}>
            <StatTile icon="server-outline" value={`€${compact(market.total_market_cap)}`} label="CAP TOTALE" tint={colors.amber} gradient={gradients.amber} />
            <StatTile icon="swap-horizontal-outline" value={compact(market.volume_24h)} label="VOLUME 24H" sub="quote" tint={colors.cyan} gradient={gradients.cyanTeal} />
            <StatTile icon="pulse-outline" value={`${market.active_count}`} label="ATTIVI" tint={colors.teal} gradient={gradients.cyanTeal} />
            <StatTile icon="trending-up-outline" value={biggest ? `${(biggest.var_pct ?? 0) >= 0 ? '+' : ''}${(biggest.var_pct ?? 0).toFixed(1)}%` : '—'} label="MOV. MAX" sub={biggest?.display_label ?? undefined} tint={colors.purple} gradient={gradients.purple} />
          </View>
        )}

        <TextInput
          testID="home-search-input"
          placeholder="Cerca cognome / squadra / nazione…"
          placeholderTextColor={colors.muted}
          style={styles.search}
          value={search}
          onChangeText={setSearch}
          returnKeyType="search"
        />

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsRow}>
          {ROLES.map((r) => (
            <Pressable key={r} testID={`home-filter-${r.toLowerCase()}`} onPress={() => setRole(r)} style={[styles.chip, role === r && styles.chipActive]}>
              <Text style={[styles.chipText, role === r && styles.chipTextActive]}>{r === 'all' ? 'TUTTI' : r}</Text>
            </Pressable>
          ))}
          <View style={styles.sep} />
          {nationalities.slice(0, 12).map((n) => (
            <Pressable key={n} onPress={() => setNat(nat === n ? null : n)} style={[styles.chip, nat === n && styles.chipActive]}>
              <Text style={[styles.chipText, nat === n && styles.chipTextActive]}>{flagEmoji(n)} {n}</Text>
            </Pressable>
          ))}
        </ScrollView>

        {teams.length > 0 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsRow}>
            <Pressable onPress={() => setTeamId(null)} style={[styles.chip, !teamId && styles.chipActive]}>
              <Text style={[styles.chipText, !teamId && styles.chipTextActive]}>OGNI SQUADRA</Text>
            </Pressable>
            {teams.map((tm) => (
              <Pressable key={tm._id} onPress={() => setTeamId(teamId === tm._id ? null : tm._id)} style={[styles.teamChip, { borderColor: teamId === tm._id ? colors.cyan : colors.border }]}>
                <TeamBadge primary={tm.color_primary} secondary={tm.color_secondary} name={tm.fantasy_name} size={20} />
                <Text style={[styles.chipText, { color: teamId === tm._id ? colors.cyan : colors.muted }]} numberOfLines={1}>{tm.fantasy_name}</Text>
              </Pressable>
            ))}
          </ScrollView>
        )}

        {loading || error || rows.length === 0 ? (
          <StateView loading={loading} error={error} empty={!loading && !error && rows.length === 0} emptyLabel={t('home.empty')} icon="podium-outline" />
        ) : (
          <ResponsiveTable
            data={rows}
            columns={columns}
            renderCard={Card}
            keyExtractor={(p) => p._id}
            sort={sort}
            onSort={onSort}
            onRowPress={(p) => router.push(`/player/${p._id}`)}
          />
        )}
        <Text style={styles.disclaimerText} testID="home-disclaimer">{t('disclaimer.short')}</Text>
      </ScrollView>
    </View>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 40, gap: spacing.md, maxWidth: 1100, width: '100%', alignSelf: 'center' },
  title: { ...typography.pageTitle, color: colors.text },
  moversRow: { gap: spacing.sm },
  moverChip: { paddingHorizontal: spacing.md, paddingVertical: 6, borderRadius: radius.pill, borderWidth: borderW, backgroundColor: colors.surface, maxWidth: 150 },
  moverName: { ...typography.small, color: colors.text },
  tilesWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  search: { backgroundColor: colors.surface, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: 10, color: colors.text, borderWidth: borderW, borderColor: colors.border, fontFamily: typography.body.fontFamily, fontSize: 14 },
  chipsRow: { gap: spacing.sm, alignItems: 'center', paddingVertical: 2 },
  sep: { width: 1, height: 24, backgroundColor: colors.border, marginHorizontal: 4 },
  chip: { paddingHorizontal: spacing.md, height: 32, justifyContent: 'center', alignItems: 'center', borderRadius: radius.pill, backgroundColor: colors.surface, borderWidth: borderW, borderColor: colors.border },
  chipActive: { backgroundColor: colors.cyan, borderColor: colors.cyan },
  chipText: { ...typography.monoLabel, color: colors.muted },
  chipTextActive: { color: colors.onAccent },
  teamChip: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: spacing.sm, height: 32, borderRadius: radius.pill, backgroundColor: colors.surface, borderWidth: borderW, maxWidth: 170 },
  // cells
  cName: { ...typography.bodyBold, color: colors.text },
  cMeta: { ...typography.small, color: colors.muted },
  teamCell: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  flag: { fontSize: 16 },
  price: { ...typography.mono, color: colors.amber, fontWeight: '700' },
  var: { ...typography.monoLabel, marginTop: 1 },
  num: { ...typography.mono, color: colors.text, fontWeight: '700' },
  statTxt: { ...typography.mono, fontSize: 12, color: colors.muted },
  soldTag: { alignSelf: 'flex-end', borderWidth: borderW, borderColor: colors.red, borderRadius: radius.sm, paddingHorizontal: 6, paddingVertical: 2 },
  soldTxt: { ...typography.monoLabel, fontSize: 9, color: colors.red },
  // mobile card
  card: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.md },
  cardMain: { flex: 1, minWidth: 0, gap: 1 },
  cardName: { ...typography.bodyBold, color: colors.text },
  disclaimerText: { ...typography.caption, color: colors.muted, textAlign: 'center', marginTop: spacing.md },
});
