import { apiFetch } from "@/services/api";
import type { DashboardSummary } from "@/types/dashboard";

export function getDashboard() {
  return apiFetch<DashboardSummary>("/dashboard/");
}
