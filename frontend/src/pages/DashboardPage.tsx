import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { STAGES, STAGE_STATIONS } from "../types";
import type { FactoryStatus, StationStatus } from "../types";
import { getFactoryStatus } from "../api/factory";

const statusColors: Record<string, string> = {
  running: "bg-green-500",
  degraded: "bg-yellow-500",
  down: "bg-red-500",
  idle: "bg-gray-400",
};

function StationCard({ station }: { station: StationStatus }) {
  return (
    <Link
      to={`/station?id=${station.station_id}`}
      className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-50 transition-colors"
    >
      <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${statusColors[station.status] || "bg-gray-400"}`} />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-800 truncate">{station.name}</div>
        <div className="text-xs text-gray-500">{station.station_id}</div>
      </div>
      <div className="text-right flex-shrink-0">
        {station.oee != null && (
          <div className={`text-xs font-semibold tabular-nums ${station.oee >= 0.75 ? "text-green-600" : station.oee >= 0.60 ? "text-yellow-600" : "text-red-600"}`}>
            {(station.oee * 100).toFixed(1)}%
          </div>
        )}
        {station.active_alerts > 0 && (
          <div className="text-xs text-red-500">{station.active_alerts} alert{station.active_alerts > 1 ? "s" : ""}</div>
        )}
      </div>
    </Link>
  );
}

function KpiCard({ label, value, unit, sub, loading }: {
  label: string; value: string; unit: string; sub?: string; loading?: boolean;
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      {loading ? (
        <div className="h-8 w-20 bg-gray-100 rounded animate-pulse" />
      ) : (
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-gray-900 tabular-nums">{value}</span>
          <span className="text-sm text-gray-500">{unit}</span>
        </div>
      )}
      {sub && !loading && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const [factory, setFactory] = useState<FactoryStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = () =>
      getFactoryStatus()
        .then((data) => { setFactory(data); setLoading(false); })
        .catch(() => setLoading(false));
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, []);

  const stationMap = new Map<string, StationStatus>();
  factory?.stations.forEach((s) => stationMap.set(s.station_id, s));

  // Derive KPIs from live factory status
  const stationsWithOee = factory?.stations.filter((s) => s.oee != null) ?? [];
  const avgOee = stationsWithOee.length
    ? stationsWithOee.reduce((sum, s) => sum + (s.oee ?? 0), 0) / stationsWithOee.length
    : null;
  const downCount = factory?.stations.filter((s) => s.status === "down").length ?? 0;
  const degradedCount = factory?.stations.filter((s) => s.status === "degraded").length ?? 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-800">Factory Overview</h2>
        {factory && (
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full font-medium">{factory.shift} Shift</span>
            <span>{new Date(factory.timestamp).toLocaleTimeString()}</span>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard
          label="Overall OEE"
          value={avgOee != null ? (avgOee * 100).toFixed(1) : "—"}
          unit="%"
          sub={stationsWithOee.length > 0 ? `across ${stationsWithOee.length} stations` : "no data"}
          loading={loading}
        />
        <KpiCard
          label="Active Alerts"
          value={String(factory?.active_alerts ?? 0)}
          unit=""
          sub="last 24 hours"
          loading={loading}
        />
        <KpiCard
          label="Stations Down"
          value={String(downCount)}
          unit=""
          sub={degradedCount > 0 ? `${degradedCount} degraded` : "all others operational"}
          loading={loading}
        />
        <KpiCard
          label="Total Machines"
          value={String(factory?.total_machines ?? "—")}
          unit=""
          sub="across 15 stations"
          loading={loading}
        />
      </div>

      {/* Stage Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {STAGES.map((stage) => (
          <div key={stage.code} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b" style={{ borderBottomColor: stage.color, borderBottomWidth: 3 }}>
              <h3 className="font-semibold text-gray-800">{stage.name}</h3>
              <span className="text-xs text-gray-500">{stage.code}</span>
            </div>
            <div className="p-2 space-y-0.5">
              {loading
                ? Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-10 bg-gray-50 rounded animate-pulse mx-1" />
                  ))
                : STAGE_STATIONS[stage.code]?.map((stationId) => {
                    const station = stationMap.get(stationId);
                    return station ? (
                      <StationCard key={stationId} station={station} />
                    ) : (
                      <div key={stationId} className="px-3 py-2 text-sm text-gray-400">{stationId}</div>
                    );
                  })}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 mt-4 text-gray-400 text-sm">
        {STAGES.map((stage, i) => (
          <span key={stage.code} className="flex items-center gap-2">
            <span className="font-medium" style={{ color: stage.color }}>{stage.name}</span>
            {i < STAGES.length - 1 && <span>→</span>}
          </span>
        ))}
      </div>
    </div>
  );
}
