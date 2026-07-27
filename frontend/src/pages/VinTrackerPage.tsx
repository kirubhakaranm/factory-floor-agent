import { useState } from "react";
import { STAGES } from "../types";
import type { VinHistory } from "../types";
import { getVinHistory } from "../api/factory";

const resultStyles: Record<string, string> = {
  pass: "bg-green-100 text-green-700 border-green-300",
  fail: "bg-red-100 text-red-700 border-red-300",
  rework: "bg-yellow-100 text-yellow-700 border-yellow-300",
  accept: "bg-green-100 text-green-700 border-green-300",
  reject: "bg-red-100 text-red-700 border-red-300",
  conditional: "bg-yellow-100 text-yellow-700 border-yellow-300",
};

export default function VinTrackerPage() {
  const [vinInput, setVinInput] = useState("PEF-SD100-26-000001");
  const [history, setHistory] = useState<VinHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = () => {
    const vin = vinInput.trim();
    if (!vin) return;
    setLoading(true);
    setError(null);
    setHistory(null);
    getVinHistory(vin)
      .then((data) => { setHistory(data); setLoading(false); })
      .catch((e) => {
        setLoading(false);
        setError(e?.message?.includes("404") ? `VIN ${vin} not found.` : "Service unavailable — ensure the API is running.");
      });
  };

  const stationQuality = history?.station_quality_context ?? [];
  const reworkCount = stationQuality.filter((s) => s.defects_found > 0).length;
  const totalDefects = stationQuality.reduce((sum, s) => sum + s.defects_found, 0);

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">VIN Tracker</h2>

      {/* Search */}
      <div className="flex gap-2 mb-6 max-w-lg">
        <input
          type="text"
          value={vinInput}
          onChange={(e) => setVinInput(e.target.value)}
          placeholder="Enter VIN (e.g., PEF-SD100-26-000001)"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primeev-500 text-sm font-mono"
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-4 py-2 bg-primeev-600 text-white rounded-lg hover:bg-primeev-700 text-sm font-medium disabled:opacity-50"
        >
          {loading ? "Tracing…" : "Trace"}
        </button>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {history && (
        <>
          {/* VIN Summary */}
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="text-lg font-mono font-semibold text-gray-800">{history.vin.vin_id}</span>
                <span className="ml-3 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {history.vin.model_id} {history.vin.model_name}
                </span>
              </div>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                history.vin.status === "shipped" ? "bg-green-100 text-green-700" :
                history.vin.status === "in_production" ? "bg-blue-100 text-blue-700" :
                "bg-gray-100 text-gray-700"
              }`}>
                {history.vin.status.toUpperCase().replace("_", " ")}
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Production Date:</span>{" "}
                <strong>{new Date(history.vin.production_date).toLocaleDateString()}</strong>
              </div>
              <div>
                <span className="text-gray-500">Batch:</span>{" "}
                <strong>{history.vin.batch_id}</strong>
              </div>
              <div>
                <span className="text-gray-500">Defects Found:</span>{" "}
                <strong className={totalDefects > 0 ? "text-yellow-600" : "text-green-600"}>{totalDefects}</strong>
              </div>
              <div>
                <span className="text-gray-500">Stations w/ Issues:</span>{" "}
                <strong className={reworkCount > 0 ? "text-yellow-600" : "text-green-600"}>{reworkCount}</strong>
              </div>
            </div>

            {/* Batch info */}
            {history.batch && (
              <div className="mt-3 pt-3 border-t border-gray-100 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Line:</span> <strong>{history.batch.line_id}</strong>
                </div>
                <div>
                  <span className="text-gray-500">Units Produced:</span> <strong>{history.batch.units_produced}</strong>
                </div>
                <div>
                  <span className="text-gray-500">Units Passed:</span> <strong>{history.batch.units_passed}</strong>
                </div>
                <div>
                  <span className="text-gray-500">Batch Yield:</span>{" "}
                  <strong className={Number(history.batch.batch_yield_pct) >= 95 ? "text-green-600" : "text-yellow-600"}>
                    {Number(history.batch.batch_yield_pct).toFixed(1)}%
                  </strong>
                </div>
              </div>
            )}

            {/* Finished goods */}
            {history.finished_goods && (
              <div className="mt-3 pt-3 border-t border-gray-100 flex gap-6 text-sm">
                <div>
                  <span className="text-gray-500">Storage:</span> <strong>{history.finished_goods.storage_location}</strong>
                </div>
                {history.finished_goods.ship_date && (
                  <div>
                    <span className="text-gray-500">Ship Date:</span>{" "}
                    <strong>{new Date(history.finished_goods.ship_date).toLocaleDateString()}</strong>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Station Quality Timeline */}
          {stationQuality.length > 0 && (
            <>
              <h3 className="text-lg font-medium text-gray-700 mb-3">Quality by Station</h3>
              <div className="relative mb-8">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
                <div className="space-y-3">
                  {stationQuality.map((sq, i) => {
                    const stageCode = sq.station_id.slice(0, 3);
                    const stage = STAGES.find((s) => s.code === stageCode);
                    const styleKey = sq.disposition.toLowerCase();
                    const style = resultStyles[styleKey] || "bg-gray-100 text-gray-600 border-gray-300";
                    return (
                      <div key={i} className="relative flex items-start gap-4 pl-10">
                        <div
                          className="absolute left-3 w-3 h-3 rounded-full border-2 bg-white"
                          style={{ borderColor: stage?.color || "#999", top: "0.4rem" }}
                        />
                        <div className={`flex-1 px-3 py-2 rounded-lg border text-sm ${style}`}>
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{sq.station_id}</span>
                            <span className="uppercase text-xs font-semibold">{sq.disposition}</span>
                          </div>
                          <div className="text-xs opacity-75 mt-0.5">
                            {sq.inspection_type} · lot {sq.lot_size}, sample {sq.sample_size}
                            {sq.defects_found > 0 && ` · ${sq.defects_found} defect${sq.defects_found > 1 ? "s" : ""}`}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {history.note && (
            <p className="text-xs text-gray-400">{history.note}</p>
          )}
        </>
      )}
    </div>
  );
}
