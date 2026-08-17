export const DOCUMENT_TYPES = [
  "MANUAL",
  "PROCEDURE",
  "CERTIFICATE",
  "PHOTO",
  "REPORT",
  "OTHER",
] as const;

export type DocumentType = (typeof DOCUMENT_TYPES)[number];

export type DocumentRecord = {
  id: string;
  title: string;
  file_name: string;
  content_type: string;
  size_bytes: number;
  storage_key: string;
  document_type: DocumentType;
  uav: string | null;
  uav_registration: string;
  component: string | null;
  component_name: string;
  template: string | null;
  template_code: string;
  work_order: string | null;
  work_order_number: string;
  uploaded_by: string | null;
  uploaded_by_name: string;
  notes: string;
  is_demo: boolean;
  has_file: boolean;
  created_at: string;
};

export type DocumentWritePayload = {
  title: string;
  file_name?: string;
  content_type?: string;
  size_bytes?: number;
  storage_key?: string;
  document_type: DocumentType;
  uav?: string | null;
  component?: string | null;
  template?: string | null;
  work_order?: string | null;
  notes?: string;
};

export type TimelineEvent = {
  occurred_at: string;
  event_type: string;
  detail: string;
  entity_id: string | null;
};
