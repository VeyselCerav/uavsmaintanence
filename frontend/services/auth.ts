import { apiFetch } from "@/services/api";
import { clearSession, patchStoredUser, saveSession, type AuthUser, type TokenResponse } from "@/lib/auth";

export async function login(email: string, password: string) {
  clearSession();
  const data = await apiFetch<TokenResponse>("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  saveSession(data);
  return data;
}

export async function updateProfile(payload: {
  full_name?: string;
  locale?: AuthUser["locale"];
  timezone?: string;
  current_password?: string;
  new_password?: string;
}) {
  const data = await apiFetch<Omit<AuthUser, "permissions">>("/auth/me/", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  patchStoredUser({
    full_name: data.full_name,
    locale: data.locale,
  });
  return data;
}

export function requestPasswordReset(email: string) {
  return apiFetch<{ accepted: boolean; reset_token?: string }>("/auth/forgot-password/", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function confirmPasswordReset(token: string, new_password: string) {
  return apiFetch<{ reset: boolean }>("/auth/forgot-password/confirm/", {
    method: "POST",
    body: JSON.stringify({ token, new_password }),
  });
}
