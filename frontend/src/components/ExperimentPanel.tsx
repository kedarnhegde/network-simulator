import { useState } from "react";
import { api } from "../api/client";

export default function ExperimentPanel() {
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any>(null);

  const runDutyCycle = async () => {
    setRunning(true);
    setResults(null);
    try {
      const res = await api.post("/experiment/duty-cycle", {}, { timeout: 120000 });
      setResults({ type: "duty-cycle", data: res.data.results });
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
    setRunning(false);
  };

  const runPhyComparison = async () => {
    setRunning(true);
    setResults(null);
    try {
      const res = await api.post("/experiment/phy-comparison", {}, { timeout: 60000 });
      setResults({ type: "phy-comparison", data: res.data.results });
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
    setRunning(false);
  };

  return (
    <div className="p-4 rounded-xl border border-slate-700 bg-slate-900">
      <h3 className="font-semibold mb-3">Experiments</h3>
      
      <div className="space-y-3 text-sm">
        <button
          onClick={runDutyCycle}
          disabled={running}
          className="w-full px-3 py-2 rounded bg-purple-600 hover:bg-purple-500 disabled:bg-gray-600"
        >
          {running ? "Running..." : "E1: Duty Cycle Impact"}
        </button>
        
        <button
          onClick={runPhyComparison}
          disabled={running}
          className="w-full px-3 py-2 rounded bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-600"
        >
          {running ? "Running..." : "E2: BLE vs WiFi"}
        </button>

        {results && (
          <div className="border-t border-slate-700 pt-3 mt-3">
            <div className="text-xs text-slate-400 mb-2">Results</div>
            
            {results.type === "duty-cycle" && (
              <div className="space-y-2">
                {results.data.map((r: any) => (
                  <div key={r.sleep_ratio} className="bg-slate-800 rounded p-2 text-xs">
                    <div className="font-semibold">Sleep Ratio: {(r.sleep_ratio * 100).toFixed(0)}%</div>
                    <div>Energy: {r.avg_energy.toFixed(1)}%</div>
                    <div>Latency: {r.avg_latency_ms.toFixed(1)}ms</div>
                    <div>PDR: {r.pdr.toFixed(2)}</div>
                    <div>Delivered: {r.delivered}/{r.enqueued}</div>
                    <div>Time: {r.simulation_time.toFixed(1)}s</div>
                  </div>
                ))}
              </div>
            )}

            {results.type === "phy-comparison" && (
              <div className="space-y-2">
                {Object.entries(results.data).map(([phy, r]: [string, any]) => (
                  <div key={phy} className="bg-slate-800 rounded p-2 text-xs">
                    <div className="font-semibold">{phy}</div>
                    <div>Energy: {r.avg_energy.toFixed(1)}%</div>
                    <div>Latency: {r.avg_latency_ms.toFixed(1)}ms</div>
                    <div>PDR: {r.pdr.toFixed(2)}</div>
                    <div>Delivered: {r.delivered}/{r.enqueued}</div>
                    <div>Time: {r.simulation_time.toFixed(1)}s</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
