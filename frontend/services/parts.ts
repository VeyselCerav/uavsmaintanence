import { apiFetch, apiFetchPage } from "@/services/api";
import type {
  CostRecord,
  Part,
  PartCompatibility,
  PartWritePayload,
  WorkOrderPart,
} from "@/types/parts";

export function listParts(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiFetchPage<Part>(`/parts/${query}`);
}

export function getPart(id: string) {
  return apiFetch<Part>(`/parts/${id}/`);
}

export function createPart(payload: PartWritePayload) {
  return apiFetch<Part>("/parts/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePart(id: string, payload: Partial<PartWritePayload>) {
  return apiFetch<Part>(`/parts/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createPartCompatibility(
  partId: string,
  payload: { uav_class?: string | null; platform_type?: string | null; component_type: string },
) {
  return apiFetch<PartCompatibility>(`/parts/${partId}/compatibility/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deletePartCompatibility(partId: string, rowId: string) {
  return apiFetch<{ deleted: boolean }>(`/parts/${partId}/compatibility/${rowId}/`, {
    method: "DELETE",
  });
}

export function listCosts(uavId = "", workOrderId = "") {
  const params = new URLSearchParams();
  if (uavId) params.set("uav", uavId);
  if (workOrderId) params.set("work_order", workOrderId);
  if (uavId || workOrderId) params.set("page_size", "50");
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetchPage<CostRecord>(`/costs/${query}`);
}

export function createCost(payload: {
  uav: string;
  work_order?: string | null;
  component?: string | null;
  part_cost?: string;
  labor_cost?: string;
  other_cost?: string;
  currency?: string;
  notes?: string;
}) {
  return apiFetch<CostRecord>("/costs/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCost(
  id: string,
  payload: { labor_cost?: string; other_cost?: string; notes?: string },
) {
  return apiFetch<CostRecord>(`/costs/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listWorkOrderParts(workOrderId: string) {
  return apiFetchPage<WorkOrderPart>(`/work-orders/${workOrderId}/parts/`);
}

export function createWorkOrderPart(workOrderId: string, payload: { part: string; quantity: string }) {
  return apiFetch<WorkOrderPart>(`/work-orders/${workOrderId}/parts/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteWorkOrderPart(workOrderId: string, lineId: string) {
  return apiFetch<{ deleted: boolean }>(`/work-orders/${workOrderId}/parts/${lineId}/`, {
    method: "DELETE",
  });
}
