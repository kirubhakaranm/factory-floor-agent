import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import type { OeeStage, FailureMode, CpkEntry, ReliabilityStation } from "../types";
import {
  getOeeByStage, getFailurePareto, getCpkSummary, getReliabilitySummary,
} from "../api/analytics";
import type { OeeAnalytics, FailurePareto, CpkSummary, ReliabilitySummary } from "../api/analytics";

function MetricCard({ title, loading, children }: {
  title: string; loading?: boolean; children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="font-medium text-gray-800">{title}</h3>
      </div>
      <div className="p-4">
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-6 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        ) : children}
      </div>
    </div>
  );
}

function OeeRow({ stage }: { stage: OeeStage }) {
  const oee = stage.oee;
  const oeeColor = oee >= 0.75 ? "text-green-600" : oee >= 0.6 ? "text-yellow-600" : "text-red-600";
  const metrics = [
    { key: "avail", value: stage.availability, bar: "bg-indigo-500" },
    { key: "perf",  value: stage.performance,  bar: "bg-cyan-500" },
    { key: "qual",  value: stage.quality,       bar: "bg-amber-400" },
  ];
  return (
    <div className="py-1.5">
      <div className="flex items-center gap-3">
        <span className="w-24 text-sm text-gray-600 text-right shrink-0 truncate">{stage.stage_name}</span>
        <div className="flex-1 flex gap-2">
          {metrics.map(({ key, value, bar }) => (
            <div key={key} className="flex-1">
              <div className="text-right text-[10px] text-gray-400 mb-0.5 tabular-nums">
                {(value * 100).toFixed(1)}%
              </div>
              <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div className={`${bar} h-full rounded-full`} style={{ width: `${value * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
        <span className={`w-16 text-sm font-semibold text-right tabular-nums shrink-0 ${oeeColor}`}>
          {(oee * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

const FAILURE_LABELS: Record<string, string> = {
  TWF: "Tool Wear Failure",
  OSF: "Overstrain Failure",
  HDF: "Heat Dissipation Failure",
  PWF: "Power Failure",
  RNF: "Random Failure",
};

const PARETO_COLORS = ["#6366F1", "#8B5CF6", "#A855F7", "#0EA5E9", "#14B8A6", "#06B6D4", "#818CF8", "#C084FC"];

function FailureTooltip({ active, payload }: { active?: boolean; payload?: { payload: { code: string; count: number; pct: number } }[] }) {
  if (!active || !payload?.length) return null;
  const { code, count, pct } = payload[0].payload;
  return (
    <div className="bg-white border border-gray-200 rounded shadow-md px-3 py-2 text-sm">
      <div className="font-semibold text-gray-800 mb-1">{FAILURE_LABELS[code] ?? code}</div>
      <div className="text-gray-500 text-xs">{count} events · {pct.toFixed(1)}% of total</div>
    </div>
  );
}

function FailureParetoChart({ modes }: { modes: FailureMode[] }) {
  const data = modes.map((m) => ({
    name: FAILURE_LABELS[m.mode] ?? m.mode,
    code: m.mode,
    count: m.count,
    pct: m.pct,
  }));
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 32, top: 0, bottom: 0 }}>
        <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
        <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 11 }} />
        <Tooltip content={<FailureTooltip />} cursor={{ fill: "#f3f4f6" }} />
        <Bar dataKey="count" radius={[0, 3, 3, 0]} label={{ position: "right", fontSize: 11, fill: "#6b7280", formatter: (v: number) => `${v}` }}>
          {data.map((_, i) => <Cell key={i} fill={PARETO_COLORS[i % PARETO_COLORS.length]} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function cpkStatus(cpk: number): "ok" | "warn" | "critical" {
  if (cpk >= 1.33) return "ok";
  if (cpk >= 1.0) return "warn";
  return "critical";
}

function CpkRow({ entry }: { entry: CpkEntry }) {
  const status = cpkStatus(entry.cpk);
  const color = status === "ok" ? "bg-green-500" : status === "warn" ? "bg-yellow-500" : "bg-red-500";
  const textColor = status === "ok" ? "text-green-600" : status === "warn" ? "text-yellow-600" : "text-red-600";
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 text-xs text-gray-500 font-mono truncate" title={`${entry.station_id} · ${entry.parameter}`}>
        {entry.station_id}
      </span>
      <span className="w-24 text-xs text-gray-500 truncate">{entry.parameter}</span>
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(100, (entry.cpk / 2) * 100)}%` }} />
      </div>
      <span className={`w-12 text-sm font-semibold text-right tabular-nums ${textColor}`}>
        {entry.cpk.toFixed(2)}
      </span>
      {entry.trending_alert && <span className="text-xs text-orange-500">↓</span>}
    </div>
  );
}

export default function AnalyticsPage() {
  const [oeeData, setOeeData] = useState<OeeAnalytics | null>(null);
  const [paretoData, setParetoData] = useState<FailurePareto | null>(null);
  const [cpkData, setCpkData] = useState<CpkSummary | null>(null);
  const [reliabilityData, setReliabilityData] = useState<ReliabilitySummary | null>(null);
  const [loading, setLoading] = useState({ oee: true, pareto: true, cpk: true, reliability: true });

  useEffect(() => {
    getOeeByStage()
      .then((d) => { setOeeData(d); setLoading((p) => ({ ...p, oee: false })); })
      .catch(() => setLoading((p) => ({ ...p, oee: false })));
    getFailurePareto(30)
      .then((d) => { setParetoData(d); setLoading((p) => ({ ...p, pareto: false })); })
      .catch(() => setLoading((p) => ({ ...p, pareto: false })));
    getCpkSummary()
      .then((d) => { setCpkData(d); setLoading((p) => ({ ...p, cpk: false })); })
      .catch(() => setLoading((p) => ({ ...p, cpk: false })));
    getReliabilitySummary()
      .then((d) => { setReliabilityData(d); setLoading((p) => ({ ...p, reliability: false })); })
      .catch(() => setLoading((p) => ({ ...p, reliability: false })));
  }, []);

  const oeeStages: OeeStage[] = oeeData?.stages ?? [];
  const failureModes: FailureMode[] = paretoData?.failure_modes ?? [];
  const cpkEntries: CpkEntry[] = cpkData?.entries ?? [];
  const reliabilityStations: ReliabilityStation[] = reliabilityData?.stations ?? [];

  // Sort Cpk entries by cpk asc so worst are first
  const sortedCpk = [...cpkEntries].sort((a, b) => a.cpk - b.cpk).slice(0, 10);

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Analytics</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* OEE by Stage */}
        <MetricCard title="OEE by Stage (live)" loading={loading.oee}>
          {oeeStages.length === 0 ? (
            <p className="text-sm text-gray-400">No OEE data — ensure ClickHouse is populated.</p>
          ) : (
            <>
              <div className="space-y-1">
                <div className="flex items-center gap-3 pb-2 border-b text-xs text-gray-400">
                  <span className="w-24 text-right">Stage</span>
                  <div className="flex-1 flex gap-2">
                    <span className="flex-1 flex items-center gap-1"><span className="w-2.5 h-2.5 bg-indigo-500 rounded-sm inline-block" />Availability</span>
                    <span className="flex-1 flex items-center gap-1"><span className="w-2.5 h-2.5 bg-cyan-500 rounded-sm inline-block" />Performance</span>
                    <span className="flex-1 flex items-center gap-1"><span className="w-2.5 h-2.5 bg-amber-400 rounded-sm inline-block" />Quality</span>
                  </div>
                  <span className="w-16 text-right">OEE</span>
                </div>
                {oeeStages.map((s) => <OeeRow key={s.stage_code} stage={s} />)}
              </div>
              {oeeData?.as_of && (
                <p className="text-xs text-gray-400 mt-2">
                  As of {new Date(oeeData.as_of).toLocaleString()}
                </p>
              )}
            </>
          )}
        </MetricCard>

        {/* Failure Pareto */}
        <MetricCard title={`Top Failure Modes (last ${paretoData?.days_back ?? 30} days)`} loading={loading.pareto}>
          {failureModes.length === 0 ? (
            <p className="text-sm text-gray-400">No failure data available.</p>
          ) : (
            <>
              <FailureParetoChart modes={failureModes} />
              <p className="text-xs text-gray-400 mt-1">{paretoData?.total} total events</p>
            </>
          )}
        </MetricCard>

        {/* Process Capability */}
        <MetricCard title="Process Capability — worst Cpk (live)" loading={loading.cpk}>
          {sortedCpk.length === 0 ? (
            <p className="text-sm text-gray-400">No Cpk data — run Kafka consumer to populate.</p>
          ) : (
            <>
              <div className="space-y-3">
                {sortedCpk.map((e) => <CpkRow key={`${e.station_id}-${e.parameter}`} entry={e} />)}
              </div>
              <div className="flex gap-4 mt-3 text-xs text-gray-400">
                <span>Target: Cpk ≥ 1.33</span>
                <span>Warning: 1.00–1.33</span>
                <span>Critical: &lt; 1.00</span>
              </div>
            </>
          )}
        </MetricCard>

        {/* Reliability */}
        <MetricCard title="Equipment Reliability — MTBF / MTTR (live)" loading={loading.reliability}>
          {reliabilityStations.length === 0 ? (
            <p className="text-sm text-gray-400">No reliability data available.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2 text-xs">Station</th>
                    <th className="pb-2 text-right text-xs">MTBF (hrs)</th>
                    <th className="pb-2 text-right text-xs">MTTR (hrs)</th>
                    <th className="pb-2 text-right text-xs">Avail %</th>
                  </tr>
                </thead>
                <tbody className="text-gray-700">
                  {reliabilityStations.map((r) => (
                    <tr key={r.station_id} className="border-b border-gray-50">
                      <td className="py-2 font-mono text-xs">{r.station_id}</td>
                      <td className={`py-2 text-right tabular-nums ${r.mtbf_hrs < 200 ? "text-red-600 font-semibold" : ""}`}>
                        {r.mtbf_hrs.toFixed(0)}
                      </td>
                      <td className={`py-2 text-right tabular-nums ${r.mttr_hrs > 3 ? "text-yellow-600 font-semibold" : ""}`}>
                        {r.mttr_hrs.toFixed(1)}
                      </td>
                      <td className="py-2 text-right tabular-nums">{r.availability_pct.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </MetricCard>
      </div>
    </div>
  );
}
