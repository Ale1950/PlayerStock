import { StyleSheet, Text, View } from 'react-native';

import { typography } from '@/src/theme/spacing';

function initials(name?: string | null): string {
  if (!name) return '··';
  const w = name.trim().split(/\s+/);
  return ((w[0]?.[0] ?? '') + (w[1]?.[0] ?? w[0]?.[1] ?? '')).toUpperCase();
}

/** Stemma squadra fantasy: colori reali (primario fondo + secondario anello) + iniziali. */
export function TeamBadge({ primary, secondary, name, size = 28 }: {
  primary?: string | null; secondary?: string | null; name?: string | null; size?: number;
}) {
  const bg = primary || '#222A36';
  const ring = secondary || 'rgba(255,255,255,0.4)';
  return (
    <View style={[styles.badge, { width: size, height: size, borderRadius: size / 4, backgroundColor: bg, borderColor: ring }]}>
      <Text style={[typography.monoLabel, { fontSize: size * 0.36, color: '#FFF', letterSpacing: 0.5 }]}>{initials(name)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { borderWidth: 2, justifyContent: 'center', alignItems: 'center' },
});
