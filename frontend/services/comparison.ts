import { apiFetch } from "@/services/api";
import type { ApproachComparison } from "@/types/comparison";

export function getApproachComparison(params: {
  classId?: string;
  platformId?: string;
  missionId?: string;
  from?: string;
  to?: string;
}) {
  const search = new URLSearchParams();
  if (params.classId) search.set("class", params.classId);
  if (params.platformId) search.set("platform", params.platformId);
  if (params.missionId) search.set("mission", params.missionId);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  const query = search.toString();
  return apiFetch<ApproachComparison>(`/reports/comparison/${query ? `?${query}` : ""}`);
}
