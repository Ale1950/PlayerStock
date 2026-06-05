import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { translateError } from '@/src/services/api';
import { getPlayer, type AthletePublic } from '@/src/services/players.service';
import { colors } from '@/src/theme/colors';
import { radius, spacing, typography } from '@/src/theme/spacing';
import { formatInt, formatPrice } from '@/src/utils/formatters';

export default function PlayerDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { t } = useTranslation();
  const [player, setPlayer] = useState<AthletePublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      if (!id) return;
      try {
        setLoading(true);
        const p = await getPlayer(id);
        setPlayer(p);
      } catch (e) { setError(translateError(e)); }
      finally { setLoading(false); }
    })();
  }, [id]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <Pressable testID="player-back" onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
          <Text style={styles.backText}>{t('player.back')}</Text>
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.container}>
        {loading && <ActivityIndicator color={colors.accent} size="large" style={{ marginTop: spacing.xxl }} />}
        {error && <Text style={styles.error}>{error}</Text>}
        {player && (
          <View testID={`player-detail-${player._id}`}>
            <View style={[styles.hero, { backgroundColor: player.team_color_primary ?? colors.card }]}>
              <View style={styles.avatar}><Text style={styles.avatarText}>{player.display_initial[0]}</Text></View>
              <Text style={styles.name}>{player.display_label}</Text>
              <Text style={styles.meta}>{t(`player.role_${player.role}`)} · {player.nationality_iso3} · {player.age ?? '?'}</Text>
              <Text style={styles.team}>{player.team_fantasy_name}</Text>
            </View>

            <View style={styles.statRow}>
              <StatBox label={t('player.price_current')} value={`€${formatPrice(player.prezzo_corrente_crediti)}`} color={colors.up} testID="player-price-current" />
              <StatBox label={t('player.price_initial')} value={`€${formatPrice(player.prezzo_iniziale_crediti)}`} testID="player-price-initial" />
            </View>

            <View style={styles.infoCard}>
              <InfoRow label={t('player.float')} value={formatInt(player.float_quote)} />
              <InfoRow label="Valore iniziale" value={`${formatInt(player.valore_iniziale_crediti)} ${t('common.currency_unit')}`} />
              <InfoRow label="Stato" value={player.status} />
            </View>

            <View style={styles.phaseNote} testID="player-phase-note">
              <Ionicons name="construct-outline" size={20} color={colors.warning} />
              <View style={{ flex: 1 }}>
                <Text style={styles.phaseNoteText}>{t('player.buy_disabled_phase1')}</Text>
                <Text style={styles.phaseNoteSub}>{t('player.phase2_note')}</Text>
              </View>
            </View>

            <Text style={styles.disclaimer}>{t('disclaimer.long')}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function StatBox({ label, value, color, testID }: { label: string; value: string; color?: string; testID?: string }) {
  return (
    <View style={styles.statBox} testID={testID}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={[styles.statValue, color ? { color } : undefined]}>{value}</Text>
    </View>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  backBtn: { flexDirection: 'row', alignItems: 'center', padding: spacing.sm, alignSelf: 'flex-start' },
  backText: { ...typography.body, color: colors.textPrimary, marginLeft: 2 },
  container: { padding: spacing.lg, paddingBottom: spacing.xxl },
  hero: { padding: spacing.xl, borderRadius: radius.lg, alignItems: 'center', marginBottom: spacing.lg },
  avatar: { width: 88, height: 88, borderRadius: 44, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'center', alignItems: 'center' },
  avatarText: { color: '#FFF', fontSize: 40, fontWeight: '700' },
  name: { ...typography.h2, color: '#FFF', marginTop: spacing.md, textAlign: 'center' },
  meta: { ...typography.body, color: 'rgba(255,255,255,0.85)', marginTop: 4 },
  team: { ...typography.small, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  statRow: { flexDirection: 'row', gap: spacing.md, marginBottom: spacing.lg },
  statBox: { flex: 1, padding: spacing.md, backgroundColor: colors.card, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border },
  statLabel: { ...typography.caption, color: colors.textSecondary },
  statValue: { ...typography.h3, color: colors.textPrimary, marginTop: 4, fontVariant: ['tabular-nums'] },
  infoCard: { backgroundColor: colors.card, padding: spacing.md, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
  infoLabel: { ...typography.body, color: colors.textSecondary },
  infoValue: { ...typography.bodyBold, color: colors.textPrimary, fontVariant: ['tabular-nums'] },
  phaseNote: {
    flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start',
    padding: spacing.md, marginTop: spacing.lg, backgroundColor: colors.bannerBg,
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.bannerBorder,
  },
  phaseNoteText: { ...typography.body, color: colors.bannerText },
  phaseNoteSub: { ...typography.small, color: colors.bannerText, opacity: 0.7, marginTop: 2 },
  disclaimer: { ...typography.caption, color: colors.textMuted, marginTop: spacing.xl, textAlign: 'center' },
  error: { color: colors.danger, padding: spacing.lg, textAlign: 'center' },
});
