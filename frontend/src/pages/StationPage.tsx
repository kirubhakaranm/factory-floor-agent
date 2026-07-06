import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { STAGES, STAGE_STATIONS } from "../types";
import type { MachineInfo } from "../types";
import { getStationMachines } from "../api/factory";

const STATION_NAMES: Record<string, string> = {
  "STP-01-PRS": "Press 1", "STP-02-PRS": "Press 2", "STP-03-TRM": "Trim/Pierce",
  "WLD-01-UBD": "Underbody", "WLD-02-SDP": "Side Panel", "WLD-03-RCL": "Roof/Closure",
  "PNT-01-ECT": "E-Coat", "PNT-02-PRM": "Prime/Base", "PNT-03-CLR": "Clear/Cure",
  "ASM-01-PWR": "Powertrain", "ASM-02-INT": "Interior", "ASM-03-FNL": "Final Fit",
  "QAT-01-ALN": "Alignment", "QAT-02-WLT": "Water Leak", "QAT-03-DYN": "Dyno Test",
};

function SensorGauge({ label, value, unit, min, max, status }: {
  label: string; value: number; unit: string; min: number; max: number; status: "ok" | "warn" | "critical";
}) {
  const pct = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const barColor = status === "ok" ? "bg-green-500" : status === "warn" ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <div className="flex justify-between items-baseline mb-2">
        <span className="text-xs text-gray-500">{label}</span>
        <span className="text-sm font-semibold text-gray-800">{value} {unit}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

export default function StationPage() {
  const [params] = useSearchParams();
  const selectedId = params.get("id") || "STP-01-PRS";
  const [machines, setMachines] = useState<MachineInfo[]>([]);

  useEffect(() => {
    getStationMachines(selectedId).then(setMachines).catch(console.error);
  }, [selectedId]);

  const stationName = STATION_NAMES[selectedId] || selectedId;
  const stage = STAGES.find((s) => selectedId.startsWith(s.code));

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-2xl font-semibold text-gray-800">{stationName}</h2>
        <span className="text-sm text-gray-500">{selectedId}</span>
        {stage && (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full text-white" style={{ backgroundColor: stage.color }}>
            {stage.name}
          </span>
        )}
      </div>

      {/* Station Picker */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {Object.entries(STAGE_STATIONS).flatMap(([, stations]) =>
          stations.map((sid) => (
            <a
              key={sid}
              href={`/station?id=${sid}`}
              className={`px-3 py-1.5 text-xs rounded-full whitespace-nowrap ${
                sid === selectedId
                  ? "bg-primeev-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {STATION_NAMES[sid] || sid}
            </a>
          ))
        )}
      </div>

      {/* Sensor Gauges (sample data for layout) */}
      <div className="mb-8">
        <h3 className="text-lg font-medium text-gray-700 mb-3">Live Sensors</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SensorGauge label="Temperature" value={47.2} unit="°C" min={10} max={85} status="ok" />
          <SensorGauge label="Vibration" value={3.8} unit="mm/s" min={0} max={11} status="warn" />
          <SensorGauge label="Pressure" value={221} unit="bar" min={150} max={280} status="ok" />
          <SensorGauge label="Power Draw" value={89} unit="kW" min={0} max={160} status="ok" />
        </div>
        <p className="text-xs text-gray-400 mt-2">Live data requires Docker services running (Phase 7)</p>
      </div>

      {/* Machines */}
      <div className="mb-8">
        <h3 className="text-lg font-medium text-gray-700 mb-3">Machines ({machines.length})</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {machines.map((m) => (
            <div key={m.machine_id} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-800">{m.machine_id}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  m.criticality === "A" ? "bg-red-100 text-red-700" :
                  m.criticality === "B" ? "bg-yellow-100 text-yellow-700" :
                  "bg-gray-100 text-gray-600"
                }`}>
                  {m.criticality}
                </span>
              </div>
              <div className="text-sm text-gray-600">{m.model}</div>
              <div className="text-xs text-gray-400 mt-1">Type: {m.machine_type}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Placeholder sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-700 mb-2">Recent Failures</h3>
          <p className="text-sm text-gray-400">Connected to Postgres in production</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-700 mb-2">Quality Summary</h3>
          <p className="text-sm text-gray-400">Connected to Postgres in production</p>
        </div>
      </div>
    </div>
  );
}
