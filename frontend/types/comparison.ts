export type ComparisonArm = {
  approach: "STANDARD" | "CLASS_SPECIFIC";
  uav_count: number;
  template_count: number;
  template_item_count: number;
  due_counts: Record<string, number>;
  due_attention: number;
  due_overdue: number;
  due_alert: number;
  work_order_counts: Record<string, number>;
  work_order_open: number;
  cost_total: string;
  uavs: { id: string; registration_number: string }[];
  operating_hours: string;
  failure_count: number;
  repair_count: number;
  total_repair_hours: string;
  mtbf_hours: string | null;
  mttr_hours: string | null;
  availability: string | null;
  zero_failure_policy: string;
  is_lower_bound: boolean;
};

export type ApproachComparison = {
  filters: {
    uav_class_id: string | null;
    platform_type_id: string | null;
    mission_type_id: string | null;
    period_start: string | null;
    period_end: string | null;
  };
  is_demo: boolean;
  arms: ComparisonArm[];
};
