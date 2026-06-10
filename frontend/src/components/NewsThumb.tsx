import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { StyleSheet, View } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { radius } from '@/src/theme/spacing';
import { gradients } from '@/src/theme/tokens';

/**
 * Thumbnail astratta per le card News (identità Luxury): blocco a gradiente oro/bronzo
 * + icona calcistica. NESSUNA foto/logo reale. Bordo subtle (mai lime: il lime resta
 * sulla card "finestra" contenitore). Varia il gradiente per indice → non tutte uguali.
 */
const VARIANTS = [gradients.amber, gradients.purple, gradients.green] as const;

export function NewsThumb({ icon, index = 0 }: { icon: string; index?: number }) {
  const { colors } = useTheme();
  const grad = VARIANTS[index % VARIANTS.length];
  return (
    <View style={[styles.box, { borderColor: colors.border }]}>
      <LinearGradient colors={grad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.fill}>
        <Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={20} color={colors.onAccent} />
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  box: { width: 44, height: 44, borderRadius: radius.md, borderWidth: 1, overflow: 'hidden' },
  fill: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
