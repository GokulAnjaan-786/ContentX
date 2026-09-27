export const TOKEN_STORAGE_KEY = "contentforge_access_token";
export const USER_STORAGE_KEY = "contentforge_user_profile";

export interface StoredUser {
  id: string;
  email: string;
  role: string;
  org_id: string;
  created_at?: string;
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") return null;
  const userJson = localStorage.getItem(USER_STORAGE_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson) as StoredUser;
  } catch {
    return null;
  }
}

export function setStoredUser(user: StoredUser): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

export function setAuthSession(token: string, user: StoredUser): void {
  setStoredToken(token);
  setStoredUser(user);
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getStoredToken());
}
