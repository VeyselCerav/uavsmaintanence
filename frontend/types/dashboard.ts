import type { MaintenanceDue } from "@/types/maintenance";
import type { UAVStatus } from "@/types/uav";
import type { WorkOrder, WorkOrderStatus } from "@/types/work-order";

export type DashboardDueStatus = "APPROACHING" | "DUE" | "OVERDUE" | "CRITICAL";

export type DashboardSummary = {
  fleet: Record<UAVStatus, number> & { total: number };
  dues: {
    counts: Record<DashboardDueStatus, number> & { attention: number; overdue: number };
    items: MaintenanceDue[];
    overdue_items: MaintenanceDue[];
  };
  work_orders: {
    counts: Record<WorkOrderStatus, number> & { open: number };
    items: WorkOrder[];
  };
  reliability: {
    mtbf_hours: string | null;
    mttr_hours: string | null;
    availability: string | null;
    failure_count: number;
    is_lower_bound: boolean;
  };
};
