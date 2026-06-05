/**
 * API client: axios instance with auth interceptor and i18n-friendly error mapping.
 */
import axios, { AxiosError, AxiosInstance } from 'axios';
import i18n from '@/src/i18n';

import { clearAuth, getToken } from './authStorage';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
if (!BACKEND_URL) {
  console.warn('EXPO_PUBLIC_BACKEND_URL is not defined; API calls will fail');
}

const api: AxiosInstance = axios.create({
  baseURL: `${BACKEND_URL ?? ''}/api`,
  timeout: 20000,
});

api.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) {
    config.headers = config.headers ?? {};
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
