// Alerts API calls

import { apiFetch } from "./client";
import type { Alert } from "../types";

interface AlertListResponse {
  alerts: Alert[];
  total: number;
}

export function getAlerts(stationId?: string, severity?: string): Promise<AlertListResponse> {
  const params = new URLSearchParams();
  if (stationId) params.set("station_id", stationId);
  if (severity) params.set("severity", severity);
  const query = params.toString() ? `?${params}` : "";
  return apiFetch<AlertListResponse>(`/alerts${query}`);
}
