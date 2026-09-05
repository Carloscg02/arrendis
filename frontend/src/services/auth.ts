import type { TokenResponse, UserResponse, LoginInput, RegisterInput } from '../types';

const API_BASE = 'http://localhost:8000/api';

const TOKEN_KEY = 'rental_handler_access_token';

let accessToken: string | null = (typeof window !== 'undefined') ? sessionStorage.getItem(TOKEN_KEY) : null;
let refreshPromise: Promise<TokenResponse> | null = null;

export function getAccessToken(): string | null {
  if (!accessToken && typeof window !== 'undefined') {
    accessToken = sessionStorage.getItem(TOKEN_KEY);
  }
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
  if (typeof window !== 'undefined') {
    if (token) {
      sessionStorage.setItem(TOKEN_KEY, token);
    } else {
      sessionStorage.removeItem(TOKEN_KEY);
    }
  }
}

async function handleAuthResponse(res: Response): Promise<TokenResponse> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Error de autenticación');
  }
  return res.json();
}

export async function register(data: RegisterInput): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    credentials: 'include',
  });
  const result = await handleAuthResponse(res);
  setAccessToken(result.access_token);
  return result;
}

export async function login(data: LoginInput): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    credentials: 'include',
  });
  const result = await handleAuthResponse(res);
  setAccessToken(result.access_token);
  return result;
}

export async function refresh(): Promise<TokenResponse> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      const result = await handleAuthResponse(res);
      setAccessToken(result.access_token);
      return result;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  setAccessToken(null);
}

export async function getMe(): Promise<UserResponse> {
  const token = getAccessToken();
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    credentials: 'include',
  });
  if (!res.ok) throw new Error('No autenticado');
  return res.json();
}

export function clearSession(): void {
  setAccessToken(null);
}
