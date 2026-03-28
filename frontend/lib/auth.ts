/**
 * Authentication utilities for token management.
 */

const TOKEN_KEY = "specsentinel_token";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function logout(): void {
  removeToken();
  window.location.href = "/login";
}
