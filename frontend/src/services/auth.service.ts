/**
 * Auth service: Google Sign-In + JWT exchange.
 *
 * Uses expo-auth-session implicit flow. In Expo Go we open the Google consent
 * via WebBrowser; the id_token is exchanged with the backend for an app JWT.
 */
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import api from './api';
import { saveToken, saveUser, type StoredUser } from './authStorage';

WebBrowser.maybeCompleteAuthSession();

const GOOGLE_DISCOVERY = {
  authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  revocationEndpoint: 'https://oauth2.googleapis.com/revoke',
};

/**
 * Builds the Google OAuth request hook. Use inside a component.
 */
export function buildGoogleAuthRequest(clientId: string) {
  const redirectUri = AuthSession.makeRedirectUri({
    scheme: 'frontend',
  });

  return AuthSession.useAuthRequest(
    {
      clientId,
      scopes: ['openid', 'email', 'profile'],
      redirectUri,
      responseType: 'id_token',
      extraParams: { nonce: 'playerstock-' + Math.random().toString(36).slice(2) },
    },
    GOOGLE_DISCOVERY,
  );
}

export interface AuthResponse {
  access_token: string;
  expires_in: number;
  user: StoredUser;
  wallet: { balance_eur: number; updated_at: string };
}

/**
 * Exchange a Google id_token with the backend for an app JWT.
 */
export async function exchangeGoogleToken(idToken: string, locale: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/google/callback', {
    id_token: idToken,
    locale,
  });
  await saveToken(data.access_token);
  await saveUser(data.user);
  return data;
}

/**
 * Auth-code + PKCE: invia code + verifier al backend, che li scambia con Google.
 * Usato su web (l'implicit id_token freezava) e flusso reale per mobile.
 */
export async function exchangeGoogleCode(
  code: string, codeVerifier: string, redirectUri: string, locale: string,
): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/google/exchange', {
    code,
    code_verifier: codeVerifier,
    redirect_uri: redirectUri,
    locale,
  });
  await saveToken(data.access_token);
  await saveUser(data.user);
  return data;
}

export async function fetchMe() {
  const { data } = await api.get('/users/me');
  return data;
}

export async function logoutBackend() {
  try {
    await api.post('/auth/logout');
  } catch {}
}

export async function deleteAccount() {
  await api.delete('/auth/me');
}
