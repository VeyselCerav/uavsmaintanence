export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  locale: "tr" | "en" | "az";
  role: string | null;
  permissions: string[];
};

export type TokenResponse = {
  access: string;
  refresh: string;
  user: AuthUser;
};

const ACCESS_KEY = "uavs.access";
const REFRESH_KEY = "uavs.refresh";
const USER_KEY = "uavs.user";
const SESSION_EVENT = "uavs.session";

let cachedUserRaw: string | null = null;
let cachedUser: AuthUser | null = null;

function notifySession() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function saveSession(payload: TokenResponse) {
  const raw = JSON.stringify(payload.user);
  localStorage.setItem(ACCESS_KEY, payload.access);
  localStorage.setItem(REFRESH_KEY, payload.refresh);
  localStorage.setItem(USER_KEY, raw);
  cachedUserRaw = raw;
  cachedUser = payload.user;
  notifySession();
}

export function clearSession() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  cachedUserRaw = null;
  cachedUser = null;
  notifySession();
}

export function patchStoredUser(partial: Partial<AuthUser>) {
  const current = getStoredUser();
  if (!current) return;
  const next = { ...current, ...partial };
  const raw = JSON.stringify(next);
  localStorage.setItem(USER_KEY, raw);
  cachedUserRaw = raw;
  cachedUser = next;
  notifySession();
}

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (raw === cachedUserRaw) {
    return cachedUser;
  }
  cachedUserRaw = raw;
  if (!raw) {
    cachedUser = null;
    return null;
  }
  try {
    cachedUser = JSON.parse(raw) as AuthUser;
  } catch {
    cachedUser = null;
  }
  return cachedUser;
}

function subscribeSession(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(SESSION_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(SESSION_EVENT, callback);
  };
}

export function getServerUserSnapshot(): AuthUser | null {
  return null;
}

export { subscribeSession };

export function hasPermission(user: AuthUser | null, code: string) {
  if (!user) return false;
  if (user.role === "ADMIN") return true;
  return user.permissions.includes(code);
}

export function canSeeAdminNav(user: AuthUser | null, permission: string, adminOnly = false) {
  if (!user) return false;
  if (adminOnly) return user.role === "ADMIN";
  return hasPermission(user, permission);
}
