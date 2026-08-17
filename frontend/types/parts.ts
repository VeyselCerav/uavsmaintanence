export type Currency = "TRY" | "USD" | "EUR" | "AZN";
export type PartStatus = "ACTIVE" | "INACTIVE";

export const CURRENCIES: Currency[] = ["TRY", "USD", "EUR", "AZN"];
export const PART_STATUSES: PartStatus[] = ["ACTIVE", "INACTIVE"];

export type PartCompatibility = {
  id: string;
  part: string;
  uav_class: string | null;
  uav_class_code: string;
  uav_class_name: string;
  platform_type: string | null;
  platform_code: string;
  platform_name: string;
  component_type: string;
  component_type_code: string;
  component_type_name: string;
  is_demo: boolean;
};

export type Part = {
  id: string;
  part_number: string;
  name: string;
  manufacturer: string;
  model: string;
  stock_qty: string;
  min_stock_qty: string;
  unit_cost: string;
  currency: Currency;
  supplier: string;
  location: string;
  status: PartStatus;
  notes: string;
  stock_low: boolean;
  is_demo: boolean;
  compatibilities: PartCompatibility[];
};

export type PartWritePayload = {
  part_number: string;
  name: string;
  manufacturer?: string;
  model?: string;
  stock_qty?: string;
  min_stock_qty?: string;
  unit_cost?: string;
  currency?: Currency;
  supplier?: string;
  location?: string;
  status?: PartStatus;
  notes?: string;
};

export type CostRecord = {
  id: string;
  work_order: string | null;
  work_order_number: string;
  uav: string;
  uav_registration: string;
  component: string | null;
  component_name: string;
  maintenance_type: string;
  part_cost: string;
  labor_cost: string;
  other_cost: string;
  total_cost: string;
  currency: Currency;
  occurred_at: string;
  notes: string;
  is_demo: boolean;
};

export type WorkOrderPart = {
  id: string;
  work_order: string;
  part: string;
  part_number: string;
  part_name: string;
  quantity: string;
  unit_cost: string;
  currency: Currency;
  line_cost: string;
};
