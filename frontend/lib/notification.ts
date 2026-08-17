import type { AppNotification } from "@/types/notification";

export function notificationMeta(item: AppNotification): string {
  if (item.type === "WORK_ORDER_ASSIGNED" || item.type === "WORK_ORDER_COMPLETED") {
    return [item.payload.work_order_number, item.payload.uav_registration, item.payload.task_code]
      .filter(Boolean)
      .join(" · ");
  }
  const parts = [item.payload.uav_registration, item.payload.task_code, item.payload.task_name].filter(Boolean);
  if (item.payload.usage_percent) {
    parts.push(`${item.payload.usage_percent}%`);
  }
  return parts.join(" · ");
}

export function notificationHref(item: AppNotification): string | null {
  if (item.payload.work_order_id) {
    return `/work-orders/${item.payload.work_order_id}`;
  }
  if (item.payload.uav_id) {
    return `/uavs/${item.payload.uav_id}`;
  }
  return null;
}
