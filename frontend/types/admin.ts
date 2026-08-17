export type Role = {
  id: string;
  code: string;
  name: string;
  description: string;
};

export type AccountUser = {
  id: string;
  email: string;
  full_name: string;
  locale: string;
  timezone: string;
  role: string;
  role_code: string;
  role_name: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
};

export type UserWritePayload = {
  email: string;
  full_name: string;
  password?: string;
  role: string;
  locale?: string;
  timezone?: string;
  is_active?: boolean;
};

export type SystemSetting = {
  key: string;
  value: unknown;
  description: string;
};

export type DueRulesValue = {
  approaching_percent: number;
  due_percent: number;
  overdue_percent: number;
  critical_percent: number;
};

export type RpnThresholdsValue = {
  low_max: number;
  medium_max: number;
  high_max: number;
};

export type AuditLog = {
  id: string;
  user: string | null;
  user_email: string;
  user_name: string;
  timestamp: string;
  ip: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  old_value: unknown;
  new_value: unknown;
  message: string;
};
