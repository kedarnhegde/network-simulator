import { useState } from "react";
import { postTraffic } from "../api/endpoints";
import type { Phy } from "../api/types";

export default function TrafficForm() {
  const [src, setSrc] = useState(1);
  const [dst, setDst] = useState(2);
  const [n, setN] = useState(10);
  const [size, setSize] = useState(100);
  const [kind, setKind] = useState<Phy>("WiFi");
  const [msg, setMsg] = useState<string>("");

  const submit = async () => {
    setMsg("Sending…");
    try {
      const r = await postTraffic({ src, dst, n, size, kind });
      const enqueued = r.enqueued_ok || 0;
      setMsg(`OK: ${enqueued}/${n} packets enqueued`);
      
      // Only trigger packet visualization if packets were actually enqueued
      if (enqueued > 0) {
        console.log("Triggering packet visualization", { src, dst, n: enqueued, kind });
        if ((window as any).addPacket) {
          const numToShow = Math.min(enqueued, 5);
          for (let i = 0; i < numToShow; i++) {
            setTimeout(() => {
              console.log(`Adding packet ${i + 1}/${numToShow}`);
              (window as any).addPacket(src, dst, kind);
            }, i * 300);
          }
        } else {
          console.error("addPacket function not available");
        }
      } else {
        setMsg(`Failed: PHY mismatch or nodes out of range`);
      }
    } catch (e:any) {
      setMsg(`Error: ${e?.message ?? e}`);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-slate-700 bg-slate-900">
      <h3 className="font-semibold mb-3">Traffic</h3>
      <div className="grid grid-cols-3 gap-2 text-sm">
        <label>Src<input type="number" className="w-full bg-slate-800 rounded px-2 py-1" value={src} onChange={e=>setSrc(Number(e.target.value))}/></label>
        <label>Dst<input type="number" className="w-full bg-slate-800 rounded px-2 py-1" value={dst} onChange={e=>setDst(Number(e.target.value))}/></label>
        <label>N<input type="number" className="w-full bg-slate-800 rounded px-2 py-1" value={n} onChange={e=>setN(Number(e.target.value))}/></label>
        <label>Size<input type="number" className="w-full bg-slate-800 rounded px-2 py-1" value={size} onChange={e=>setSize(Number(e.target.value))}/></label>
        <label>PHY
          <select className="w-full bg-slate-800 rounded px-2 py-1" value={kind} onChange={e=>setKind(e.target.value as Phy)}>
            <option>WiFi</option><option>BLE</option>
          </select>
        </label>
      </div>
      <button onClick={submit} className="mt-3 px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-500">Send</button>
      <div className="mt-2 text-xs text-slate-400">⚠️ PHY must match source node's PHY type</div>
      {msg && <div className="text-xs text-slate-300 mt-2 break-all">{msg}</div>}
    </div>
  );
}
