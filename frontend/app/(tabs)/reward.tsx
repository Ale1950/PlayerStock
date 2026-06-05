import { Ionicons } from '@expo/vector-icons';
import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { useTranslation } from 'react-i18next';
import {
  ActivityIndicator, Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  connectMiningWallet, getRewardBalance, getRewardProvider,
  type RewardBalance, type RewardProviderInfo,
} from '@/src/services/reward.service';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';

export default function Reward() {
  const { t } = useTranslation();
  const [balance, setBalance] = useState<RewardBalance | null>(null);
  const [provider, setProvider] = useState<RewardProviderInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [key, setKey] = useState('');
  const [connecting, setConnecting] = useState(false);

  const load = useCallback(() => {
    let active = true;
    setLoading(true);
    Promise.all([getRewardBalance(), getRewardProvider()])
      .then(([b, p]) => { if (active) { setBalance(b); setProvider(p); } })
      .catch(() => { /* offline / non loggato: lascia stato vuoto */ })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  useFocusEffect(load);

  const onConnect = async () => {
    if (!key.trim()) return;
    setConnecting(true);
    try {
      await connectMiningWallet(key.trim());
      setKey('');
      Alert.alert(t('reward.connect_ok'));
      load();
    } catch {
      Alert.alert(t('reward.connect_err'));
    } finally {
      setConnecting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t('reward.title')}</Text>

        {/* Saldo (placeholder MVP) */}
        <View style={styles.card} testID="reward-balance-card">
          <View style={styles.row}>
            <Text style={styles.cardLabel}>{t('reward.balance_title')}</Text>
            {balance?.is_placeholder && (
              <View style={styles.badge}><Text style={styles.badgeText}>{t('reward.placeholder_badge')}</Text></View>
            )}
          </View>
          {loading ? (
            <ActivityIndicator color={colors.accent} />
          ) : (
            <Text style={styles.balanceValue}>{(balance?.amount ?? 0).toFixed(2)} NACKL</Text>
          )}
          <Text style={styles.note}>{t('reward.placeholder_note')}</Text>
        </View>

        {/* Provider / rete / mining */}
        <View style={styles.infoBox}>
          <Ionicons name="hardware-chip-outline" size={20} color={colors.accent} />
          <View style={{ flex: 1 }}>
            <Text style={styles.infoText}>
              {t('reward.provider_title')}: {provider?.provider_name ?? '—'} · {t('reward.network')}: {provider?.network ?? '—'}
            </Text>
            <Text style={styles.miningText}>⛏️ {t('reward.mining_coming')}</Text>
          </View>
        </View>

        {/* Wallet connect (solo public key) */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>{t('reward.wallet_title')}</Text>
          <Text style={[styles.note, { color: provider?.wallet_connected ? colors.up : colors.textMuted }]}>
            {provider?.wallet_connected ? `✓ ${t('reward.wallet_connected')}` : t('reward.wallet_not_connected')}
          </Text>
          <Text style={styles.hint}>{t('reward.connect_hint')}</Text>
          <TextInput
            style={styles.input}
            value={key}
            onChangeText={setKey}
            placeholder={t('reward.connect_placeholder')}
            placeholderTextColor={colors.textMuted}
            autoCapitalize="none"
            autoCorrect={false}
          />
          <TouchableOpacity style={styles.cta} onPress={onConnect} disabled={connecting || !key.trim()}>
            {connecting
              ? <ActivityIndicator color={colors.bg} />
              : <Text style={styles.ctaText}>{t('reward.connect_cta')}</Text>}
          </TouchableOpacity>
          <Text style={styles.qrSoon}><Ionicons name="qr-code-outline" size={14} /> {t('reward.scan_qr_soon')}</Text>
        </View>

        <View style={styles.infoBox}>
          <Ionicons name="information-circle-outline" size={20} color={colors.accent} />
          <Text style={styles.infoText}>{t('reward.info_separated')}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, gap: spacing.md },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.sm },
  card: {
    padding: spacing.lg, backgroundColor: colors.card,
    borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border, gap: spacing.sm,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardLabel: { ...typography.small, color: colors.textMuted, textTransform: 'uppercase' },
  balanceValue: { ...typography.h1, color: colors.accent },
  note: { ...typography.small, color: colors.textSecondary, lineHeight: 18 },
  hint: { ...typography.small, color: colors.textMuted, lineHeight: 16 },
  badge: { backgroundColor: colors.bgElevated, borderRadius: radius.sm, paddingHorizontal: 8, paddingVertical: 2, borderWidth: 1, borderColor: colors.border },
  badgeText: { ...typography.small, color: colors.textMuted, fontSize: 10 },
  input: {
    backgroundColor: colors.bg, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm, color: colors.textPrimary,
  },
  cta: { backgroundColor: colors.accent, borderRadius: radius.md, paddingVertical: spacing.md, alignItems: 'center' },
  ctaText: { ...typography.body, color: colors.bg, fontWeight: '700' },
  qrSoon: { ...typography.small, color: colors.textMuted, textAlign: 'center' },
  miningText: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  infoBox: {
    padding: spacing.md, borderRadius: radius.md, backgroundColor: colors.bgElevated,
    borderWidth: 1, borderColor: colors.border, flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start',
  },
  infoText: { ...typography.small, color: colors.textSecondary, flex: 1, lineHeight: 18 },
});
