export type FlightResult = "COMPLETED" | "ABORTED" | "TRAINING";

export type Flight = {
  id: string;
  flight_number: string;
  uav: string;
  uav_registration: string;
  operator: string | null;
  operator_name: string;
  mission_type: string;
  mission_code: string;
  mission_name: string;
  flown_on: string;
  start_at: string;
  end_at: string;
  duration_hours: string;
  result: FlightResult;
  notes: string;
  counters_applied: boolean;
  is_demo: boolean;
};

export type FlightWritePayload = {
  uav: string;
  start_at: string;
  end_at: string;
  duration_hours?: string | null;
  notes?: string;
};
