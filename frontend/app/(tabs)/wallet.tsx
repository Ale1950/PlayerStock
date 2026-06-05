import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { translateError } from '@/src/services/api';
import { getBalance, getTransactions, type WalletTransaction } from '@/src/services/wallet.service';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';
import { formatCredits, formatDateTime } from '@/src/utils/formatters';

export default function Wallet() {
  const { t } = useTranslation();
  const [balance, setBalance] = useState<number | null>(null);
  const [txs, setTxs] = useState<WalletTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [b, list] = await Promise.all([getBalance(), getTransactions(1, 50)]);
      setBalance(b.balance_credits);
      setTxs(list.items);
    } catch (e) { setError(translateError(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useFocusEffect(useCallback(() => { setLoading(true); load(); }, [load]));

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}><Text style={styles.title}>{t('wallet.title')}</Text></View>

      <View style={styles.balanceCard} testID="wallet-balance-card">
        <Text style={styles.balanceLabel}>{t('wallet.balance')}</Text>
        {loading && balance === null ? (
          <ActivityIndicator color={colors.accent} />
        ) : (
          <Text style={styles.balanceValue} testID="wallet-balance-value">
            {formatCredits(balance ?? 0)} <Text style={styles.balanceUnit}>{t('common.currency_unit')}</Text>
          </Text>
        )}
      </View>

      <Text style={styles.sectionLabel}>{t('wallet.movements')}</Text>
      <FlatList
        testID="wallet-tx-list"
        data={txs}
        keyExtractor={(x) => x._id}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={colors.accent} />}
        ListEmptyComponent={<Text style={styles.empty}>{t('wallet.no_movements')}</Text>}
        renderItem={({ item }) => {
          const isPositive = item.amount > 0;
          return (
            <View style={styles.txRow} testID={`wallet-tx-${item._id}`}>
              <View style={{ flex: 1 }}>
                <Text style={styles.txDesc}>{t(`wallet.tx_${item.type}` as any, { defaultValue: item.description_it })}</Text>
                <Text style={styles.txDate}>{formatDateTime(item.created_at)}</Text>
              </View>
              <Text style={[styles.txAmount, { color: isPositive ? colors.up : colors.down }]}>
                {isPositive ? '+' : ''}{formatCredits(item.amount)}
              </Text>
            </View>
          );
        }}
      />
      {!!error && <Text style={styles.error}>{error}</Text>}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, paddingBottom: spacing.sm },
  title: { ...typography.h1, color: colors.textPrimary },
  balanceCard: {
    marginHorizontal: spacing.lg, padding: spacing.lg,
    backgroundColor: colors.card, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border, marginVertical: spacing.md,
  },
  balanceLabel: { ...typography.caption, color: colors.textSecondary },
  balanceValue: { ...typography.h1, color: colors.up, marginTop: spacing.sm, fontVariant: ['tabular-nums'] },
  balanceUnit: { ...typography.h3, color: colors.textSecondary, fontWeight: '500' },
  sectionLabel: { ...typography.caption, color: colors.textSecondary, paddingHorizontal: spacing.lg, marginTop: spacing.md },
  list: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, paddingBottom: spacing.xxl + 60 },
  txRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border },
  txDesc: { ...typography.body, color: colors.textPrimary },
  txDate: { ...typography.small, color: colors.textMuted, marginTop: 2 },
  txAmount: { ...typography.mono, fontWeight: '700' },
  empty: { ...typography.body, color: colors.textSecondary, padding: spacing.lg, textAlign: 'center' },
  error: { color: colors.danger, padding: spacing.md, textAlign: 'center' },
});
