import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { UserResponse, LoginInput, RegisterInput } from '../types';
import * as authService from '../services/auth';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (data: LoginInput) => Promise<void>;
  register: (data: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Try silent refresh on mount to recover session
  useEffect(() => {
    authService.refresh()
      .then((res) => setUser(res.user))
      .catch(() => { /* No session, user stays null */ })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (data: LoginInput) => {
    const res = await authService.login(data);
    setUser(res.user);
  }, []);

  const register = useCallback(async (data: RegisterInput) => {
    const res = await authService.register(data);
    setUser(res.user);
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
