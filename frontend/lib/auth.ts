const TOKEN_STORAGE_KEY = "applypilot_token";
const USER_STORAGE_KEY = "applypilot_user";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function getStoredUserJson(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(USER_STORAGE_KEY);
}

export function setStoredUserJson(userJson: string): void {
  window.localStorage.setItem(USER_STORAGE_KEY, userJson);
}

export function clearStoredUserJson(): void {
  window.localStorage.removeItem(USER_STORAGE_KEY);
}
