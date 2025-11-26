import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export default function MqttPanel() {
  const qc = useQueryClient();
  const [publisherId, setPublisherId] = useState(1);
  const [subscriberId, setSubscriberId] = useState(2);
  const [topic, setTopic] = useState("sensor/temperature");
  const [payload, setPayload] = useState("25.5");
  const [qos, setQos] = useState(0);
  const [msg, setMsg] = useState("");

  const { data: stats } = useQuery({
    queryKey: ["mqtt-stats"],
    queryFn: () => api.get("/mqtt/stats").then(r => r.data),
    refetchInterval: 1000
  });

  const subscribe = async () => {
    try {
      const r = await api.post("/mqtt/subscribe", null, {
        params: { client_id: subscriberId, topic, qos }
      });
      setMsg(`Subscribed: ${JSON.stringify(r.data)}`);
      qc.invalidateQueries({ queryKey: ["mqtt-stats"] });
    } catch (e: any) {
      setMsg(`Error: ${e?.message}`);
    }
  };

  const publish = async () => {
    try {
      const r = await api.post("/mqtt/publish", null, {
        params: { publisher_id: publisherId, topic, payload, qos, retained: false }
      });
      setMsg(`Published: ${JSON.stringify(r.data)}`);
      qc.invalidateQueries({ queryKey: ["mqtt-stats"] });
    } catch (e: any) {
      setMsg(`Error: ${e?.message}`);
    }
  };

  const resetMqtt = async () => {
    try {
      await api.post("/mqtt/reset");
      setMsg("MQTT reset complete");
      qc.invalidateQueries({ queryKey: ["mqtt-stats"] });
    } catch (e: any) {
      setMsg(`Error: ${e?.message}`);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-slate-700 bg-slate-900">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold">MQTT</h3>
        <button
          onClick={resetMqtt}
          className="text-xs px-2 py-1 rounded bg-red-600 hover:bg-red-500"
        >
          Reset
        </button>
      </div>
      
      <div className="space-y-3 text-sm">
        <div className="grid grid-cols-2 gap-2">
          <label>
            Topic
            <input
              type="text"
              className="w-full bg-slate-800 rounded px-2 py-1"
              value={topic}
              onChange={e => setTopic(e.target.value)}
            />
          </label>
          <label>
            QoS
            <select
              className="w-full bg-slate-800 rounded px-2 py-1"
              value={qos}
              onChange={e => setQos(Number(e.target.value))}
            >
              <option value={0}>0 (Fire & Forget)</option>
              <option value={1}>1 (At Least Once)</option>
            </select>
          </label>
        </div>

        <div className="border-t border-slate-700 pt-2">
          <div className="text-xs text-slate-400 mb-1">Subscribe</div>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Subscriber ID"
              className="w-24 bg-slate-800 rounded px-2 py-1"
              value={subscriberId}
              onChange={e => setSubscriberId(Number(e.target.value))}
            />
            <button
              onClick={subscribe}
              className="px-3 py-1 rounded bg-green-600 hover:bg-green-500"
            >
              Subscribe
            </button>
          </div>
        </div>

        <div className="border-t border-slate-700 pt-2">
          <div className="text-xs text-slate-400 mb-1">Publish</div>
          <div className="flex gap-2 mb-2">
            <input
              type="number"
              placeholder="Publisher ID"
              className="w-24 bg-slate-800 rounded px-2 py-1"
              value={publisherId}
              onChange={e => setPublisherId(Number(e.target.value))}
            />
            <input
              type="text"
              placeholder="Payload"
              className="flex-1 bg-slate-800 rounded px-2 py-1"
              value={payload}
              onChange={e => setPayload(e.target.value)}
            />
          </div>
          <button
            onClick={publish}
            className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-500"
          >
            Publish
          </button>
        </div>

        {msg && <div className="text-xs text-slate-300 break-all">{msg}</div>}

        {stats && (
          <div className="border-t border-slate-700 pt-2">
            <div className="text-xs text-slate-400 mb-1">Broker Stats</div>
            {Object.entries(stats.brokers || {}).map(([id, s]: [string, any]) => (
              <div key={id} className="text-xs bg-slate-800 rounded p-2 mb-1">
                <div>Broker {id}: Queue={s.queue_depth}</div>
                <div>Received={s.messages_received} Delivered={s.messages_delivered}</div>
                <div>QoS0={s.qos0_messages} QoS1={s.qos1_messages} DUPs={s.duplicates_sent}</div>
              </div>
            ))}
            
            <div className="text-xs text-slate-400 mt-2 mb-1">Client Stats</div>
            {Object.entries(stats.clients || {}).map(([id, c]: [string, any]) => (
              <div key={id} className="text-xs bg-slate-800 rounded p-2 mb-1">
                <div className="flex items-center gap-2">
                  <span className={c.connected ? "text-green-500" : "text-red-500"}>●</span>
                  <span>{c.role} {id}</span>
                </div>
                <div>Topics={c.subscribed_topics.join(", ") || "none"}</div>
                <div>Pub={c.stats.messages_published} Rcv={c.stats.messages_received} DUPs={c.stats.duplicates_received}</div>
                {c.stats.reconnects > 0 && <div className="text-yellow-500">Reconnects={c.stats.reconnects}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
