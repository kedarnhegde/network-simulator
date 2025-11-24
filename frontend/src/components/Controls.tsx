import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createNode, deleteNode, startSim, pauseSim, resetSim } from "../api/endpoints";
import type { Phy, Role } from "../api/types";

export default function Controls() {
  const qc = useQueryClient();
  const [role, setRole] = useState<Role>("sensor");
  const [phy, setPhy] = useState<Phy>("WiFi");
  const [x, setX] = useState<number>(100);
  const [y, setY] = useState<number>(100);

  const mCreate = useMutation({
    mutationFn: () => createNode({ role, phy, x, y }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["nodes"] }),
  });



  return (
    <div className="space-y-4">
      <div className="p-4 rounded-xl border border-slate-700 bg-slate-900">
        <h3 className="font-semibold mb-3">Add Node</h3>
        <div className="grid grid-cols-2 gap-2">
          <label className="text-sm">Role
            <select value={role} onChange={e=>setRole(e.target.value as Role)} className="w-full bg-slate-800 rounded px-2 py-1">
              <option>sensor</option>
              <option>broker</option>
              <option>subscriber</option>
              <option>publisher</option>
            </select>
          </label>
          <label className="text-sm">PHY
            <select value={phy} onChange={e=>setPhy(e.target.value as Phy)} className="w-full bg-slate-800 rounded px-2 py-1">
              <option>WiFi</option><option>BLE</option>
            </select>
          </label>
          <label className="text-sm">X
            <input type="number" value={x} onChange={e=>setX(Number(e.target.value))} className="w-full bg-slate-800 rounded px-2 py-1" />
          </label>
          <label className="text-sm">Y
            <input type="number" value={y} onChange={e=>setY(Number(e.target.value))} className="w-full bg-slate-800 rounded px-2 py-1" />
          </label>
        </div>
        <button onClick={()=>mCreate.mutate()} className="mt-3 px-3 py-1 rounded bg-blue-600 hover:bg-blue-500">Create</button>
        <div className="mt-2 text-xs text-slate-400">WiFi range: 55 units · BLE range: 15 units</div>
        <div className="mt-1 text-xs text-slate-500">Click node on canvas to delete</div>
      </div>

      <div className="p-4 rounded-xl border border-slate-700 bg-slate-900">
        <h3 className="font-semibold mb-3">Simulation</h3>
        <div className="flex gap-2">
          <button onClick={()=>startSim()} className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500">Start</button>
          <button onClick={()=>pauseSim()} className="px-3 py-1 rounded bg-amber-600 hover:bg-amber-500">Pause</button>
          <button onClick={async()=>{ await resetSim(); qc.invalidateQueries({queryKey:["nodes","metrics","routing"]}); }} className="px-3 py-1 rounded bg-slate-600 hover:bg-slate-500">Reset</button>
        </div>
      </div>
    </div>
  );
}
