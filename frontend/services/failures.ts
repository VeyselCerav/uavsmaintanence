import { apiFetch, apiFetchPage } from "@/services/api";
import type { Failure, FailureMode, FailureWritePayload } from "@/types/failure";

export function listFailures(search = "", status = "", uavId = "") {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (status) params.set("status", status);
  if (uavId) params.set("uav", uavId);
  if (uavId) params.set("page_size", "50");
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetchPage<Failure>(`/failures/${query}`);
}

export function getFailure(id: string) {
  return apiFetch<Failure>(`/failures/${id}/`);
}

export function createFailure(payload: FailureWritePayload) {
  return apiFetch<Failure>("/failures/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resolveFailure(id: string) {
  return apiFetch<Failure>(`/failures/${id}/resolve/`, { method: "POST" });
}

export function listFailureModes() {
  return apiFetchPage<FailureMode>("/failure-modes/");
}
