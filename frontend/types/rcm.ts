import type { RCMStrategy } from "@/types/maintenance";

export type RCMStatus = "DRAFT" | "IN_REVIEW" | "APPROVED" | "ARCHIVED";
export type Detectability = "LOW" | "MEDIUM" | "HIGH";

export const RCM_STATUSES: RCMStatus[] = ["DRAFT", "IN_REVIEW", "APPROVED", "ARCHIVED"];
export const DETECTABILITIES: Detectability[] = ["LOW", "MEDIUM", "HIGH"];

export type RCMItem = {
  id: string;
  analysis: string;
  sequence: number;
  function: string;
  functional_failure: string;
  failure_mode: string;
  failure_effect: string;
  safety_effect: boolean;
  operational_effect: boolean;
  detectability: Detectability;
  preventive_feasible: boolean;
  suggested_strategy: RCMStrategy;
  strategy: RCMStrategy;
  is_overridden: boolean;
  rationale: string;
  fmea_item: string | null;
  fmea_item_function: string;
  grounded_warning: boolean;
  is_demo: boolean;
};

export type RCMAnalysis = {
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
  status: RCMStatus;
  revision: number;
  approved_at: string | null;
  approved_by: string | null;
  approved_by_name: string;
  notes: string;
  is_demo: boolean;
  item_count: number;
  items: RCMItem[];
};

export type RCMWritePayload = {
  code: string;
  title: string;
  uav_class: string;
  platform_type: string;
  component_type: string;
  mission_type?: string | null;
  notes?: string;
};

export type RCMItemWritePayload = {
  function: string;
  functional_failure: string;
  failure_mode: string;
  failure_effect?: string;
  safety_effect: boolean;
  operational_effect: boolean;
  detectability: Detectability;
  preventive_feasible: boolean;
  strategy?: RCMStrategy | "";
  rationale?: string;
  fmea_item?: string | null;
};

export type RCMApplyResult = {
  updated: number;
  strategy: RCMStrategy;
};
