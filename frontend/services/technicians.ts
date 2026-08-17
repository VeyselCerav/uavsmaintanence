import { apiFetch, apiFetchPage } from "@/services/api";
import type {
  Skill,
  Technician,
  TechnicianCertification,
  TechnicianSkill,
  TechnicianWritePayload,
} from "@/types/technician";

export function listTechnicians(search = "") {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiFetchPage<Technician>(`/technicians/${query}`);
}

export function getTechnician(id: string) {
  return apiFetch<Technician>(`/technicians/${id}/`);
}

export function createTechnician(payload: TechnicianWritePayload) {
  return apiFetch<Technician>("/technicians/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTechnician(id: string, payload: Partial<TechnicianWritePayload> & { status?: string }) {
  return apiFetch<Technician>(`/technicians/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listSkills() {
  return apiFetchPage<Skill>("/skills/?page_size=100");
}

export function addTechnicianSkill(
  technicianId: string,
  payload: { skill: string; certified_at?: string; expires_at?: string },
) {
  return apiFetch<TechnicianSkill>(`/technicians/${technicianId}/skills/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteTechnicianSkill(technicianId: string, skillId: string) {
  return apiFetch<{ deleted: boolean }>(`/technicians/${technicianId}/skills/${skillId}/`, {
    method: "DELETE",
  });
}

export function addTechnicianCertification(
  technicianId: string,
  payload: {
    name: string;
    issuer: string;
    issued_at?: string;
    expires_at?: string;
    document_id?: string;
  },
) {
  return apiFetch<TechnicianCertification>(`/technicians/${technicianId}/certifications/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteTechnicianCertification(technicianId: string, certificationId: string) {
  return apiFetch<{ deleted: boolean }>(`/technicians/${technicianId}/certifications/${certificationId}/`, {
    method: "DELETE",
  });
}
