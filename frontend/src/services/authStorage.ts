/**
 * Auth storage: token JWT + dati utente.
 * Uses the project-provided `@/src/utils/storage` wrapper.
 */
import { storage } from '@/src/utils/storage';

const TOKEN_KEY = 'playerstock.auth.token';
const USER_KEY = 'playerstock.auth.user';

export interface StoredUser {
  id: string;
  email: string;
  name: string;
  picture?: string | null;
  locale: string;
  role: 'user' | 'admin';
  terms_accepted_at: string | null;
  privacy_accepted_at: string | null;
}

export async function saveToken(token: string): Promise<void> {
  await storage.setItem(TOKEN_KEY, token);
}

export async function getToken(): Promise<string | null> {
  return storage.getItem(TOKEN_KEY);
}

export async function clearAuth(): Promise<void> {
  await storage.removeItem(TOKEN_KEY);
  await storage.removeItem(USER_KEY);
}

export async function saveUser(user: StoredUser): Promise<void> {
  await storage.setItem(USER_KEY, JSON.stringify(user));
}

export async function getUser(): Promise<StoredUser | null> {
  const raw = await storage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
}
