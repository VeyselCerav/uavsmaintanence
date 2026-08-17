export type WorkOrderStatus =
  | "OPEN"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "WAITING_PARTS"
  | "COMPLETED"
  | "CANCELLED";

export type MaintenanceType =
  | "PREVENTIVE"
  | "CORRECTIVE"
  | "SCHEDULED"
  | "UNSCHEDULED"
  | "INSPECTION"
  | "FUNCTIONAL_CHECK";

export type WorkOrder = {
  id: string;
  number: string;
  uav: string;
  uav_registration: string;
  component: string | null;
  component_name: string | null;
  component_serial: string | null;
  template_item: string | null;
  task_code: string | null;
  task_name: string | null;
  maintenance_type: MaintenanceType;
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: WorkOrderStatus;
  planned_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  assigned_technician: string | null;
  assigned_name: string | null;
  estimated_duration_minutes: number | null;
  findings: string;
  notes: string;
  is_demo: boolean;
};

export type Assignee = {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  employee_number: string;
  role: string | null;
};
