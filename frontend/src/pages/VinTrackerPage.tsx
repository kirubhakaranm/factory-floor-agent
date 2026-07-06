import { useState } from "react";
import { STAGES } from "../types";

interface VinStage {
  stage: string;
  station: string;
  result: "pass" | "fail" | "rework" | "pending";
  timestamp: string;
  notes?: string;
}

const SAMPLE_VIN_HISTORY: VinStage[] = [
  { stage: "Stamping", station: "STP-01-PRS", result: "pass", timestamp: "06:12 AM" },
  { stage: "Stamping", station: "STP-02-PRS", result: "pass", timestamp: "06:18 AM" },
  { stage: "Stamping", station: "STP-03-TRM", result: "pass", timestamp: "06:24 AM" },
  { stage: "Welding", station: "WLD-01-UBD", result: "pass", timestamp: "06:42 AM" },
  { stage: "Welding", station: "WLD-02-SDP", result: "rework", timestamp: "07:05 AM", notes: "Weld spatter on B-pillar — 12 min rework" },
  { stage: "Welding", station: "WLD-03-RCL", result: "pass", timestamp: "07:28 AM" },
  { stage: "Paint", station: "PNT-01-ECT", result: "pass", timestamp: "08:15 AM" },
  { stage: "Paint", station: "PNT-02-PRM", result: "pass", timestamp: "08:45 AM" },
  { stage: "Paint", station: "PNT-03-CLR", result: "pass", timestamp: "09:30 AM" },
  { stage: "Assembly", station: "ASM-01-PWR", result: "pass", timestamp: "10:00 AM" },
  { stage: "Assembly", station: "ASM-02-INT", result: "pass", timestamp: "10:30 AM" },
  { stage: "Assembly", station: "ASM-03-FNL", result: "pass", timestamp: "11:00 AM" },
  { stage: "Quality", station: "QAT-01-ALN", result: "pass", timestamp: "11:15 AM" },
  { stage: "Quality", station: "QAT-02-WLT", result: "pass", timestamp: "11:25 AM" },
  { stage: "Quality", station: "QAT-03-DYN", result: "pass", timestamp: "11:45 AM" },
];

const resultStyles = {
  pass: "bg-green-100 text-green-700 border-green-300",
  fail: "bg-red-100 text-red-700 border-red-300",
  rework: "bg-yellow-100 text-yellow-700 border-yellow-300",
  pending: "bg-gray-100 text-gray-500 border-gray-300",
};

export default function VinTrackerPage() {
  const [vinInput, setVinInput] = useState("PEF-SD100-26-004521");
  const [showResults, setShowResults] = useState(false);

  const handleSearch = () => {
    if (vinInput.trim()) setShowResults(true);
  };

  const passCount = SAMPLE_VIN_HISTORY.filter((s) => s.result === "pass").length;
  const reworkCount = SAMPLE_VIN_HISTORY.filter((s) => s.result === "rework").length;
  const fpy = ((passCount / SAMPLE_VIN_HISTORY.length) * 100).toFixed(1);

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">VIN Tracker</h2>

      {/* Search */}
      <div className="flex gap-2 mb-6 max-w-lg">
        <input
          type="text"
          value={vinInput}
          onChange={(e) => setVinInput(e.target.value)}
          placeholder="Enter VIN (e.g., PEF-SD100-26-004521)"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primeev-500 text-sm font-mono"
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-primeev-600 text-white rounded-lg hover:bg-primeev-700 text-sm font-medium"
        >
          Trace
        </button>
      </div>

      {showResults && (
        <>
          {/* VIN Summary */}
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="text-lg font-mono font-semibold text-gray-800">{vinInput}</span>
                <span className="ml-3 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">PE-SD100 Sedan</span>
              </div>
              <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
                EOL PASS
              </span>
            </div>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div><span className="text-gray-500">Production Date:</span> <strong>2026-06-28</strong></div>
              <div><span className="text-gray-500">Batch:</span> <strong>B-000042</strong></div>
              <div><span className="text-gray-500">Stations Passed:</span> <strong>{passCount}/15</strong></div>
              <div><span className="text-gray-500">Rework Events:</span> <strong className="text-yellow-600">{reworkCount}</strong></div>
            </div>
            <div className="mt-2 text-sm">
              <span className="text-gray-500">Rolled Throughput Yield:</span>{" "}
              <strong className={Number(fpy) >= 95 ? "text-green-600" : "text-yellow-600"}>{fpy}%</strong>
            </div>
          </div>

          {/* Timeline */}
          <h3 className="text-lg font-medium text-gray-700 mb-3">Production Timeline</h3>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
            <div className="space-y-3">
              {SAMPLE_VIN_HISTORY.map((step, i) => {
                const stage = STAGES.find((s) => s.name === step.stage);
                return (
                  <div key={i} className="relative flex items-start gap-4 pl-10">
                    <div
                      className="absolute left-3 w-3 h-3 rounded-full border-2 bg-white"
                      style={{ borderColor: stage?.color || "#999", top: "0.35rem" }}
                    />
                    <div className={`flex-1 px-3 py-2 rounded-lg border text-sm ${resultStyles[step.result]}`}>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{step.station} — {step.stage}</span>
                        <span className="text-xs">{step.timestamp}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="uppercase text-xs font-semibold">{step.result}</span>
                        {step.notes && <span className="text-xs opacity-75">— {step.notes}</span>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
