import { apiFetch } from "@/services/api";
import type { ReliabilityMetrics, ReliabilityScope } from "@/types/reliability";

export function getReliability(params: {
  scope?: ReliabilityScope;
  scopeId?: string;
  from?: string;
  to?: string;
}) {
  const search = new URLSearchParams();
  search.set("scope", params.scope ?? "fleet");
  if (params.scopeId) search.set("scope_id", params.scopeId);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  return apiFetch<ReliabilityMetrics>(`/reliability/?${search.toString()}`);
}
