import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BentoCard } from '@/src/components/BentoCard';
import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { getCurrentMatchDay, type MatchDayState } from '@/src/services/matchday.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { type ThemeColors } from '@/src/theme/tokens';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { formatPrice } from '@/src/utils/formatters';

const mmss = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

export default function MatchDay() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);

  const [state, setState] = useState<MatchDayState | null>(null);
  const [loading, setLoading] = useState(true);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const ticker = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    try {
      const s = await getCurrentMatchDay();
      setState(s);
      if (s.live && typeof s.seconds_left === 'number') setSecondsLeft(s.seconds_left);
    } catch {
      setState({ live: false });
    } finally {
      setLoading(false);
    }
  }, []);

  // poll ogni 12s + countdown locale al secondo
  useEffect(() => {
    load();
    const poll = setInterval(load, 12000);
    ticker.current = setInterval(() => setSecondsLeft((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => { clearInterval(poll); if (ticker.current) clearInterval(ticker.current); };
  }, [load]);

  const live = state?.live === true;

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <GeometricBackground />
      <View style={styles.headerBar}>
        <Pressable style={styles.backBtn} onPress={() => router.back()} hitSlop={8}>
          <Ionicons name="chevron-back" size={20} color={colors.text} />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('matchday.title')}</Text>

        {loading && !state ? (
          <ActivityIndicator color={colors.accent} style={{ marginTop: spacing.xl }} />
        ) : !live ? (
          <BentoCard testID="matchday-soon">
            <View style={styles.soonPill}><Text style={styles.soonTxt}>{t('home.matchday_soon')}</Text></View>
            <Text style={styles.heroTitle}>{t('matchday.soon_title')}</Text>
            <Text style={styles.heroSub}>{t('matchday.soon_body')}</Text>
          </BentoCard>
        ) : (
          <>
            <BentoCard testID="matchday-live">
              <View style={styles.liveRow}>
                <View style={styles.livePill}><Text style={styles.liveTxt}>{t('matchday.live')}</Text></View>
                <Text style={styles.countdown}>{mmss(secondsLeft)}</Text>
              </View>
              <Text style={styles.heroSub}>{t('matchday.tick')} {state?.tick ?? 0} · {t('matchday.ends_in')}</Text>
            </BentoCard>

            <BentoCard title={t('matchday.players')} testID="matchday-slate">
              {(state?.slate ?? []).map((p, i, arr) => (
                <View key={p.athlete_id} style={[styles.row, i < arr.length - 1 && styles.rowBorder]}>
                  <Text style={styles.pName} numberOfLines={1}>{p.label ?? '—'}</Text>
                  <Text style={styles.pRole}>{p.role ?? ''}</Text>
                  <Text style={styles.pPrice}>€{formatPrice(p.prezzo ?? 0)}</Text>
                </View>
              ))}
            </BentoCard>
          </>
        )}

        <Text style={styles.disclaimer}>{t('disclaimer.short')}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  headerBar: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  backBtn: { flexDirection: 'row', alignItems: 'center', padding: spacing.sm, alignSelf: 'flex-start' },
  backText: { ...typography.body, color: colors.text, marginLeft: 2 },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md, maxWidth: 900, width: '100%', alignSelf: 'center' },
  title: { ...typography.pageTitle, color: colors.text },
  soonPill: { alignSelf: 'flex-start', backgroundColor: colors.surfaceAlt, borderRadius: radius.pill, paddingHorizontal: 10, paddingVertical: 3, borderWidth: borderW, borderColor: colors.border },
  soonTxt: { ...typography.monoLabel, fontSize: 9, color: colors.muted },
  heroTitle: { ...typography.h2, color: colors.text },
  heroSub: { ...typography.small, color: colors.muted },
  liveRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  livePill: { backgroundColor: colors.accent, borderRadius: radius.pill, paddingHorizontal: 10, paddingVertical: 3 },
  liveTxt: { ...typography.monoLabel, fontSize: 10, color: colors.onAccent },
  countdown: { ...typography.mono, fontSize: 28, fontWeight: '700', color: colors.text },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: 10 },
  rowBorder: { borderBottomWidth: 1, borderBottomColor: colors.border },
  pName: { ...typography.body, color: colors.text, flex: 1 },
  pRole: { ...typography.monoLabel, fontSize: 10, color: colors.muted, width: 44 },
  pPrice: { ...typography.mono, color: colors.accent, fontWeight: '700', minWidth: 80, textAlign: 'right' },
  disclaimer: { ...typography.caption, color: colors.muted, textAlign: 'center', marginTop: spacing.md },
});
