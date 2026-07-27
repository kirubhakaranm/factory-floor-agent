// Factory status API calls

import { apiFetch } from "./client";
import type { FactoryStatus, MachineInfo, SensorReading, VinHistory } from "../types";

export function getFactoryStatus(): Promise<FactoryStatus> {
  return apiFetch<FactoryStatus>("/factory/status");
}

export function getStationMachines(stationId: string): Promise<MachineInfo[]> {
  return apiFetch<MachineInfo[]>(`/factory/stations/${stationId}/machines`);
}

export function getMachineInfo(machineId: string): Promise<MachineInfo> {
  return apiFetch<MachineInfo>(`/factory/machines/${machineId}`);
}

export function getStationSensors(stationId: string): Promise<SensorReading[]> {
  return apiFetch<SensorReading[]>(`/factory/stations/${stationId}/sensors`);
}

export function getVinHistory(vinId: string): Promise<VinHistory> {
  return apiFetch<VinHistory>(`/factory/vin/${encodeURIComponent(vinId)}`);
}
