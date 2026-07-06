// Factory status API calls

import { apiFetch } from "./client";
import type { FactoryStatus, MachineInfo } from "../types";

export function getFactoryStatus(): Promise<FactoryStatus> {
  return apiFetch<FactoryStatus>("/factory/status");
}

export function getStationMachines(stationId: string): Promise<MachineInfo[]> {
  return apiFetch<MachineInfo[]>(`/factory/stations/${stationId}/machines`);
}

export function getMachineInfo(machineId: string): Promise<MachineInfo> {
  return apiFetch<MachineInfo>(`/factory/machines/${machineId}`);
}
