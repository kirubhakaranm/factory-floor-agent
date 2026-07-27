// PrimeEV Factory Floor Agent — TypeScript types

// ─── Chat ─────────────────────────────────────────────────────────────────────

export interface Citation {
  id: number;
  source_type: "rag";
  doc_type: string;
  doc_type_label: string;
  title: string;
  path: string;
  excerpt: string;
  station_id: string | null;
  relevance: number;
}

export interface ToolCall {
  tool: string;
  args: Record<string, unknown>;
  agent?: string;
}

export interface ToolTrace extends ToolCall {
  result_snippet?: string;
  latency_ms?: number;
  had_error?: boolean;
}

export interface UsageInfo {
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cost_usd: number;
  total_latency_ms: number;
  ttft_ms: number | null;
  tool_call_count: number;
  llm_reentry_count: number;
  context_tokens_used: number;
  tool_latency_ms: number;
}

export type ResponseMode = "detailed" | "concise" | "summarized";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  toolCalls?: ToolCall[];
  toolTrace?: ToolTrace[];
  citations?: Citation[];
  usage?: UsageInfo;
  timestamp: Date;
  responseMode?: ResponseMode;
  reformattedContent?: string;
  reformattedMode?: ResponseMode;
  activeView?: "original" | "reformatted";
  isReformatting?: boolean;
  followUps?: string[];
  isLoadingFollowUps?: boolean;
}

// ─── Factory ──────────────────────────────────────────────────────────────────

export interface StationStatus {
  station_id: string;
  name: string;
  stage: string;
  status: "running" | "degraded" | "down" | "idle";
  machine_count: number;
  active_alerts: number;
  oee: number | null;
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

export interface SensorReading {
  machine_id: string;
  sensor_type: string;
  latest_value: number;
  latest_time: string;
  unit: string;
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

// ─── Analytics ────────────────────────────────────────────────────────────────

export interface OeeStage {
  stage_code: string;
  stage_name: string;
  oee: number;
  availability: number;
  performance: number;
  quality: number;
  station_count: number;
}

export interface FailureMode {
  mode: string;
  count: number;
  pct: number;
}

export interface CpkEntry {
  station_id: string;
  parameter: string;
  cpk: number;
  cp: number;
  out_of_control_signals: number;
  trending_alert: boolean;
}

export interface ReliabilityStation {
  station_id: string;
  failure_count: number;
  mtbf_hrs: number;
  mttr_hrs: number;
  availability_pct: number;
}

// ─── VIN Tracker ──────────────────────────────────────────────────────────────

export interface VinRecord {
  vin_id: string;
  model_id: string;
  model_name: string;
  production_date: string;
  batch_id: string;
  status: string;
}

export interface VinBatch {
  batch_id: string;
  line_id: string;
  start_time: string;
  end_time: string;
  units_produced: number;
  units_passed: number;
  batch_yield_pct: number;
}

export interface VinFinishedGoods {
  completion_date: string;
  storage_location: string;
  ship_date: string | null;
}

export interface VinStationQuality {
  station_id: string;
  inspection_type: string;
  lot_size: number;
  sample_size: number;
  defects_found: number;
  disposition: string;
}

export interface VinHistory {
  vin: VinRecord;
  batch: VinBatch | null;
  finished_goods: VinFinishedGoods | null;
  station_quality_context: VinStationQuality[];
  note: string;
}

// ─── Stages ───────────────────────────────────────────────────────────────────

export const STAGES = [
  { code: "STP", name: "Stamping", color: "#6366F1" },
  { code: "WLD", name: "Welding", color: "#8B5CF6" },
  { code: "PNT", name: "Paint", color: "#A855F7" },
  { code: "ASM", name: "Assembly", color: "#0EA5E9" },
  { code: "QAT", name: "Quality", color: "#14B8A6" },
] as const;

export const STAGE_STATIONS: Record<string, string[]> = {
  STP: ["STP-01-PRS", "STP-02-PRS", "STP-03-TRM"],
  WLD: ["WLD-01-UBD", "WLD-02-SDP", "WLD-03-RCL"],
  PNT: ["PNT-01-ECT", "PNT-02-PRM", "PNT-03-CLR"],
  ASM: ["ASM-01-PWR", "ASM-02-INT", "ASM-03-FNL"],
  QAT: ["QAT-01-ALN", "QAT-02-WLT", "QAT-03-DYN"],
};
