/**
 * PlayerStock — i18n setup (i18next + react-i18next + expo-localization).
 * Default: italiano. Pronto per 10 lingue (it/en/es/fr/de/pt/nl/pl/ro/ar).
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';

import ar from './locales/ar/common.json';
import de from './locales/de/common.json';
import en from './locales/en/common.json';
import es from './locales/es/common.json';
import fr from './locales/fr/common.json';
import it from './locales/it/common.json';
import nl from './locales/nl/common.json';
import pl from './locales/pl/common.json';
import pt from './locales/pt/common.json';
import ro from './locales/ro/common.json';

export const SUPPORTED_LOCALES = ['it', 'en', 'es', 'fr', 'de', 'pt', 'nl', 'pl', 'ro', 'ar'] as const;
export type SupportedLocale = typeof SUPPORTED_LOCALES[number];

const resources = {
  it: { common: it },
  en: { common: en },
  es: { common: es },
  fr: { common: fr },
  de: { common: de },
  pt: { common: pt },
  nl: { common: nl },
  pl: { common: pl },
  ro: { common: ro },
  ar: { common: ar },
};

function detectDeviceLocale(): SupportedLocale {
  try {
    const locales = Localization.getLocales();
    const code = (locales?.[0]?.languageCode || 'it').toLowerCase();
    if ((SUPPORTED_LOCALES as readonly string[]).includes(code)) return code as SupportedLocale;
  } catch {}
  return 'it';
}

i18n.use(initReactI18next).init({
  resources,
  // MVP: parte sempre in italiano; cambieremo questo in fase di settings utente
  lng: 'it',
  fallbackLng: 'it',
  defaultNS: 'common',
  interpolation: { escapeValue: false },
  returnEmptyString: false,
});

export default i18n;
