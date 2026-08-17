import { apiFetch, apiFetchPage } from "@/services/api";
import type { Flight, FlightWritePayload } from "@/types/flight";

export function listFlights(search = "", uavId = "") {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (uavId) params.set("uav", uavId);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetchPage<Flight>(`/flights/${query}`);
}

export function getFlight(id: string) {
  return apiFetch<Flight>(`/flights/${id}/`);
}

export function createFlight(payload: FlightWritePayload) {
  return apiFetch<Flight>("/flights/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function completeFlight(id: string) {
  return apiFetch<Flight>(`/flights/${id}/complete/`, { method: "POST" });
}
