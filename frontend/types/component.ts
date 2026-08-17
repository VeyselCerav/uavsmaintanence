export type ComponentStatus = "INSTALLED" | "REMOVED" | "QUARANTINE" | "SCRAPPED";

export type UAVComponent = {
  id: string;
  uav: string;
  uav_registration: string;
  component_type: string;
  component_type_code: string;
  component_type_name: string;
  name: string;
  serial_number: string;
  part_number: string;
  manufacturer: string;
  model: string;
  installed_at: string | null;
  removed_at: string | null;
  operating_hours: string;
  cycle_count: number;
  status: ComponentStatus;
  notes: string;
  is_demo: boolean;
};

export type ComponentInstallPayload = {
  uav: string;
  component_type: string;
  name?: string;
  serial_number?: string;
  part_number?: string;
  manufacturer?: string;
  model?: string;
  installed_at?: string;
  notes?: string;
};

export type ComponentRemovePayload = {
  status?: Exclude<ComponentStatus, "INSTALLED">;
  notes?: string;
};
