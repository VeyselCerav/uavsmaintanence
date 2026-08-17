export type TechnicianStatus = "ACTIVE" | "INACTIVE";

export type TechnicianSkill = {
  id: string;
  skill_id: string;
  skill_code: string;
  skill_name: string;
  certified_at: string | null;
  expires_at: string | null;
};

export type TechnicianCertification = {
  id: string;
  name: string;
  issuer: string;
  issued_at: string | null;
  expires_at: string | null;
  document_id: string;
};

export type Technician = {
  id: string;
  user_id: string;
  employee_number: string;
  status: TechnicianStatus;
  notes: string;
  is_demo: boolean;
  email: string;
  full_name: string;
  role: string | null;
  skills?: TechnicianSkill[];
  certifications?: TechnicianCertification[];
};

export type TechnicianWritePayload = {
  employee_number: string;
  email: string;
  full_name: string;
  password: string;
  notes?: string;
  status?: TechnicianStatus;
};

export type Skill = {
  id: string;
  code: string;
  name: string;
  description: string;
  is_active: boolean;
  is_demo: boolean;
};
