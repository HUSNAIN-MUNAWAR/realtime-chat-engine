export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

export type AuthUser = { id: string; email: string; username: string; role: string };

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem('chat_token');
}
export function setAuth(token: string, user: AuthUser) {
  window.localStorage.setItem('chat_token', token);
  window.localStorage.setItem('chat_user', JSON.stringify(user));
}
export function getUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem('chat_user');
  return raw ? JSON.parse(raw) : null;
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const res = await fetch(`${API_URL}${path}`, { ...options, headers, cache: 'no-store' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
