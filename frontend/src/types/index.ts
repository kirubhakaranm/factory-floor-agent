// PrimeEV Factory Floor Agent — TypeScript types

// ─── Chat ─────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  toolCalls?: ToolCall[];
  confidence?: number;
  timestamp: Date;
}

export interface ToolCall {
  tool: string;
  args: Record<string, unknown>;
  agent?: string;
}

export interface ChatSSEEvent {
  event_type: "token" | "tool_call" | "tool_result" | "done" | "session" | "error";
  data: string;
  agent_name?: string;
  tool_name?: string;
}

// ─── Factory ──────────────────────────────────────────────────────────────────

export interface StationStatus {
  station_id: string;
  name: string;
  stage: string;
  status: "running" | "degraded" | "down" | "idle";
  machine_count: number;
  active_alerts: number;
}

export interface FactoryStatus {
  timestamp: string;
  stations: StationStatus[];
  total_machines: number;
  active_alerts: number;
  shift: string;
}

export interface MachineInfo {
  machine_id: string;
  station_id: string;
  machine_type: string;
  model: string;
  criticality: string;
  status: string;
}

// ─── Alerts ───────────────────────────────────────────────────────────────────

export interface Alert {
  alert_id: string;
  machine_id: string;
  station_id: string;
  alert_type: string;
  severity: "critical" | "major" | "minor";
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

// ─── Stages ───────────────────────────────────────────────────────────────────

export const STAGES = [
  { code: "STP", name: "Stamping", color: "#ef4444" },
  { code: "WLD", name: "Welding", color: "#f97316" },
  { code: "PNT", name: "Paint", color: "#eab308" },
  { code: "ASM", name: "Assembly", color: "#22c55e" },
  { code: "QAT", name: "Quality", color: "#3b82f6" },
] as const;

export const STAGE_STATIONS: Record<string, string[]> = {
  STP: ["STP-01-PRS", "STP-02-PRS", "STP-03-TRM"],
  WLD: ["WLD-01-UBD", "WLD-02-SDP", "WLD-03-RCL"],
  PNT: ["PNT-01-ECT", "PNT-02-PRM", "PNT-03-CLR"],
  ASM: ["ASM-01-PWR", "ASM-02-INT", "ASM-03-FNL"],
  QAT: ["QAT-01-ALN", "QAT-02-WLT", "QAT-03-DYN"],
};
