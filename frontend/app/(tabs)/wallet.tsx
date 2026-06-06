import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { GeometricBackground } from '@/src/components/chrome/GeometricBackground';
import { type Column, ResponsiveTable } from '@/src/components/ResponsiveTable';
import { StateView } from '@/src/components/StateView';
import { VividCard, VividText } from '@/src/components/VividCard';
import { translateError } from '@/src/services/api';
import {
  connectMiningWallet, getRewardBalance, getRewardProvider,
  type RewardBalance, type RewardProviderInfo,
} from '@/src/services/reward.service';
import { getBalance, getTransactions, type WalletTransaction } from '@/src/services/wallet.service';
import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, radius, spacing, typography } from '@/src/theme/spacing';
import { type ThemeColors } from '@/src/theme/tokens';
import { formatCredits, formatDateTime } from '@/src/utils/formatters';

const DAILY_CAP = 500; // €/giorno da attività (faucet, D7 ×100) — solo display

function isToday(iso: string): boolean {
  const d = new Date(iso); const n = new Date();
  return d.getFullYear() === n.getFullYear() && d.getMonth() === n.getMonth() && d.getDate() === n.getDate();
}

export default function CreditsHub() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);

  const [balance, setBalance] = useState<number | null>(null);
  const [txs, setTxs] = useState<WalletTransaction[]>([]);
  const [reward, setReward] = useState<RewardBalance | null>(null);
  const [provider, setProvider] = useState<RewardProviderInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [key, setKey] = useState('');
  const [connecting, setConnecting] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [b, list] = await Promise.all([getBalance(), getTransactions(1, 50)]);
      setBalance(b.balance_eur);
      setTxs(list.items);
    } catch (e) { setError(translateError(e)); }
    finally { setLoading(false); }
    // NACKL: indipendente, non blocca i Crediti se fallisce
    try {
      const [rb, rp] = await Promise.all([getRewardBalance(), getRewardProvider()]);
      setReward(rb); setProvider(rp);
    } catch { /* offline reward provider: blocco mostrato vuoto */ }
  }, []);

  useFocusEffect(useCallback(() => { setLoading(true); load(); }, [load]));

  const todayActivity = useMemo(
    () => txs.filter((x) => x.type === 'engagement_reward' && x.amount > 0 && isToday(x.created_at))
      .reduce((s, x) => s + x.amount, 0),
    [txs],
  );
  const capPct = Math.min(100, (todayActivity / DAILY_CAP) * 100);
  const capReached = todayActivity >= DAILY_CAP;

  const onConnect = async () => {
    if (!key.trim()) return;
    setConnecting(true);
    try {
      await connectMiningWallet(key.trim());
      setKey('');
      Alert.alert(t('reward.connect_ok'));
      load();
    } catch { Alert.alert(t('reward.connect_err')); }
    finally { setConnecting(false); }
  };

  // Traguardi DISPLAY-ONLY (celebrativi, nessun premio) — derivati dai dati esistenti
  const achievements = useMemo(() => ([
    { key: 'welcome', icon: 'gift-outline' as const, got: txs.some((x) => x.type === 'welcome_bonus') },
    { key: 'first_activity', icon: 'flame-outline' as const, got: txs.some((x) => x.type === 'engagement_reward') },
    { key: 'nackl_active', icon: 'sparkles-outline' as const, got: (reward?.amount ?? 0) > 0 },
    { key: 'daily_cap', icon: 'speedometer-outline' as const, got: capReached },
  ]), [txs, reward, capReached]);

  const txColumns: Column<WalletTransaction>[] = [
    { key: 'desc', label: t('credits_hub.col_desc'), flex: 1.6, render: (x) => (
      <Text style={styles.txDesc} numberOfLines={1}>{t(`wallet.tx_${x.type}` as any, { defaultValue: x.description_it })}</Text>) },
    { key: 'date', label: t('credits_hub.col_date'), width: 150, render: (x) => (
      <Text style={styles.txDate}>{formatDateTime(x.created_at)}</Text>) },
    { key: 'amount', label: t('credits_hub.col_amount'), width: 110, align: 'right', render: (x) => (
      <Text style={[styles.txAmount, { color: x.amount >= 0 ? colors.green : colors.red }]}>
        {x.amount >= 0 ? '+' : ''}{formatCredits(x.amount)}
      </Text>) },
  ];

  const txCard = (x: WalletTransaction) => (
    <View style={styles.txCard} testID={`wallet-tx-${x._id}`}>
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={styles.txDesc} numberOfLines={1}>{t(`wallet.tx_${x.type}` as any, { defaultValue: x.description_it })}</Text>
        <Text style={styles.txDate}>{formatDateTime(x.created_at)}</Text>
      </View>
      <Text style={[styles.txAmount, { color: x.amount >= 0 ? colors.green : colors.red }]}>
        {x.amount >= 0 ? '+' : ''}{formatCredits(x.amount)}
      </Text>
    </View>
  );

  return (
    <View style={styles.safe} testID="credits-hub">
      <GeometricBackground />
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <Text style={styles.title}>{t('tabs.wallet')}</Text>

        {/* ───────── BLOCCO 1 — CREDITI (sobrio) ───────── */}
        <Text style={styles.sectionLabel}>{t('credits_hub.credits_section')}</Text>
        <View style={styles.balanceCard} testID="credits-balance">
          <Text style={styles.balanceLabel}>{t('credits_hub.balance')}</Text>
          {loading && balance === null
            ? <StateView loading />
            : <Text style={styles.balanceValue} testID="credits-balance-value">
                {formatCredits(balance ?? 0)} <Text style={styles.balanceUnit}>{t('common.currency_unit')}</Text>
              </Text>}
        </View>

        <View style={styles.capCard} testID="credits-daily-cap">
          <View style={styles.rowBetween}>
            <Text style={styles.capLabel}>{t('credits_hub.daily_activity')}</Text>
            <Text style={[styles.capCount, { color: capReached ? colors.green : colors.amber }]}>
              {formatCredits(Math.min(todayActivity, DAILY_CAP))}/{DAILY_CAP}
            </Text>
          </View>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${capPct}%`, backgroundColor: capReached ? colors.green : colors.amber }]} />
          </View>
          <Text style={styles.capHint}>
            {capReached ? t('credits_hub.daily_cap_reached') : t('credits_hub.daily_cap_hint', { cap: DAILY_CAP })}
          </Text>
          <Pressable testID="credits-earn-link" onPress={() => router.push('/(tabs)/engage')}
            style={({ pressed }) => [styles.earnBtn, pressed && { opacity: 0.85 }]}>
            <Ionicons name="flame-outline" size={16} color={colors.cyan} />
            <Text style={styles.earnText}>{t('credits_hub.earn_credits')}</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.cyan} />
          </Pressable>
        </View>

        <Text style={styles.sectionLabel}>{t('credits_hub.movements')}</Text>
        {loading || error || txs.length === 0 ? (
          <StateView loading={loading && txs.length === 0} error={error}
            empty={!loading && !error && txs.length === 0} emptyLabel={t('credits_hub.no_movements')} icon="receipt-outline" />
        ) : (
          <View testID="credits-movements">
            <ResponsiveTable
              data={txs}
              columns={txColumns}
              keyExtractor={(x) => x._id}
              renderCard={txCard}
            />
          </View>
        )}

        {/* ───────── BLOCCO 2 — REWARD · NACKL (vivido, distinto) ───────── */}
        <Text style={[styles.sectionLabel, { marginTop: spacing.xl }]}>{t('credits_hub.nackl_section')}</Text>
        <VividCard variant="purple" pill={reward?.is_placeholder !== false ? t('credits_hub.nackl_preview_badge') : undefined}
          style={{ marginBottom: spacing.md }}>
          <View testID="nackl-card">
            <VividText size="small">{t('credits_hub.nackl_balance')}</VividText>
            <VividText size="title">{(reward?.amount ?? 0).toFixed(2)} NACKL</VividText>
            <VividText size="small">
              {t('credits_hub.nackl_status')}: {reward?.status ?? provider?.mining_status ?? '—'} · {t('credits_hub.nackl_network')}: {reward?.network ?? provider?.network ?? '—'}
            </VividText>
            <VividText size="small">{t('credits_hub.nackl_separated')}</VividText>
          </View>
        </VividCard>

        <View style={styles.nacklConnect} testID="nackl-connect">
          <Text style={styles.connectLabel}>{t('reward.wallet_title')}</Text>
          <Text style={[styles.connectStatus, { color: provider?.wallet_connected ? colors.green : colors.muted }]}>
            {provider?.wallet_connected ? `✓ ${t('reward.wallet_connected')}` : t('reward.wallet_not_connected')}
          </Text>
          <Text style={styles.connectHint}>{t('reward.connect_hint')}</Text>
          <TextInput
            testID="nackl-connect-input"
            style={styles.input}
            value={key}
            onChangeText={setKey}
            placeholder={t('reward.connect_placeholder')}
            placeholderTextColor={colors.muted}
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Pressable testID="nackl-connect-btn" onPress={onConnect} disabled={connecting || !key.trim()}
            style={({ pressed }) => [styles.connectBtn, (connecting || !key.trim()) && { opacity: 0.5 }, pressed && { opacity: 0.85 }]}>
            <Text style={styles.connectBtnText}>{t('reward.connect_cta')}</Text>
          </Pressable>
          <Text style={styles.qrSoon}><Ionicons name="qr-code-outline" size={13} /> {t('reward.scan_qr_soon')}</Text>
        </View>

        {/* ───────── BLOCCO 3 — TRAGUARDI (display-only, nessun premio) ───────── */}
        <Text style={[styles.sectionLabel, { marginTop: spacing.xl }]}>{t('credits_hub.achievements')}</Text>
        <Text style={styles.achSub}>{t('credits_hub.achievements_sub')}</Text>
        <View style={styles.achGrid}>
          {achievements.map((a) => (
            <View key={a.key} testID={`achievement-${a.key}`}
              style={[styles.achChip, a.got ? { borderColor: colors.amber, backgroundColor: colors.amber + '18' } : { opacity: 0.55 }]}>
              <View style={[styles.achIcon, { backgroundColor: (a.got ? colors.amber : colors.muted) + '22' }]}>
                <Ionicons name={a.icon} size={18} color={a.got ? colors.amber : colors.muted} />
              </View>
              <Text style={styles.achTitle}>{t(`credits_hub.ach_${a.key}`)}</Text>
              <Text style={styles.achDesc}>{t(`credits_hub.ach_${a.key}_d`)}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const makeStyles = (colors: ThemeColors) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl + 60, maxWidth: 760, width: '100%', alignSelf: 'center' },
  title: { ...typography.pageTitle, color: colors.text, marginBottom: spacing.md },
  sectionLabel: { ...typography.caption, color: colors.muted, marginBottom: spacing.sm, marginTop: spacing.xs },

  balanceCard: {
    padding: spacing.lg, backgroundColor: colors.surface, borderRadius: radius.card,
    borderWidth: borderW, borderColor: colors.border, marginBottom: spacing.md,
  },
  balanceLabel: { ...typography.caption, color: colors.muted },
  balanceValue: { ...typography.pageTitle, color: colors.amber, marginTop: spacing.xs, fontVariant: ['tabular-nums'] },
  balanceUnit: { ...typography.h3, color: colors.muted, fontWeight: '500' },

  capCard: {
    padding: spacing.lg, backgroundColor: colors.surface, borderRadius: radius.card,
    borderWidth: borderW, borderColor: colors.border, marginBottom: spacing.md, gap: spacing.sm,
  },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  capLabel: { ...typography.bodyBold, color: colors.text },
  capCount: { ...typography.bodyBold, fontVariant: ['tabular-nums'] },
  track: { height: 8, borderRadius: 4, backgroundColor: colors.surfaceAlt, overflow: 'hidden' },
  fill: { height: '100%', borderRadius: 4 },
  capHint: { ...typography.small, color: colors.muted },
  earnBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start',
    marginTop: spacing.xs, paddingVertical: 8, paddingHorizontal: 12,
    borderRadius: radius.md, borderWidth: borderW, borderColor: colors.cyan, backgroundColor: colors.cyan + '14',
  },
  earnText: { ...typography.monoLabel, color: colors.cyan },

  txDesc: { ...typography.body, color: colors.text },
  txDate: { ...typography.small, color: colors.muted, marginTop: 2 },
  txAmount: { ...typography.mono, fontWeight: '700' },
  txCard: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    padding: spacing.md, backgroundColor: colors.surface, borderRadius: radius.md,
    borderWidth: borderW, borderColor: colors.border,
  },

  nacklConnect: {
    padding: spacing.lg, backgroundColor: colors.surface, borderRadius: radius.card,
    borderWidth: borderW, borderColor: colors.border, gap: spacing.sm,
  },
  connectLabel: { ...typography.caption, color: colors.muted },
  connectStatus: { ...typography.small },
  connectHint: { ...typography.small, color: colors.muted, lineHeight: 16 },
  input: {
    backgroundColor: colors.bg, borderWidth: borderW, borderColor: colors.border, borderRadius: radius.md,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm, color: colors.text,
  },
  connectBtn: { backgroundColor: colors.cyan, borderRadius: radius.md, paddingVertical: 12, alignItems: 'center' },
  connectBtnText: { ...typography.bodyBold, color: colors.onAccent },
  qrSoon: { ...typography.small, color: colors.muted, textAlign: 'center' },

  achSub: { ...typography.small, color: colors.muted, marginBottom: spacing.md },
  achGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  achChip: {
    width: '47%', flexGrow: 1, padding: spacing.md, borderRadius: radius.card,
    borderWidth: borderW, borderColor: colors.border, backgroundColor: colors.surface, gap: 4,
  },
  achIcon: { width: 34, height: 34, borderRadius: 9, justifyContent: 'center', alignItems: 'center', marginBottom: 2 },
  achTitle: { ...typography.bodyBold, color: colors.text },
  achDesc: { ...typography.small, color: colors.muted },
});
