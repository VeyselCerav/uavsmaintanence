export type UAVStatus = "READY" | "MAINTENANCE" | "GROUNDED" | "RETIRED";
export type MaintenanceApproach = "STANDARD" | "CLASS_SPECIFIC";

export type CatalogItem = {
  id: string;
  code: string;
  name: string;
  description: string;
  is_active: boolean;
  is_demo: boolean;
};

export type UAVClass = CatalogItem & {
  mtow_min_kg: string | null;
  mtow_max_kg: string | null;
  sort_order: number;
};

export type UAV = {
  id: string;
  registration_number: string;
  serial_number: string;
  manufacturer: string;
  model: string;
  uav_class: string;
  uav_class_code: string;
  uav_class_name: string;
  platform_type: string;
  platform_code: string;
  platform_name: string;
  mission_type: string;
  mission_code: string;
  mission_name: string;
  maintenance_template: string | null;
  template_code: string | null;
  template_name: string | null;
  maintenance_approach: MaintenanceApproach;
  mtow_kg: string | null;
  production_date: string | null;
  inventory_entry_date: string | null;
  total_flight_hours: string;
  total_flight_count: number;
  total_flight_cycles: number;
  status: UAVStatus;
  notes: string;
  is_demo: boolean;
};

export type UAVWritePayload = {
  registration_number: string;
  serial_number: string;
  manufacturer: string;
  model: string;
  uav_class: string;
  platform_type: string;
  mission_type: string;
  maintenance_approach: MaintenanceApproach;
  mtow_kg?: string | null;
  production_date?: string | null;
  inventory_entry_date?: string | null;
  status: UAVStatus;
  notes?: string;
};
