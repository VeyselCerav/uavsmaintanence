export type IntervalUnit =
  | "FLIGHT_HOURS"
  | "FLIGHT_CYCLES"
  | "COMPONENT_CYCLES"
  | "CALENDAR_DAYS"
  | "CALENDAR_MONTHS"
  | "CALENDAR_YEARS";

export type DueStatus = "NORMAL" | "APPROACHING" | "DUE" | "OVERDUE" | "CRITICAL";
export type Priority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type InspectionType =
  | "VISUAL"
  | "FUNCTIONAL"
  | "MEASUREMENT"
  | "OVERHAUL"
  | "REPLACEMENT"
  | "LUBRICATION"
  | "SOFTWARE";
export type RCMStrategy =
  | "SCHEDULED_INSPECTION"
  | "SCHEDULED_RESTORATION"
  | "SCHEDULED_DISCARD"
  | "CONDITION_INSPECTION"
  | "FUNCTIONAL_CHECK"
  | "CORRECTIVE";

export type MaintenanceTemplateItem = {
  id: string;
  template: string;
  component_type: string;
  component_type_code: string;
  component_type_name: string;
  sequence: number;
  task_code: string;
  task_name: string;
  interval_value: string;
  interval_unit: IntervalUnit;
  priority: Priority;
  estimated_duration_minutes: number;
  inspection_type: InspectionType;
  rcm_strategy: RCMStrategy;
  notes: string;
  is_demo: boolean;
};

export type MaintenanceTemplate = {
  id: string;
  code: string;
  name: string;
  description: string;
  uav_class: string;
  uav_class_code: string;
  uav_class_name: string;
  platform_type: string;
  platform_code: string;
  platform_name: string;
  mission_type: string;
  mission_code: string;
  mission_name: string;
  approach: "STANDARD" | "CLASS_SPECIFIC";
  is_active: boolean;
  is_demo: boolean;
  notes: string;
  item_count: number;
  items: MaintenanceTemplateItem[];
};

export type TemplateWritePayload = {
  code: string;
  name: string;
  description?: string;
  uav_class: string;
  platform_type: string;
  mission_type: string;
  approach: "STANDARD" | "CLASS_SPECIFIC";
  is_active: boolean;
  notes?: string;
};

export type TemplateItemWritePayload = {
  component_type: string;
  task_code: string;
  task_name: string;
  interval_value: string;
  interval_unit: IntervalUnit;
  priority: Priority;
  estimated_duration_minutes: number;
  inspection_type: InspectionType;
  rcm_strategy: RCMStrategy;
  notes?: string;
};

export type MaintenanceDue = {
  id: string;
  uav: string;
  uav_registration: string;
  component: string;
  component_name: string;
  component_serial: string;
  component_type_code: string;
  component_type_name: string;
  template_item: string;
  task_code: string;
  task_name: string;
  interval_value: string;
  interval_unit: IntervalUnit;
  inspection_type: InspectionType;
  status: DueStatus;
  remaining_value: string;
  remaining_unit: IntervalUnit;
  usage_percent: string;
  due_at: string | null;
  calculated_at: string;
  priority: Priority;
};

export type MaintenanceRecord = {
  id: string;
  work_order: string;
  work_order_number: string;
  uav: string;
  uav_registration: string;
  component: string | null;
  component_name: string | null;
  component_serial: string | null;
  maintenance_type: string;
  performed_at: string;
  technician: string | null;
  technician_name: string | null;
  description: string;
  findings: string;
  approach: "STANDARD" | "CLASS_SPECIFIC";
  operating_hours_snapshot: string;
  cycle_count_snapshot: number;
  uav_cycles_snapshot: number;
  task_code: string | null;
  task_name: string | null;
};

export const INTERVAL_UNITS: IntervalUnit[] = [
  "FLIGHT_HOURS",
  "FLIGHT_CYCLES",
  "COMPONENT_CYCLES",
  "CALENDAR_DAYS",
  "CALENDAR_MONTHS",
  "CALENDAR_YEARS",
];

export const PRIORITIES: Priority[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export const INSPECTION_TYPES: InspectionType[] = [
  "VISUAL",
  "FUNCTIONAL",
  "MEASUREMENT",
  "OVERHAUL",
  "REPLACEMENT",
  "LUBRICATION",
  "SOFTWARE",
];

export const RCM_STRATEGIES: RCMStrategy[] = [
  "SCHEDULED_INSPECTION",
  "SCHEDULED_RESTORATION",
  "SCHEDULED_DISCARD",
  "CONDITION_INSPECTION",
  "FUNCTIONAL_CHECK",
  "CORRECTIVE",
];
