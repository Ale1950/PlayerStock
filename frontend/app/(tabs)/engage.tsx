import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { translateError } from '@/src/services/api';
import {
  claimStreak, getStreak, getQuizzes, submitQuiz, getPredictions,
  type StreakState, type QuizSummary, type Prediction,
} from '@/src/services/engagement.service';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';

export default function Engage() {
  const { t } = useTranslation();
  const [streak, setStreak] = useState<StreakState | null>(null);
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [preds, setPreds] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const load = useCallback(async () => {
    setMsg(null);
    try {
      const [s, q, p] = await Promise.all([getStreak(), getQuizzes(), getPredictions()]);
      setStreak(s); setQuizzes(q.items); setPreds(p.items);
    } catch (e) { setMsg(translateError(e)); }
    finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { setLoading(true); load(); }, [load]));

  const onClaimStreak = async () => {
    setBusyAction('streak'); setMsg(null);
    try {
      const r = await claimStreak();
      setMsg(r.claimed
        ? t('engage.streak_claimed_msg', { reward: r.reward_amount?.toFixed(2) ?? '?', streak: r.current_streak })
        : t('engage.streak_already_claimed'));
      await load();
    } catch (e) { setMsg(translateError(e)); }
    finally { setBusyAction(null); }
  };

  const onSubmitQuiz = async (quiz: QuizSummary) => {
    if (!quiz.questions.length) return;
    setBusyAction(quiz.id);
    try {
      // Strategia MVP: random tap su prima opzione (UI completa = Fase 7); per ora "submit demo"
      const answers = quiz.questions.map(() => 0);
      const r = await submitQuiz(quiz.id, answers);
      setMsg(t('engage.quiz_done_msg', { correct: r.correct, total: r.total, reward: r.reward_amount.toFixed(2) }));
      await load();
    } catch (e) { setMsg(translateError(e)); }
    finally { setBusyAction(null); }
  };

  if (loading) return (
    <SafeAreaView style={styles.safe}><View style={styles.loading}><ActivityIndicator color={colors.accent} size="large"/></View></SafeAreaView>
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('engage.title')}</Text>
        <Text style={styles.sub}>{t('engage.subtitle')}</Text>

        {!!msg && (<View style={styles.banner} testID="engage-banner"><Text style={styles.bannerText}>{msg}</Text></View>)}

        {/* Streak card */}
        <View style={styles.card} testID="engage-streak-card">
          <View style={styles.cardHeader}>
            <Ionicons name="flame" size={24} color={colors.warning} />
            <Text style={styles.cardTitle}>{t('engage.streak_title')}</Text>
          </View>
          <View style={styles.streakRow}>
            <View><Text style={styles.streakBig}>{streak?.current_streak ?? 0}</Text><Text style={styles.streakLabel}>{t('engage.streak_days')}</Text></View>
            <View><Text style={styles.streakMid}>{streak?.longest_streak ?? 0}</Text><Text style={styles.streakLabel}>{t('engage.streak_longest')}</Text></View>
            <View><Text style={styles.streakMid}>{(streak?.next_reward_estimate ?? 1).toFixed(2)}</Text><Text style={styles.streakLabel}>{t('engage.streak_next_reward')}</Text></View>
          </View>
          <Pressable
            testID="engage-streak-claim"
            disabled={!streak?.can_claim_today || busyAction === 'streak'}
            onPress={onClaimStreak}
            style={({ pressed }) => [styles.btn, (!streak?.can_claim_today || busyAction === 'streak') && { opacity: 0.5 }, pressed && { opacity: 0.8 }]}
          >
            {busyAction === 'streak'
              ? <ActivityIndicator color="#fff"/>
              : <Text style={styles.btnText}>{streak?.can_claim_today ? t('engage.streak_claim_btn') : t('engage.streak_already_claimed')}</Text>}
          </Pressable>
        </View>

        {/* Quiz card */}
        <View style={styles.card} testID="engage-quizzes-card">
          <View style={styles.cardHeader}>
            <Ionicons name="help-circle" size={24} color={colors.accent} />
            <Text style={styles.cardTitle}>{t('engage.quiz_title')}</Text>
          </View>
          {quizzes.length === 0 ? (
            <Text style={styles.empty}>{t('engage.no_quiz')}</Text>
          ) : quizzes.map((q) => (
            <View key={q.id} style={styles.quizItem} testID={`engage-quiz-${q.id}`}>
              <View style={{ flex: 1 }}>
                <Text style={styles.quizTitle}>{q.title}</Text>
                <Text style={styles.quizMeta}>{q.questions.length} {t('engage.quiz_questions')}</Text>
              </View>
              <Pressable
                testID={`engage-quiz-submit-${q.id}`}
                onPress={() => onSubmitQuiz(q)}
                disabled={busyAction === q.id}
                style={({ pressed }) => [styles.btnSmall, busyAction === q.id && { opacity: 0.5 }, pressed && { opacity: 0.8 }]}
              >
                <Text style={styles.btnSmallText}>{busyAction === q.id ? '...' : t('engage.quiz_play')}</Text>
              </Pressable>
            </View>
          ))}
          <Text style={styles.noteSmall}>{t('engage.quiz_note_phase7')}</Text>
        </View>

        {/* Predictions card */}
        <View style={styles.card} testID="engage-predictions-card">
          <View style={styles.cardHeader}>
            <Ionicons name="trending-up" size={24} color={colors.up} />
            <Text style={styles.cardTitle}>{t('engage.predictions_title')}</Text>
          </View>
          {preds.length === 0 ? (
            <Text style={styles.empty}>{t('engage.no_predictions')}</Text>
          ) : preds.map((p) => {
            const won = p.outcome === 'won';
            const lost = p.outcome === 'lost';
            const c = won ? colors.up : lost ? colors.down : colors.textSecondary;
            return (
              <View key={p.id} style={styles.predItem} testID={`engage-pred-${p.id}`}>
                <Ionicons name={p.direction === 'up' ? 'arrow-up-circle' : 'arrow-down-circle'} size={20} color={c} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.predTitle}>{p.direction === 'up' ? t('engage.pred_up') : t('engage.pred_down')} · {p.base_price.toFixed(4)}</Text>
                  <Text style={styles.predMeta}>{p.status} {p.reward_amount > 0 ? `· +${p.reward_amount.toFixed(2)} NACKL` : ''}</Text>
                </View>
              </View>
            );
          })}
          <Text style={styles.noteSmall}>{t('engage.predictions_note')}</Text>
        </View>

        <Text style={styles.disclaimer}>{t('engage.reward_note')}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 60 },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { ...typography.h1, color: colors.textPrimary },
  sub: { ...typography.body, color: colors.textSecondary, marginTop: 4 },
  banner: { padding: spacing.md, backgroundColor: colors.accent + '22', borderRadius: radius.md, borderWidth: 1, borderColor: colors.accent, marginTop: spacing.md },
  bannerText: { ...typography.body, color: colors.accent },
  card: { padding: spacing.lg, backgroundColor: colors.card, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border, marginTop: spacing.md, gap: spacing.md },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  cardTitle: { ...typography.h3, color: colors.textPrimary },
  streakRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.sm },
  streakBig: { ...typography.h1, color: colors.warning, fontVariant: ['tabular-nums'] },
  streakMid: { ...typography.h2, color: colors.textPrimary, fontVariant: ['tabular-nums'] },
  streakLabel: { ...typography.caption, color: colors.textMuted, marginTop: 2 },
  btn: { backgroundColor: colors.accent, paddingVertical: 14, borderRadius: radius.md, alignItems: 'center', minHeight: 48, justifyContent: 'center' },
  btnText: { ...typography.bodyBold, color: '#fff' },
  btnSmall: { backgroundColor: colors.accent, paddingHorizontal: spacing.md, paddingVertical: 8, borderRadius: radius.md },
  btnSmallText: { ...typography.small, color: '#fff', fontWeight: '600' },
  quizItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
  quizTitle: { ...typography.bodyBold, color: colors.textPrimary },
  quizMeta: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  empty: { ...typography.body, color: colors.textSecondary, paddingVertical: spacing.sm },
  predItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
  predTitle: { ...typography.bodyBold, color: colors.textPrimary },
  predMeta: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  noteSmall: { ...typography.caption, color: colors.textMuted, fontStyle: 'italic' },
  disclaimer: { ...typography.caption, color: colors.textMuted, marginTop: spacing.lg, textAlign: 'center' },
});
