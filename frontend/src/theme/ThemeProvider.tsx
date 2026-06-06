/**
 * PlayerStock — Theme provider (Fase Design).
 * Espone tema corrente + toggle scuro/chiaro. Default SCURO. Persistito su storage.
 *
 * Uso:
 *   const { colors, scheme, toggle } = useTheme();
 *   const styles = useMemo(() => makeStyles(colors), [colors]);
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { storage } from '@/src/utils/storage';
import { themes, type Scheme, type ThemeColors } from './tokens';

const STORAGE_KEY = 'playerstock.theme.scheme';

interface ThemeContextValue {
  scheme: Scheme;
  colors: ThemeColors;
  isDark: boolean;
  toggle: () => void;
  setScheme: (s: Scheme) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [scheme, setSchemeState] = useState<Scheme>('dark');

  useEffect(() => {
    (async () => {
      const saved = await storage.getItem<string>(STORAGE_KEY, 'dark');
      if (saved === 'light' || saved === 'dark') setSchemeState(saved);
    })();
  }, []);

  const setScheme = useCallback((s: Scheme) => {
    setSchemeState(s);
    void storage.setItem(STORAGE_KEY, s);
  }, []);

  const toggle = useCallback(() => {
    setSchemeState((prev) => {
      const next: Scheme = prev === 'dark' ? 'light' : 'dark';
      void storage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  const value = useMemo<ThemeContextValue>(() => ({
    scheme,
    colors: themes[scheme],
    isDark: scheme === 'dark',
    toggle,
    setScheme,
  }), [scheme, toggle, setScheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme deve essere usato dentro <ThemeProvider>');
  return ctx;
}
