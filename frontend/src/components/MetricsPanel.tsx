import { useQuery } from "@tanstack/react-query";
import { getMetrics } from "../api/endpoints";

export default function MetricsPanel() {
  const { data } = useQuery({ queryKey: ["metrics"], queryFn: getMetrics, refetchInterval: 500 });

  return (
    <div className="p-4 rounded-xl border border-slate-700 bg-slate-900">
      <h3 className="font-semibold mb-3">Metrics</h3>
      {!data ? <div className="text-slate-400">Waiting…</div> : (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="bg-slate-800 rounded p-2">Now: <b>{data.now.toFixed(1)}</b></div>
          <div className="bg-slate-800 rounded p-2">PDR: <b>{data.pdr.toFixed(2)}</b></div>
          <div className="bg-slate-800 rounded p-2">Delivered: <b>{data.delivered}</b></div>
          <div className="bg-slate-800 rounded p-2">Latency(ms): <b>{data.avgLatencyMs.toFixed(1)}</b></div>
          <div className="bg-slate-800 rounded p-2">Duplicates: <b>{data.duplicates}</b></div>
        </div>
      )}
    </div>
  );
}
