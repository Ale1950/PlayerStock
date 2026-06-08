/**
 * API client: axios instance with auth interceptor and i18n-friendly error mapping.
 */
import axios, { AxiosError, AxiosInstance } from 'axios';
import i18n from '@/src/i18n';

import { clearAuth, getToken } from './authStorage';

// Single-origin (deploy web prod): EXPO_PUBLIC_BACKEND_URL vuoto → base RELATIVA "/api"
// (stesso dominio del backend, niente CORS). Per l'app NATIVA contro il prod va invece
// impostato all'URL ASSOLUTO del dominio. In dev (Expo :8081) punta al tunnel.
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL ?? '';

const api: AxiosInstance = axios.create({
  baseURL: `${BACKEND_URL}/api`,   // "" ⇒ "/api" relativo (single-origin)
  timeout: 20000,
});

api.interceptors.request.use(async (config) => {
  config.headers = config.headers ?? {};
  // DEV: bypassa l'interstiziale "warning" di ngrok su TUTTE le richieste (tunnel dev).
  (config.headers as Record<string, string>)['ngrok-skip-browser-warning'] = 'true';
  const token = await getToken();
  if (token) {
    (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface ApiError {
  error_code: string;
  message_it: string;
  status?: number;
}

api.interceptors.response.use(
  (r) => r,
  (err: AxiosError<{ detail?: ApiError }>) => {
    if (err.response?.status === 401) {
      // session expired → clear stored auth
      clearAuth().catch(() => {});
    }
    return Promise.reject(err);
  },
);

/**
 * Get a human-readable error message from an axios error, using i18n.
 */
export function translateError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as any)?.detail;
    if (detail?.error_code) {
      const key = `error.${detail.error_code}`;
      const translated = i18n.t(key);
      if (translated !== key) return translated;
      return detail.message_it ?? i18n.t('common.error_generic');
    }
  }
  return i18n.t('common.error_generic');
}

export default api;
