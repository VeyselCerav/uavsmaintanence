export type DiscoveredDuring = "FLIGHT" | "INSPECTION" | "MAINTENANCE" | "OTHER";
export type FailureSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type FailureMode = {
  id: string;
  code: string;
  name: string;
  description: string;
  is_active: boolean;
  is_demo: boolean;
};

export type Failure = {
  id: string;
  uav: string;
  uav_registration: string;
  component: string | null;
  component_name: string;
  failure_mode: string | null;
  failure_mode_code: string;
  failure_mode_name: string;
  occurred_at: string;
  discovered_during: DiscoveredDuring;
  severity: FailureSeverity;
  description: string;
  downtime_hours: string;
  resolved_at: string | null;
  work_order: string | null;
  work_order_number: string;
  is_demo: boolean;
};

export type FailureWritePayload = {
  uav: string;
  occurred_at?: string;
  discovered_during: DiscoveredDuring;
  severity: FailureSeverity;
  failure_mode?: string | null;
  description: string;
  downtime_hours?: string | null;
};
