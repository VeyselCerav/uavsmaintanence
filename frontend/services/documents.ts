import { apiDownload, apiFetch, apiFetchPage } from "@/services/api";
import type { DocumentRecord, DocumentWritePayload } from "@/types/document";
import type { MaintenanceTemplate } from "@/types/maintenance";
import type { UAV } from "@/types/uav";
import type { WorkOrder } from "@/types/work-order";

export function listDocuments(search = "", filters: Record<string, string> = {}) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetchPage<DocumentRecord>(`/documents/${query}`);
}

function appendTarget(body: FormData, key: string, value?: string | null) {
  if (value) {
    body.append(key, value);
  }
}

export function createDocument(payload: DocumentWritePayload, file?: File | null) {
  if (file) {
    const body = new FormData();
    body.append("title", payload.title);
    body.append("document_type", payload.document_type);
    if (payload.notes) body.append("notes", payload.notes);
    appendTarget(body, "uav", payload.uav);
    appendTarget(body, "component", payload.component);
    appendTarget(body, "template", payload.template);
    appendTarget(body, "work_order", payload.work_order);
    body.append("file", file);
    return apiFetch<DocumentRecord>("/documents/", { method: "POST", body });
  }
  return apiFetch<DocumentRecord>("/documents/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteDocument(id: string) {
  return apiFetch<{ deleted: boolean }>(`/documents/${id}/`, { method: "DELETE" });
}

export function downloadDocument(id: string, fileName: string) {
  return apiDownload(`/documents/${id}/download/`, fileName);
}

export function listDocumentTargets() {
  return Promise.all([
    apiFetchPage<UAV>("/uavs/?page_size=100"),
    apiFetchPage<WorkOrder>("/work-orders/?page_size=100"),
    apiFetchPage<MaintenanceTemplate>("/maintenance-templates/?page_size=100"),
  ]);
}
