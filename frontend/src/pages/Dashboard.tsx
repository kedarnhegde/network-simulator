import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getNodes, deleteNode } from "../api/endpoints";
import TopologyCanvas from "../components/TopologyCanvas";
import Controls from "../components/Controls";
import MetricsPanel from "../components/MetricsPanel";
import RoutingPanel from "../components/RoutingPanel";
import TrafficForm from "../components/TrafficForm";
import MqttPanel from "../components/MqttPanel";
import ExperimentPanel from "../components/ExperimentPanel";

export default function Dashboard() {
  const { data: nodes } = useQuery({ queryKey: ["nodes"], queryFn: getNodes, refetchInterval: 1000 });
  const qc = useQueryClient();

  const handleDeleteNode = async (id: number) => {
    await deleteNode(id);
    qc.invalidateQueries({ queryKey: ["nodes"] });
  };

  return (
    <div className="p-4 max-w-[1280px] mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <img src="/logo.png" alt="Logo" className="w-10 h-10" />
        <h1 className="text-2xl font-bold">IoT/MQTT Network Simulator</h1>
      </div>
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-3 space-y-4">
          <Controls />
          <TrafficForm />
        </div>
        <div className="col-span-6">
          <TopologyCanvas nodes={nodes ?? []} onDeleteNode={handleDeleteNode} />
          <div className="mt-2 text-xs text-slate-400">
            <div>Roles: <span className="text-green-500">●</span> Sensor · <span className="text-amber-500">●</span> Subscriber · <span className="text-teal-500">●</span> Publisher · <span className="text-pink-500">●</span> Broker</div>
            <div>Packets: <span className="text-cyan-500">●</span> WiFi · <span className="text-yellow-500">●</span> BLE</div>
          </div>
        </div>
        <div className="col-span-3 space-y-4">
          <MetricsPanel />
          <MqttPanel />
          <ExperimentPanel />
          <RoutingPanel />
        </div>
      </div>
    </div>
  );
}
