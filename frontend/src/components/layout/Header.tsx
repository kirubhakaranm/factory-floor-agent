import { useEffect, useState } from "react";

export default function Header() {
  const [shift, setShift] = useState("Day");
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      setTime(now);
      const h = now.getHours();
      setShift(h >= 6 && h < 14 ? "Day" : h >= 14 && h < 22 ? "Swing" : "Night");
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-gray-800">Factory Floor Agent</h1>
        <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded-full">
          Production Active
        </span>
      </div>
      <div className="flex items-center gap-6 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-primeev-500" />
          <span>Shift: <strong>{shift}</strong></span>
        </div>
        <div>
          {time.toLocaleTimeString()} | {time.toLocaleDateString()}
        </div>
        <div className="flex items-center gap-1">
          <svg className="w-4 h-4 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>0 alerts</span>
        </div>
      </div>
    </header>
  );
}
