import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet } from 'react-native';

import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW } from '@/src/theme/spacing';

/** Toggle sole/luna. Commuta tema scuro <-> chiaro. */
export function ThemeToggle({ size = 20 }: { size?: number }) {
  const { colors, isDark, toggle } = useTheme();
  return (
    <Pressable
      testID="theme-toggle"
      onPress={toggle}
      hitSlop={8}
      style={({ pressed }) => [
        styles.btn,
        { borderColor: colors.border, backgroundColor: colors.surfaceAlt },
        pressed && { opacity: 0.7 },
      ]}
      accessibilityLabel={isDark ? 'Tema chiaro' : 'Tema scuro'}
    >
      <Ionicons name={isDark ? 'sunny-outline' : 'moon-outline'} size={size} color={colors.cyan} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: { width: 36, height: 36, borderRadius: 10, borderWidth: borderW, justifyContent: 'center', alignItems: 'center' },
});
