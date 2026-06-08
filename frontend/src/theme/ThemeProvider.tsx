/**
 * PlayerStock — Theme provider.
 * Tema UNICO scuro (Luxury). Niente toggle/tema chiaro (ritirati — D12).
 * `isDark` resta esposto (sempre true) per compat con i call-site.
 *
 * Uso:
 *   const { colors } = useTheme();
 *   const styles = useMemo(() => makeStyles(colors), [colors]);
 */
import { createContext, useContext, useMemo, type ReactNode } from 'react';

import { themes, type ThemeColors } from './tokens';

interface ThemeContextValue {
  colors: ThemeColors;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const value = useMemo<ThemeContextValue>(() => ({
    colors: themes.dark,
    isDark: true,
  }), []);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme deve essere usato dentro <ThemeProvider>');
  return ctx;
}
