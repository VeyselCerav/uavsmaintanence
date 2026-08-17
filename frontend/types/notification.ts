export type AppNotificationType =
  | "MAINTENANCE_APPROACHING"
  | "MAINTENANCE_DUE"
  | "MAINTENANCE_OVERDUE"
  | "CRITICAL_COMPONENT"
  | "LOW_STOCK"
  | "WORK_ORDER_ASSIGNED"
  | "WORK_ORDER_COMPLETED";

export type AppNotification = {
  id: string;
  type: AppNotificationType;
  title_key: string;
  body_key: string;
  payload: {
    due_id?: string;
    uav_id?: string;
    uav_registration?: string;
    task_code?: string;
    task_name?: string;
    status?: string;
    usage_percent?: string;
    component_serial?: string;
    work_order_id?: string;
    work_order_number?: string;
    assigned_name?: string;
  };
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};
