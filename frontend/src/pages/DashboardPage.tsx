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
      <span className={`w-2.5 h-2.5 rounded-full ${statusColors[station.status] || "bg-gray-400"}`} />
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-800">{station.name}</div>
        <div className="text-xs text-gray-500">{station.station_id}</div>
      </div>
      <div className="text-xs text-gray-400">{station.machine_count} machines</div>
    </Link>
  );
}

function KpiCard({ label, value, unit, trend }: { label: string; value: string; unit: string; trend?: string }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        <span className="text-sm text-gray-500">{unit}</span>
      </div>
      {trend && <div className="text-xs text-green-600 mt-1">{trend}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const [factory, setFactory] = useState<FactoryStatus | null>(null);

  useEffect(() => {
    getFactoryStatus().then(setFactory).catch(console.error);
    const interval = setInterval(() => {
      getFactoryStatus().then(setFactory).catch(console.error);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const stationMap = new Map<string, StationStatus>();
  factory?.stations.forEach((s) => stationMap.set(s.station_id, s));

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Factory Overview</h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Overall OEE" value="78.3" unit="%" trend="+2.1% vs last week" />
        <KpiCard label="Active Alerts" value={String(factory?.active_alerts || 0)} unit="" />
        <KpiCard label="Today's Output" value="73" unit="units" trend="91% of target" />
        <KpiCard label="First Pass Yield" value="95.2" unit="%" />
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
              {STAGE_STATIONS[stage.code]?.map((stationId) => {
                const station = stationMap.get(stationId);
                return station ? (
                  <StationCard key={stationId} station={station} />
                ) : (
                  <div key={stationId} className="px-3 py-2 text-sm text-gray-400">
                    {stationId}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Flow Arrows */}
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
