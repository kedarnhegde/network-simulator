import { useQuery } from "@tanstack/react-query";
import { getRouting } from "../api/endpoints";

export default function RoutingPanel() {
  const { data } = useQuery({ queryKey: ["routing"], queryFn: getRouting, refetchInterval: 2000 });

  return (
    <div className="p-4 rounded-xl border border-slate-700 bg-slate-900">
      <h3 className="font-semibold mb-3">Routing Tables</h3>
      {!data ? <div className="text-slate-400">Waiting…</div> : (
        <div className="space-y-3 text-sm">
          {data.map(rt => (
            <div key={rt.nodeId} className="bg-slate-800 rounded p-2">
              <div className="font-semibold mb-1">Node {rt.nodeId}</div>
              {rt.routes.length === 0 ? <div className="text-slate-400">No routes</div> :
                <ul className="list-disc pl-5">
                  {rt.routes.map(r => (
                    <li key={`${r.dest}-${r.nextHop}`}>dest {r.dest} → nextHop {r.nextHop}</li>
                  ))}
                </ul>
              }
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
