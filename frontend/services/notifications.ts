import { apiFetch, apiFetchPage } from "@/services/api";
import type { AppNotification } from "@/types/notification";

export function listNotifications(unread = false) {
  const query = unread ? "?unread=true&page_size=20" : "?page_size=20";
  return apiFetchPage<AppNotification>(`/notifications/${query}`);
}

export function getUnreadCount() {
  return apiFetch<{ unread: number }>("/notifications/unread-count/");
}

export function markNotificationRead(id: string) {
  return apiFetch<AppNotification>(`/notifications/${id}/read/`, { method: "POST" });
}

export function markAllNotificationsRead() {
  return apiFetch<{ updated: number }>("/notifications/read-all/", { method: "POST" });
}
