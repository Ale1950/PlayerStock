/**
 * useAuth hook: shared auth state across the app.
 */
import { useCallback, useEffect, useState } from 'react';
import { clearAuth, getToken, getUser, type StoredUser } from '@/src/services/authStorage';
import { fetchMe, logoutBackend } from '@/src/services/auth.service';

interface AuthState {
  isLoading: boolean;
  isAuthenticated: boolean;
  user: StoredUser | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({ isLoading: true, isAuthenticated: false, user: null });

  const bootstrap = useCallback(async () => {
    try {
      const token = await getToken();
      const user = await getUser();
      if (!token) {
        setState({ isLoading: false, isAuthenticated: false, user: null });
        return;
      }
      // Token present: try to fetch /users/me to validate
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

  return { ...state, logout, refresh };
}
