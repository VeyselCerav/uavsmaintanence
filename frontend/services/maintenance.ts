import { apiFetch, apiFetchPage } from "@/services/api";
import type { CatalogItem } from "@/types/uav";
import type {
  MaintenanceDue,
  MaintenanceRecord,
  MaintenanceTemplate,
  MaintenanceTemplateItem,
  TemplateItemWritePayload,
  TemplateWritePayload,
} from "@/types/maintenance";

export function listTemplates(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiFetchPage<MaintenanceTemplate>(`/maintenance-templates/${query}`);
}

export function getTemplate(id: string) {
  return apiFetch<MaintenanceTemplate>(`/maintenance-templates/${id}/`);
}

export function createTemplate(payload: TemplateWritePayload) {
  return apiFetch<MaintenanceTemplate>("/maintenance-templates/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTemplate(id: string, payload: Partial<TemplateWritePayload>) {
  return apiFetch<MaintenanceTemplate>(`/maintenance-templates/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createTemplateItem(templateId: string, payload: TemplateItemWritePayload) {
  return apiFetch<MaintenanceTemplateItem>(`/maintenance-templates/${templateId}/items/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteTemplateItem(templateId: string, itemId: string) {
  return apiFetch<{ deleted: boolean }>(`/maintenance-templates/${templateId}/items/${itemId}/`, {
    method: "DELETE",
  });
}

export function reorderTemplateItems(templateId: string, itemIds: string[]) {
  return apiFetch<MaintenanceTemplateItem[]>(`/maintenance-templates/${templateId}/items/reorder/`, {
    method: "POST",
    body: JSON.stringify({ item_ids: itemIds }),
  });
}

export function listComponentTypes() {
  return apiFetchPage<CatalogItem>("/component-types/?page_size=100");
}

export function listDues(uavId = "", status = "", search = "", dueFrom = "", dueTo = "") {
  const params = new URLSearchParams();
  if (uavId) params.set("uav", uavId);
  if (status) params.set("status", status);
  if (search) params.set("search", search);
  if (dueFrom) params.set("due_from", dueFrom);
  if (dueTo) params.set("due_to", dueTo);
  params.set("page_size", dueFrom || uavId ? "100" : "50");
  return apiFetchPage<MaintenanceDue>(`/maintenance-dues/?${params.toString()}`);
}

export function listRecords(search = "", uavId = "") {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (uavId) params.set("uav", uavId);
  params.set("page_size", "50");
  return apiFetchPage<MaintenanceRecord>(`/maintenance-records/?${params.toString()}`);
}
