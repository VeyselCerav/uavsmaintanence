import { apiFetch, apiFetchPage } from "@/services/api";
import type {
  RCMAnalysis,
  RCMApplyResult,
  RCMItem,
  RCMItemWritePayload,
  RCMWritePayload,
} from "@/types/rcm";

export function listRCMs(search = "", uavId = "", status = "") {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (uavId) params.set("uav", uavId);
  if (status) params.set("status", status);
  if (uavId) params.set("page_size", "50");
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetchPage<RCMAnalysis>(`/rcm/${query}`);
}

export function getRCM(id: string) {
  return apiFetch<RCMAnalysis>(`/rcm/${id}/`);
}

export function createRCM(payload: RCMWritePayload) {
  return apiFetch<RCMAnalysis>("/rcm/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateRCM(id: string, payload: Partial<RCMWritePayload>) {
  return apiFetch<RCMAnalysis>(`/rcm/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function approveRCM(id: string) {
  return apiFetch<RCMAnalysis>(`/rcm/${id}/approve/`, { method: "POST" });
}

export function evaluateRCM(id: string) {
  return apiFetch<RCMAnalysis>(`/rcm/${id}/evaluate/`, { method: "POST" });
}

export function applyRCMToTemplate(id: string) {
  return apiFetch<RCMApplyResult>(`/rcm/${id}/apply-to-template/`, { method: "POST" });
}

export function createRCMItem(rcmId: string, payload: RCMItemWritePayload) {
  return apiFetch<RCMItem>(`/rcm/${rcmId}/items/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteRCMItem(rcmId: string, itemId: string) {
  return apiFetch<{ deleted: boolean }>(`/rcm/${rcmId}/items/${itemId}/`, {
    method: "DELETE",
  });
}
