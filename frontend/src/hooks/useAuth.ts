/**
 * Auth state CONDIVISO via Context (un'unica fonte per tutta l'app).
 *
 * Prima era un hook con stato locale per-istanza: il login salvava il token ma
 * l'istanza nel RootNavigator non si aggiornava → isAuthenticated restava false
 * e il guard rimbalzava al login. Ora è un Context: dopo l'exchange il login
 * chiama refresh() e TUTTI i consumer vedono lo stato aggiornato.
 */
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';

import { clearAuth, getToken, type StoredUser } from '@/src/services/authStorage';
import { fetchMe, logoutBackend } from '@/src/services/auth.service';

interface AuthState {
  isLoading: boolean;
  isAuthenticated: boolean;
  user: StoredUser | null;
}

interface AuthValue extends AuthState {
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider(props: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ isLoading: true, isAuthenticated: false, user: null });

  const bootstrap = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) {
        setState({ isLoading: false, isAuthenticated: false, user: null });
        return;
      }
      try {
        const res = await fetchMe();
        const fresh: StoredUser = {
          id: res.user._id,
          email: res.user.email,
          name: res.user.name,
          picture: res.user.picture,
          locale: res.user.locale,
          role: res.user.role,
          terms_accepted_at: res.user.terms_accepted_at,
          privacy_accepted_at: res.user.privacy_accepted_at,
        };
        setState({ isLoading: false, isAuthenticated: true, user: fresh });
      } catch {
        await clearAuth();
        setState({ isLoading: false, isAuthenticated: false, user: null });
      }
    } catch {
      setState({ isLoading: false, isAuthenticated: false, user: null });
    }
  }, []);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const logout = useCallback(async () => {
    await logoutBackend();
    await clearAuth();
    setState({ isLoading: false, isAuthenticated: false, user: null });
  }, []);

  const refresh = useCallback(async () => {
    await bootstrap();
  }, [bootstrap]);

  const value: AuthValue = { ...state, logout, refresh };
  return React.createElement(AuthContext.Provider, { value }, props.children);
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
