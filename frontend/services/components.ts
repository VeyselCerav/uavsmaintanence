import { apiFetch, apiFetchPage } from "@/services/api";
import type {
  ComponentInstallPayload,
  ComponentRemovePayload,
  UAVComponent,
} from "@/types/component";

export function listUAVComponents(uavId: string, status = "") {
  const params = new URLSearchParams({ uav: uavId, page_size: "100" });
  if (status) {
    params.set("status", status);
  }
  return apiFetchPage<UAVComponent>(`/components/?${params.toString()}`);
}

export function installUAVComponent(payload: ComponentInstallPayload) {
  return apiFetch<UAVComponent>("/components/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeUAVComponent(id: string, payload: ComponentRemovePayload = {}) {
  return apiFetch<UAVComponent>(`/components/${id}/remove/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
