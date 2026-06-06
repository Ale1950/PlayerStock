import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { StateView } from '@/src/components/StateView';
import { VividCard, VividText } from '@/src/components/VividCard';
import { useResponsive } from '@/src/hooks/use-responsive';
import { translateError } from '@/src/services/api';
import {
  claimMission, claimStreak, getOverview, submitQuiz,
  type EngagementOverview, type MissionItem,
} from '@/src/services/engagement.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { type ThemeColors } from '@/src/theme/tokens';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';

const INK = '#05070A';
type Key = 'streak' | 'quiz' | 'predictions' | 'challenge' | 'missions' | 'news';
type Variant = 'cyan' | 'teal' | 'purple' | 'green' | 'amber' | 'pink';

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.max(0.03, Math.min(1, max ? value / max : 0));
  return <View style={pstyles.track}><View style={[pstyles.fill, { width: `${pct * 100}%`, backgroundColor: color }]} /></View>;
}

export default function Engage() {
  const { colors } = useTheme();
  const { isDesktop } = useResponsive();
  const s = useMemo(() => makeStyles(colors), [colors]);

  const [ov, setOv] = useState<EngagementOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<Key | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try { setOv(await getOverview()); } catch (e) { setError(translateError(e)); }
    finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { setLoading(true); load(); }, [load]));

  const onClaimStreak = async () => {
    setBusy('streak');
    try { const r = await claimStreak(); if (r.claimed) setToast(`+${r.reward_amount?.toFixed(1)} NACKL · streak ${r.current_streak}`); await load(); } finally { setBusy(null); }
  };
  const onSubmitQuiz = async () => {
    if (!ov) return; setBusy('quiz');
    try {
      const ans = ov.market_quiz.questions.map((q) => answers[q.id] ?? 0);
      const r = await submitQuiz(ov.market_quiz.id, ans);
      setToast(`Quiz ${r.correct}/${r.total} · +${r.reward_amount.toFixed(1)} NACKL + €`); setOpen(null); await load();
    } catch (e) { setToast(translateError(e)); } finally { setBusy(null); }
  };
  const onClaimMission = async (m: MissionItem) => {
    setBusy(m.id);
    try { const r = await claimMission(m.id); if (r.claimed) setToast(`Missione: +€${r.credits} + ${r.nackl} NACKL`); await load(); }
    catch (e) { setToast(translateError(e)); } finally { setBusy(null); }
  };

  // 6 colori DISTINTI; disposti così che card adiacenti (orizz. E vert.) siano sempre diverse:
  //   riga1 cyan|purple · riga2 green|amber · riga3 pink|teal
  const launchers: { key: Key; variant: Variant; icon: keyof typeof Ionicons.glyphMap; title: string; teaser: string }[] = ov ? [
    { key: 'streak', variant: 'cyan', icon: 'flame', title: 'Streak', teaser: `${ov.streak.current_streak} giorni 🔥${ov.streak.can_claim_today ? ' · riscatta' : ''}` },
    { key: 'quiz', variant: 'purple', icon: 'help-circle', title: 'Quiz Mercato', teaser: ov.market_quiz.already_attempted ? '✓ completato oggi' : `${ov.market_quiz.questions.length} domande` },
    { key: 'predictions', variant: 'green', icon: 'trending-up', title: 'Pronostici', teaser: `${ov.predictions.open} aperti` },
    { key: 'challenge', variant: 'amber', icon: 'trophy', title: 'Sfida', teaser: ov.challenge.my_rank ? `Tu #${ov.challenge.my_rank} / ${ov.challenge.total}` : '—' },
    { key: 'missions', variant: 'pink', icon: 'flag', title: 'Missioni', teaser: `${ov.missions.filter((m) => m.completed).length}/${ov.missions.length} completate` },
    { key: 'news', variant: 'teal', icon: 'newspaper', title: 'News', teaser: `${ov.news.items.length} eventi di mercato` },
  ] : [];

  const toneColor = (t: string) => t === 'green' ? colors.green : t === 'red' ? colors.red : t === 'amber' ? colors.amber : colors.cyan;

  return (
    <View style={s.safe}>
      <GeometricBackground />
      <ScrollView contentContainerStyle={s.container}>
        <Text style={s.title}>Engage</Text>
        <Text style={s.subtitle}>Premi su DUE economie: <Text style={{ color: colors.amber }}>€</Text> (gioco) e <Text style={{ color: colors.cyan }}>NACKL</Text> (placeholder) — distinte. Tocca un'attività per aprirla.</Text>
        {!!toast && <View style={s.toast}><Text style={s.toastTxt}>{toast}</Text></View>}

        {loading || error || !ov ? (
          <StateView loading={loading} error={error} empty={!loading && !error && !ov} emptyLabel="—" icon="flame-outline" />
        ) : (
          <View style={[s.grid, isDesktop && s.gridDesktop]}>
            {launchers.map((l) => (
              <Pressable key={l.key} testID={`launcher-${l.key}`} onPress={() => { setOpen(l.key); setAnswers({}); }} style={[s.cellBase, isDesktop ? s.cellDesktop : s.cellMobile]}>
                <VividCard variant={l.variant} style={s.launcher}>
                  <View style={s.launcherRow}>
                    <Ionicons name={l.icon} size={26} color={INK} />
                    <Ionicons name="chevron-forward" size={20} color={INK} style={{ opacity: 0.7 }} />
                  </View>
                  <VividText size="title">{l.title}</VividText>
                  <VividText size="body">{l.teaser}</VividText>
                </VividCard>
              </Pressable>
            ))}
          </View>
        )}
      </ScrollView>

      {/* PANNELLO DEDICATO (modale desktop · schermo mobile) */}
      <Modal visible={open != null} transparent animationType="fade" onRequestClose={() => setOpen(null)}>
        <Pressable style={s.backdrop} onPress={() => setOpen(null)}>
          <Pressable style={[s.panel, isDesktop ? s.panelDesktop : s.panelMobile]} onPress={(e) => e.stopPropagation?.()}>
            <View style={s.panelHead}>
              <Text style={s.panelTitle}>{launchers.find((l) => l.key === open)?.title}</Text>
              <Pressable onPress={() => setOpen(null)} hitSlop={8}><Ionicons name="close" size={24} color={colors.muted} /></Pressable>
            </View>
            <ScrollView contentContainerStyle={{ gap: spacing.md, paddingBottom: spacing.md }}>
              {ov && open === 'streak' && (
                <>
                  <Text style={s.big}>{ov.streak.current_streak} giorni 🔥</Text>
                  <Text style={s.pMeta}>Record {ov.streak.longest_streak} · prossimo +{ov.streak.next_reward_estimate?.toFixed(1)} NACKL</Text>
                  <Pressable disabled={!ov.streak.can_claim_today || busy === 'streak'} onPress={onClaimStreak} style={[s.cta, !ov.streak.can_claim_today && s.ctaOff]}>
                    <Text style={s.ctaTxt}>{ov.streak.can_claim_today ? 'RISCATTA OGGI' : 'GIÀ RISCATTATO'}</Text>
                  </Pressable>
                </>
              )}
              {ov && open === 'quiz' && (ov.market_quiz.already_attempted ? (
                <Text style={s.pMeta}>✓ Completato oggi — torna domani per un nuovo quiz dai dati di mercato.</Text>
              ) : (
                <>
                  {ov.market_quiz.questions.map((q) => (
                    <View key={q.id}>
                      <Text style={s.qTxt}>{q.text}</Text>
                      <View style={s.opts}>
                        {q.options.map((o, oi) => (
                          <Pressable key={oi} onPress={() => setAnswers((a) => ({ ...a, [q.id]: oi }))} style={[s.opt, answers[q.id] === oi && { backgroundColor: colors.cyan, borderColor: colors.cyan }]}>
                            <Text style={[s.optTxt, answers[q.id] === oi && { color: colors.onAccent }]}>{o}</Text>
                          </Pressable>
                        ))}
                      </View>
                    </View>
                  ))}
                  <Pressable disabled={busy === 'quiz'} onPress={onSubmitQuiz} style={s.cta}><Text style={s.ctaTxt}>INVIA · +€ + NACKL</Text></Pressable>
                </>
              ))}
              {ov && open === 'predictions' && (
                <>
                  <Text style={s.pMeta}>{ov.predictions.open} pronostici aperti · su↑/giù↓ a 24h, chiusi sul prezzo reale.</Text>
                  {ov.predictions.recent.map((p) => (
                    <View key={p.id} style={s.listRow}>
                      <Text style={s.listTxt}>{p.direction === 'up' ? '▲ su' : '▼ giù'}</Text>
                      <Text style={[s.listTag, { color: p.status === 'won' ? colors.green : p.status === 'lost' ? colors.red : colors.muted }]}>
                        {p.status === 'won' ? '✓ vinto' : p.status === 'lost' ? '✗ perso' : '… in corso'}{p.reward_amount ? ` · +${p.reward_amount} NACKL` : ''}
                      </Text>
                    </View>
                  ))}
                  <Text style={s.pMeta}>Apri un nuovo pronostico dal Dettaglio di un giocatore.</Text>
                </>
              )}
              {ov && open === 'challenge' && (
                <>
                  <Text style={s.pMeta}>{ov.challenge.metric} · {ov.challenge.week_key} · tu #{ov.challenge.my_rank ?? '—'} / {ov.challenge.total}</Text>
                  {ov.challenge.standings.map((st) => (
                    <View key={st.rank} style={[s.listRow, st.is_self && { borderColor: colors.cyan, borderWidth: borderW }]}>
                      <Text style={s.listTxt}>{['🥇', '🥈', '🥉'][st.rank - 1] ?? `#${st.rank}`} {st.pseudonym}{st.is_self ? ' (TU)' : ''}</Text>
                      <Text style={[s.listTag, { color: st.return_pct >= 0 ? colors.green : colors.red }]}>
                        {st.return_pct >= 0 ? '+' : ''}{st.return_pct.toFixed(1)}%{st.prize_proposed ? ` · ${st.prize_proposed.credits}cr+${st.prize_proposed.nackl}N` : ''}
                      </Text>
                    </View>
                  ))}
                </>
              )}
              {ov && open === 'news' && (
                <>
                  <Text style={s.pMeta}>Eventi di mercato dai dati interni · informativo (nessun premio).</Text>
                  {ov.news.items.length === 0 && <Text style={s.pMeta}>Nessun evento di rilievo al momento.</Text>}
                  {ov.news.items.map((n, i) => (
                    <View key={i} style={s.listRow}>
                      <View style={{ flex: 1, minWidth: 0 }}>
                        <Text style={[s.qTxt, { color: toneColor(n.tone) }]} numberOfLines={2}>{n.title}</Text>
                        <Text style={s.pMeta}>{n.detail}</Text>
                      </View>
                    </View>
                  ))}
                </>
              )}
              {ov && open === 'missions' && ov.missions.map((m) => (
                <View key={m.id} style={s.mission}>
                  <View style={s.missionTop}>
                    <Text style={s.qTxt}>{m.title}</Text>
                    <Text style={[s.listTag, { color: m.completed ? colors.green : colors.muted }]}>{m.claimed ? '✓ riscattata' : m.completed ? 'completata' : 'in corso'}</Text>
                  </View>
                  <Text style={s.pMeta}>{m.description}</Text>
                  <Bar value={Math.min(m.progress, m.target)} max={m.target} color={m.completed ? colors.green : colors.cyan} />
                  <Text style={s.pMeta}>{Math.round(Math.min(m.progress, m.target)).toLocaleString('it-IT')} / {m.target.toLocaleString('it-IT')} · premio €{m.reward_proposed.credits} + {m.reward_proposed.nackl} NACKL</Text>
                  {m.completed && !m.claimed && (
                    <Pressable disabled={busy === m.id} onPress={() => onClaimMission(m)} style={[s.cta, { alignSelf: 'flex-start' }]}><Text style={s.ctaTxt}>RISCATTA</Text></Pressable>
                  )}
                </View>
              ))}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

const pstyles = StyleSheet.create({
  track: { height: 8, borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.10)', marginTop: spacing.xs, overflow: 'hidden' },
  fill: { height: 8, borderRadius: 999 },
});

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 60, gap: spacing.md, maxWidth: 1000, width: '100%', alignSelf: 'center' },
  title: { ...typography.pageTitle, color: colors.text },
  subtitle: { ...typography.small, color: colors.muted, marginTop: -spacing.sm },
  toast: { backgroundColor: colors.surfaceAlt, borderRadius: radius.md, borderWidth: borderW, borderColor: colors.cyan, padding: spacing.sm },
  toastTxt: { ...typography.small, color: colors.text },
  grid: {},
  gridDesktop: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  cellBase: { marginBottom: 24 },     // gap VERTICALE reale tra le righe (rowGap non rende su RNW)
  cellDesktop: { width: '48.5%' },
  cellMobile: { width: '100%' },
  launcher: { height: 122, justifyContent: 'flex-start', gap: 4 },
  launcherRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  note: { ...typography.caption, color: colors.muted, textAlign: 'center', marginTop: spacing.md },
  // panel
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.55)', justifyContent: 'center', alignItems: 'center', padding: spacing.lg },
  panel: { backgroundColor: colors.surface, borderRadius: radius.card, borderWidth: borderW, borderColor: colors.border, padding: spacing.lg },
  panelDesktop: { width: '100%', maxWidth: 560, maxHeight: '85%' },
  panelMobile: { width: '100%', maxHeight: '88%' },
  panelHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md },
  panelTitle: { ...typography.h2, color: colors.text },
  big: { ...typography.mono, fontSize: 30, fontWeight: '700', color: colors.cyan },
  pMeta: { ...typography.small, color: colors.muted },
  qTxt: { ...typography.bodyBold, color: colors.text },
  opts: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 4 },
  opt: { backgroundColor: colors.bg, borderWidth: borderW, borderColor: colors.border, borderRadius: radius.pill, paddingHorizontal: 12, paddingVertical: 6 },
  optTxt: { ...typography.small, color: colors.text },
  cta: { backgroundColor: colors.cyan, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: 10, alignItems: 'center', marginTop: spacing.xs },
  ctaOff: { opacity: 0.45 },
  ctaTxt: { ...typography.monoLabel, color: colors.onAccent },
  listRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: colors.bg, borderRadius: radius.md, borderWidth: borderW, borderColor: colors.border, padding: spacing.sm },
  listTxt: { ...typography.body, color: colors.text },
  listTag: { ...typography.monoLabel },
  mission: { backgroundColor: colors.bg, borderRadius: radius.md, borderWidth: borderW, borderColor: colors.border, padding: spacing.md, gap: 4 },
  missionTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
});
