import { apiFetch, apiFetchPage } from "@/services/api";
import type { TimelineEvent } from "@/types/document";
import type { CatalogItem, UAV, UAVClass, UAVWritePayload } from "@/types/uav";

export function listUAVs(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiFetchPage<UAV>(`/uavs/${query}`);
}

export function getUAV(id: string) {
  return apiFetch<UAV>(`/uavs/${id}/`);
}

export function getUAVTimeline(id: string) {
  return apiFetch<TimelineEvent[]>(`/uavs/${id}/timeline/`);
}

export function createUAV(payload: UAVWritePayload) {
  return apiFetch<UAV>("/uavs/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateUAV(id: string, payload: UAVWritePayload) {
  return apiFetch<UAV>(`/uavs/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listClasses() {
  return apiFetchPage<UAVClass>("/uav-classes/?page_size=100");
}

export function listPlatforms() {
  return apiFetchPage<CatalogItem>("/platforms/?page_size=100");
}

export function listMissions() {
  return apiFetchPage<CatalogItem>("/missions/?page_size=100");
}

export function createCatalog(path: string, payload: { code: string; name: string; description?: string }) {
  return apiFetch<CatalogItem>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
