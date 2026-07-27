// Analytics API calls

import { apiFetch } from "./client";
import type { CpkEntry, FailureMode, OeeStage, ReliabilityStation } from "../types";

export interface OeeAnalytics {
  stages: OeeStage[];
  as_of: string;
}

export interface FailurePareto {
  failure_modes: FailureMode[];
  total: number;
  days_back: number;
}

export interface CpkSummary {
  entries: CpkEntry[];
}

export interface ReliabilitySummary {
  stations: ReliabilityStation[];
  days_back: number;
}

export function getOeeByStage(): Promise<OeeAnalytics> {
  return apiFetch<OeeAnalytics>("/analytics/oee");
}

export function getFailurePareto(daysBack = 30): Promise<FailurePareto> {
  return apiFetch<FailurePareto>(`/analytics/failures?days_back=${daysBack}`);
}

export function getCpkSummary(): Promise<CpkSummary> {
  return apiFetch<CpkSummary>("/analytics/cpk");
}

export function getReliabilitySummary(): Promise<ReliabilitySummary> {
  return apiFetch<ReliabilitySummary>("/analytics/reliability");
}
