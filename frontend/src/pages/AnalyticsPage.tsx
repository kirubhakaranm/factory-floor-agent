function MetricCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="font-medium text-gray-800">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function OeeBar({ label, availability, performance, quality }: {
  label: string; availability: number; performance: number; quality: number;
}) {
  const oee = availability * performance * quality;
  return (
    <div className="flex items-center gap-3 py-2">
      <span className="w-24 text-sm text-gray-600 text-right">{label}</span>
      <div className="flex-1 flex gap-0.5 h-6 rounded overflow-hidden">
        <div className="bg-blue-400" style={{ width: `${availability * 100}%` }}
          title={`Availability: ${(availability * 100).toFixed(1)}%`} />
        <div className="bg-green-400" style={{ width: `${performance * 100 * 0.3}%` }}
          title={`Performance: ${(performance * 100).toFixed(1)}%`} />
        <div className="bg-yellow-400" style={{ width: `${quality * 100 * 0.2}%` }}
          title={`Quality: ${(quality * 100).toFixed(1)}%`} />
      </div>
      <span className={`w-16 text-sm font-semibold text-right ${oee >= 0.75 ? "text-green-600" : oee >= 0.6 ? "text-yellow-600" : "text-red-600"}`}>
        {(oee * 100).toFixed(1)}%
      </span>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">Analytics</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* OEE by Stage */}
        <MetricCard title="OEE by Stage (Last 30 Days)">
          <div className="space-y-1">
            <div className="flex items-center gap-3 pb-2 border-b text-xs text-gray-400">
              <span className="w-24 text-right">Stage</span>
              <div className="flex-1 flex gap-4">
                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-400 rounded" />Avail</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-400 rounded" />Perf</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-400 rounded" />Quality</span>
              </div>
              <span className="w-16 text-right">OEE</span>
            </div>
            <OeeBar label="Stamping" availability={0.96} performance={0.92} quality={0.97} />
            <OeeBar label="Welding" availability={0.93} performance={0.89} quality={0.95} />
            <OeeBar label="Paint" availability={0.91} performance={0.87} quality={0.93} />
            <OeeBar label="Assembly" availability={0.95} performance={0.91} quality={0.96} />
            <OeeBar label="Quality" availability={0.98} performance={0.95} quality={0.99} />
          </div>
          <p className="text-xs text-gray-400 mt-3">Live data with recharts visualization in production</p>
        </MetricCard>

        {/* Failure Pareto */}
        <MetricCard title="Top Failure Modes (Last 30 Days)">
          <div className="space-y-2">
            {[
              { mode: "Tool Wear Failure (TWF)", count: 12, pct: 35 },
              { mode: "Heat Dissipation (HDF)", count: 8, pct: 24 },
              { mode: "Overstrain (OSF)", count: 6, pct: 18 },
              { mode: "Power Failure (PWF)", count: 5, pct: 15 },
              { mode: "Random Failure (RNF)", count: 3, pct: 9 },
            ].map((f) => (
              <div key={f.mode} className="flex items-center gap-3">
                <span className="w-48 text-sm text-gray-600 truncate">{f.mode}</span>
                <div className="flex-1 h-5 bg-gray-100 rounded overflow-hidden">
                  <div className="h-full bg-red-400 rounded" style={{ width: `${f.pct}%` }} />
                </div>
                <span className="w-12 text-sm text-gray-800 text-right">{f.count}</span>
              </div>
            ))}
          </div>
        </MetricCard>

        {/* Process Capability */}
        <MetricCard title="Process Capability (Cpk Trend)">
          <div className="space-y-3">
            {[
              { param: "Panel Thickness (STP-01)", cpk: 1.45, status: "ok" as const },
              { param: "Weld Nugget Dia (WLD-01)", cpk: 1.28, status: "warn" as const },
              { param: "Paint Film DFT (PNT-02)", cpk: 1.52, status: "ok" as const },
              { param: "Torque Value (ASM-01)", cpk: 0.98, status: "critical" as const },
              { param: "Alignment Toe (QAT-01)", cpk: 1.67, status: "ok" as const },
            ].map((p) => (
              <div key={p.param} className="flex items-center gap-3">
                <span className="w-48 text-sm text-gray-600 truncate">{p.param}</span>
                <div className="flex-1 flex items-center gap-2">
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${p.status === "ok" ? "bg-green-500" : p.status === "warn" ? "bg-yellow-500" : "bg-red-500"}`}
                      style={{ width: `${Math.min(100, (p.cpk / 2) * 100)}%` }}
                    />
                  </div>
                </div>
                <span className={`w-12 text-sm font-semibold text-right ${p.status === "ok" ? "text-green-600" : p.status === "warn" ? "text-yellow-600" : "text-red-600"}`}>
                  {p.cpk.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-400">
            <span>Target: Cpk &ge; 1.33</span>
            <span>Warning: 1.00-1.33</span>
            <span>Critical: &lt; 1.00</span>
          </div>
        </MetricCard>

        {/* Reliability */}
        <MetricCard title="Equipment Reliability (MTBF / MTTR)">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2">Station</th>
                  <th className="pb-2 text-right">MTBF (hrs)</th>
                  <th className="pb-2 text-right">MTTR (hrs)</th>
                  <th className="pb-2 text-right">Avail %</th>
                </tr>
              </thead>
              <tbody className="text-gray-700">
                {[
                  { station: "STP-01-PRS", mtbf: 187, mttr: 3.2, avail: 98.3 },
                  { station: "STP-02-PRS", mtbf: 624, mttr: 1.1, avail: 99.8 },
                  { station: "WLD-01-UBD", mtbf: 412, mttr: 1.8, avail: 99.6 },
                  { station: "PNT-02-PRM", mtbf: 350, mttr: 2.1, avail: 99.4 },
                  { station: "ASM-01-PWR", mtbf: 540, mttr: 1.4, avail: 99.7 },
                ].map((r) => (
                  <tr key={r.station} className="border-b border-gray-50">
                    <td className="py-2 font-mono text-xs">{r.station}</td>
                    <td className={`py-2 text-right ${r.mtbf < 200 ? "text-red-600 font-semibold" : ""}`}>{r.mtbf}</td>
                    <td className={`py-2 text-right ${r.mttr > 3 ? "text-yellow-600 font-semibold" : ""}`}>{r.mttr}</td>
                    <td className="py-2 text-right">{r.avail}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </MetricCard>
      </div>
    </div>
  );
}
