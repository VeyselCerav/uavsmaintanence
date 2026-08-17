import { apiFetch, apiFetchPage } from "@/services/api";
import type { FMEA, FMEAItem, FMEAItemWritePayload, FMEAWritePayload } from "@/types/fmea";

export function listFMEAs(search = "", uavId = "", status = "") {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (uavId) params.set("uav", uavId);
  if (status) params.set("status", status);
  if (uavId) params.set("page_size", "50");
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetchPage<FMEA>(`/fmea/${query}`);
}

export function getFMEA(id: string) {
  return apiFetch<FMEA>(`/fmea/${id}/`);
}

export function createFMEA(payload: FMEAWritePayload) {
  return apiFetch<FMEA>("/fmea/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateFMEA(id: string, payload: Partial<FMEAWritePayload>) {
  return apiFetch<FMEA>(`/fmea/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function approveFMEA(id: string) {
  return apiFetch<FMEA>(`/fmea/${id}/approve/`, { method: "POST" });
}

export function createFMEAItem(fmeaId: string, payload: FMEAItemWritePayload) {
  return apiFetch<FMEAItem>(`/fmea/${fmeaId}/items/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteFMEAItem(fmeaId: string, itemId: string) {
  return apiFetch<{ deleted: boolean }>(`/fmea/${fmeaId}/items/${itemId}/`, {
    method: "DELETE",
  });
}
