import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { apiClient } from './api';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  createdAt: string;
  token?: string;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = 'docuchat_user';

function readStoredUser(): User | null {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) return null;
  try {
    const parsed = JSON.parse(stored) as User;
    if (!parsed?.token) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize from localStorage synchronously to avoid redirect races after login/signup.
  const [user, setUser] = useState<User | null>(() => readStoredUser());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const restore = async () => {
      try {
        const parsed = readStoredUser();
        if (!parsed) {
          localStorage.removeItem(STORAGE_KEY);
          setIsLoading(false);
          return;
        }

        // Don't block UI on token validation.
        // Immediately allow the app to proceed with the stored token,
        // then validate in the background and clear session if invalid.
        setUser(parsed);
        setIsLoading(false);

        try {
          const me = await apiClient.me();
          const u: User = {
            id: String(me.id),
            email: me.email,
            name: parsed.name || me.email.split('@')[0],
            createdAt: me.created_at || parsed.createdAt || new Date().toISOString(),
            token: parsed.token,
          };
          localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
          setUser(u);
        } catch {
          localStorage.removeItem(STORAGE_KEY);
          setUser(null);
        }
      } catch {
        localStorage.removeItem(STORAGE_KEY);
        setUser(null);
        setIsLoading(false);
      }
    };

    restore();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiClient.login(email, password);
    const u: User = {
      id: String(response.user_id),
      email: response.email || email,
      name: email.split('@')[0],
      createdAt: new Date().toISOString(),
      token: response.access_token,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
    setUser(u);
    setIsLoading(false);
  }, []);

  const signup = useCallback(async (email: string, password: string, name: string) => {
    const response = await apiClient.signup(email, password, name);
    const u: User = {
      id: String(response.user_id),
      email: response.email || email,
      name,
      createdAt: new Date().toISOString(),
      token: response.access_token,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
    setUser(u);
    setIsLoading(false);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    // Instead of throwing immediately, let's provide a more graceful fallback
    console.error('useAuth must be used within AuthProvider');
    return {
      user: null,
      isLoading: false,
      login: async () => { throw new Error('Auth not initialized'); },
      signup: async () => { throw new Error('Auth not initialized'); },
      logout: () => { console.warn('Auth not initialized'); }
    };
  }
  return ctx;
}
