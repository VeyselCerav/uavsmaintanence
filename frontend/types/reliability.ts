export type ReliabilityScope = "fleet" | "class" | "uav" | "component";

export type ReliabilityMetrics = {
  scope: ReliabilityScope;
  scope_id: string | null;
  scope_label: string;
  period_start: string | null;
  period_end: string | null;
  operating_hours: string;
  failure_count: number;
  repair_count: number;
  total_repair_hours: string;
  mtbf_hours: string | null;
  mttr_hours: string | null;
  availability: string | null;
  zero_failure_policy: "undefined" | "operating_time_as_lower_bound";
  is_lower_bound: boolean;
};
