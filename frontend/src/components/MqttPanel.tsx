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
  const [brokerX, setBrokerX] = useState(200);
  const [brokerY, setBrokerY] = useState(100);

  const { data: stats } = useQuery({
    queryKey: ["mqtt-stats"],
    queryFn: () => api.get("/mqtt/stats").then(r => r.data),
    refetchInterval: 1000
  });
  
  const { data: topics } = useQuery({
    queryKey: ["mqtt-topics"],
    queryFn: () => api.get("/mqtt/topics").then(r => r.data),
    refetchInterval: 1000
  });
  
  const { data: reconnections } = useQuery({
    queryKey: ["mqtt-reconnections"],
    queryFn: () => api.get("/mqtt/reconnections").then(r => r.data),
    refetchInterval: 500
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
      qc.invalidateQueries({ queryKey: ["mqtt-stats", "mqtt-topics"] });
    } catch (e: any) {
      setMsg(`Error: ${e?.message}`);
    }
  };
  
  const relocateBroker = async () => {
    try {
      const brokerIds = Object.keys(stats?.brokers || {});
      if (brokerIds.length === 0) {
        setMsg("No broker found");
        return;
      }
      const brokerId = Number(brokerIds[0]);
      const r = await api.post("/broker/relocate", null, {
        params: { broker_id: brokerId, x: brokerX, y: brokerY }
      });
      setMsg(`Broker relocated to (${brokerX}, ${brokerY})`);
      qc.invalidateQueries({ queryKey: ["nodes"] });
    } catch (e: any) {
      setMsg(`Error: ${e?.message}`);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-slate-700 bg-slate-900">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold">MQTT Protocol</h3>
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
                <div className="flex justify-between">
                  <span>Broker {id}</span>
                  <span className="text-amber-400">Queue: {s.queue_depth}</span>
                </div>
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
                <div>Pub={c.stats.messages_published} Rcv={c.stats.messages_received} Acks={c.stats.acks_sent}</div>
                {c.stats.reconnects > 0 && <div className="text-yellow-500">Reconnects={c.stats.reconnects}</div>}
                {c.latest_message && (
                  <div className="mt-1 text-cyan-300">
                    Latest: {c.latest_message.topic} = "{c.latest_message.payload}" (from node {c.latest_message.publisher_id})
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {topics && Object.keys(topics.topics || {}).length > 0 && (
          <div className="border-t border-slate-700 pt-2">
            <div className="text-xs text-slate-400 mb-1">Topic Heatmap</div>
            {Object.entries(topics.topics).map(([topic, count]: [string, any]) => {
              const maxCount = Math.max(...Object.values(topics.topics));
              const intensity = Math.min(100, (count / maxCount) * 100);
              return (
                <div key={topic} className="text-xs bg-slate-800 rounded p-2 mb-1">
                  <div className="flex justify-between items-center">
                    <span>{topic}</span>
                    <span className="text-cyan-400">{count} msgs</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded h-1 mt-1">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-1 rounded"
                      style={{ width: `${intensity}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
        
        {reconnections && reconnections.reconnections.length > 0 && (
          <div className="border-t border-slate-700 pt-2">
            <div className="text-xs text-slate-400 mb-1">Reconnection Wave</div>
            <div className="text-xs bg-slate-800 rounded p-2">
              {reconnections.reconnections.map(([nid, t]: [number, number]) => (
                <div key={`${nid}-${t}`} className="text-green-400">Node {nid} reconnected</div>
              ))}
            </div>
          </div>
        )}
        
        <div className="border-t border-slate-700 pt-2">
          <div className="text-xs text-slate-400 mb-1">Broker Failover</div>
          <div className="flex gap-2 mb-2">
            <input
              type="number"
              placeholder="X"
              className="w-16 bg-slate-800 rounded px-2 py-1 text-xs"
              value={brokerX}
              onChange={e => setBrokerX(Number(e.target.value))}
            />
            <input
              type="number"
              placeholder="Y"
              className="w-16 bg-slate-800 rounded px-2 py-1 text-xs"
              value={brokerY}
              onChange={e => setBrokerY(Number(e.target.value))}
            />
            <button
              onClick={relocateBroker}
              className="px-2 py-1 rounded bg-orange-600 hover:bg-orange-500 text-xs"
            >
              Relocate
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
