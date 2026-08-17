import { apiFetch, apiFetchPage } from "@/services/api";
import type { AccountUser, AuditLog, Role, SystemSetting, UserWritePayload } from "@/types/admin";

export function listUsers(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiFetchPage<AccountUser>(`/users/${query}`);
}

export function createUser(payload: UserWritePayload) {
  return apiFetch<AccountUser>("/users/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateUser(id: string, payload: Partial<UserWritePayload>) {
  return apiFetch<AccountUser>(`/users/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listRoles() {
  return apiFetchPage<Role>("/roles/?page_size=100");
}

export function listSettings() {
  return apiFetch<SystemSetting[]>("/settings/");
}

export function updateSetting(key: string, value: unknown) {
  return apiFetch<SystemSetting>("/settings/", {
    method: "PATCH",
    body: JSON.stringify({ key, value }),
  });
}

export function listAuditLogs(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiFetchPage<AuditLog>(`/audit/${query}`);
}
