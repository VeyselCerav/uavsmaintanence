import { apiFetch } from "@/services/api";
import type { DueRules } from "@/types/due-rules";

export function getDueRules() {
  return apiFetch<DueRules>("/maintenance-rules/");
}

export function updateDueRules(payload: DueRules) {
  return apiFetch<DueRules>("/maintenance-rules/", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
