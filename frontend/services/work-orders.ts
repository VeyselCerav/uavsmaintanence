import { apiFetch, apiFetchPage } from "@/services/api";
import type { Assignee, WorkOrder } from "@/types/work-order";

export function listWorkOrders(search = "", uavId = "", status = "") {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (uavId) params.set("uav", uavId);
  if (status) params.set("status", status);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetchPage<WorkOrder>(`/work-orders/${query}`);
}

export function getWorkOrder(id: string) {
  return apiFetch<WorkOrder>(`/work-orders/${id}/`);
}

export function createWorkOrderFromDue(dueId: string) {
  return apiFetch<WorkOrder>("/work-orders/", {
    method: "POST",
    body: JSON.stringify({ due: dueId }),
  });
}

export function assignWorkOrder(id: string, technicianId: string) {
  return apiFetch<WorkOrder>(`/work-orders/${id}/assign/`, {
    method: "POST",
    body: JSON.stringify({ assigned_technician: technicianId }),
  });
}

export function startWorkOrder(id: string) {
  return apiFetch<WorkOrder>(`/work-orders/${id}/start/`, { method: "POST" });
}

export function completeWorkOrder(id: string, findings = "") {
  return apiFetch<WorkOrder>(`/work-orders/${id}/complete/`, {
    method: "POST",
    body: JSON.stringify({ findings }),
  });
}

export function cancelWorkOrder(id: string) {
  return apiFetch<WorkOrder>(`/work-orders/${id}/cancel/`, { method: "POST" });
}

export function waitingPartsWorkOrder(id: string) {
  return apiFetch<WorkOrder>(`/work-orders/${id}/waiting-parts/`, { method: "POST" });
}

export function listAssignees() {
  return apiFetch<Assignee[]>("/work-orders/assignees/");
}
