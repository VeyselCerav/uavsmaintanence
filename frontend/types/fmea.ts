export type FMEAStatus = "DRAFT" | "IN_REVIEW" | "APPROVED" | "ARCHIVED";
export type RPNBand = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export const FMEA_STATUSES: FMEAStatus[] = ["DRAFT", "IN_REVIEW", "APPROVED", "ARCHIVED"];

export type FMEAItem = {
  id: string;
  fmea: string;
  sequence: number;
  function: string;
  functional_failure: string;
  failure_mode: string;
  catalog_mode: string | null;
  catalog_mode_code: string;
  catalog_mode_name: string;
  failure_cause: string;
  failure_effect: string;
  severity: number;
  occurrence: number;
  detection: number;
  rpn: number;
  rpn_band: RPNBand | null;
  existing_control: string;
  recommended_action: string;
  is_demo: boolean;
};

export type FMEA = {
  id: string;
  code: string;
  title: string;
  uav_class: string;
  uav_class_code: string;
  uav_class_name: string;
  platform_type: string;
  platform_code: string;
  platform_name: string;
  component_type: string;
  component_type_code: string;
  component_type_name: string;
  mission_type: string | null;
  mission_code: string;
  mission_name: string;
  status: FMEAStatus;
  revision: number;
  approved_at: string | null;
  approved_by: string | null;
  approved_by_name: string;
  notes: string;
  is_demo: boolean;
  item_count: number;
  max_rpn: number | null;
  rpn_band: RPNBand | null;
  items: FMEAItem[];
};

export type FMEAWritePayload = {
  code: string;
  title: string;
  uav_class: string;
  platform_type: string;
  component_type: string;
  mission_type?: string | null;
  notes?: string;
};

export type FMEAItemWritePayload = {
  function: string;
  functional_failure: string;
  failure_mode: string;
  catalog_mode?: string | null;
  failure_cause?: string;
  failure_effect?: string;
  severity: number;
  occurrence: number;
  detection: number;
  existing_control?: string;
  recommended_action?: string;
};
