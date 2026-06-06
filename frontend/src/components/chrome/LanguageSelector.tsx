import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text } from 'react-native';

import { SUPPORTED_LOCALES } from '@/src/i18n';
import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, typography } from '@/src/theme/spacing';

/**
 * Selettore lingua compatto (header). Tap = cicla tra le lingue supportate.
 * Mostra il codice ISO maiuscolo in mono. Picker completo: passaggio finale.
 */
export function LanguageSelector() {
  const { colors } = useTheme();
  const { i18n } = useTranslation();
  const [lang, setLang] = useState<string>((i18n.language || 'it').slice(0, 2));

  const onPress = () => {
    const idx = SUPPORTED_LOCALES.indexOf(lang as (typeof SUPPORTED_LOCALES)[number]);
    const next = SUPPORTED_LOCALES[(idx + 1) % SUPPORTED_LOCALES.length];
    setLang(next);
    void i18n.changeLanguage(next);
  };

  return (
    <Pressable
      testID="language-selector"
      onPress={onPress}
      hitSlop={8}
      style={({ pressed }) => [
        styles.btn,
        { borderColor: colors.border, backgroundColor: colors.surfaceAlt },
        pressed && { opacity: 0.7 },
      ]}
    >
      <Text style={[typography.monoLabel, { color: colors.text, letterSpacing: 1 }]}>{lang.toUpperCase()}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: { height: 36, minWidth: 40, paddingHorizontal: 10, borderRadius: 10, borderWidth: borderW, justifyContent: 'center', alignItems: 'center' },
});
