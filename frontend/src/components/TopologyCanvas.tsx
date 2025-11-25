import { useEffect, useRef, useState } from "react";
import type { NodeView, PacketInFlight } from "../api/types";

const ROLE_COLOR: Record<string, string> = {
  sensor: "#10b981",     // green-500
  subscriber: "#f59e0b", // amber-500
  publisher: "#14b8a6",  // teal-500
  broker: "#ec4899",     // pink-500
  mobile: "#8b5cf6"      // violet-500
};

const PHY_COLOR: Record<string, string> = {
  WiFi: "#06b6d4",  // cyan-500 (bright, visible)
  BLE: "#eab308",   // yellow-500 (bright)
};

type Props = { nodes: NodeView[]; width?: number; height?: number; onDeleteNode?: (id: number) => void; };

const SCALE = 3; // Scale factor to spread nodes visually

export default function TopologyCanvas({ nodes, width = 1200, height = 700, onDeleteNode }: Props) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  const [packets, setPackets] = useState<PacketInFlight[]>([]);
  const packetsRef = useRef<PacketInFlight[]>([]);
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; node: NodeView } | null>(null);

  useEffect(() => {
    packetsRef.current = packets;
  }, [packets]);

  const drawLines = (ctx: CanvasRenderingContext2D) => {
    const drawn = new Set<string>();
    for (const pkt of packetsRef.current) {
      const key = `${pkt.srcId}-${pkt.dstId}`;
      if (drawn.has(key)) continue;
      drawn.add(key);
      
      ctx.beginPath();
      ctx.moveTo(pkt.srcX * SCALE, pkt.srcY * SCALE);
      ctx.lineTo(pkt.dstX * SCALE, pkt.dstY * SCALE);
      ctx.strokeStyle = "#475569"; // slate-600
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  };

  const drawNodes = (ctx: CanvasRenderingContext2D) => {
    for (const n of nodes) {
      const x = n.x * SCALE;
      const y = n.y * SCALE;
      const color = ROLE_COLOR[n.role] ?? "#94a3b8";
      const isHovered = hoveredNode === n.id;
      
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.shadowBlur = isHovered ? 16 : 8;
      ctx.shadowColor = color;
      ctx.fill();
      ctx.shadowBlur = 0;
      
      if (n.isBroker) {
        ctx.beginPath();
        ctx.arc(x, y, 12, 0, Math.PI * 2);
        ctx.strokeStyle = "#fbbf24"; // yellow-400
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      
      // Highlight on hover
      if (isHovered) {
        ctx.beginPath();
        ctx.arc(x, y, 16, 0, Math.PI * 2);
        ctx.strokeStyle = "#ef4444"; // red-500
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      
      // Draw node ID
      ctx.fillStyle = "#fff";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(n.id.toString(), x, y - 15);
    }
  };

  const drawPackets = (ctx: CanvasRenderingContext2D) => {
    for (const pkt of packetsRef.current) {
      const x = (pkt.srcX + (pkt.dstX - pkt.srcX) * pkt.progress) * SCALE;
      const y = (pkt.srcY + (pkt.dstY - pkt.srcY) * pkt.progress) * SCALE;
      
      const color = PHY_COLOR[pkt.kind] ?? "#fff";
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.shadowBlur = 12;
      ctx.shadowColor = color;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  };

  useEffect(() => {
    const animate = () => {
      const canvas = ref.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      drawLines(ctx);
      drawNodes(ctx);
      drawPackets(ctx);
      
      // Update packet positions (slower speed)
      setPackets(prev => 
        prev
          .map(p => ({ ...p, progress: p.progress + 0.008 }))
          .filter(p => p.progress < 1)
      );
      
      requestAnimationFrame(animate);
    };
    
    const animId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animId);
  }, [nodes]);

  // Expose method to add packets
  useEffect(() => {
    (window as any).addPacket = (srcId: number, dstId: number, kind: string) => {
      const src = nodes.find(n => n.id === srcId);
      const dst = nodes.find(n => n.id === dstId);
      if (!src || !dst) {
        console.log("Node not found:", srcId, dstId);
        return;
      }
      
      console.log("Adding packet:", srcId, "->", dstId, kind);
      setPackets(prev => [...prev, {
        id: `${Date.now()}-${Math.random()}`,
        srcId,
        dstId,
        srcX: src.x,
        srcY: src.y,
        dstX: dst.x,
        dstY: dst.y,
        progress: 0,
        kind: kind as any
      }]);
    };
  }, [nodes]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = ref.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    
    // Check if click is on a node
    for (const n of nodes) {
      const nodeX = n.x * SCALE;
      const nodeY = n.y * SCALE;
      const distance = Math.sqrt((clickX - nodeX) ** 2 + (clickY - nodeY) ** 2);
      
      if (distance <= 16) { // Click radius
        if (confirm(`Delete node ${n.id} (${n.role})?`)) {
          onDeleteNode?.(n.id);
        }
        return;
      }
    }
  };

  const handleCanvasMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = ref.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Check if hovering over a node
    let foundNode: number | null = null;
    let foundNodeData: NodeView | null = null;
    for (const n of nodes) {
      const nodeX = n.x * SCALE;
      const nodeY = n.y * SCALE;
      const distance = Math.sqrt((mouseX - nodeX) ** 2 + (mouseY - nodeY) ** 2);
      
      if (distance <= 16) {
        foundNode = n.id;
        foundNodeData = n;
        break;
      }
    }
    
    setHoveredNode(foundNode);
    if (foundNodeData) {
      setTooltip({ x: e.clientX, y: e.clientY, node: foundNodeData });
    } else {
      setTooltip(null);
    }
  };

  return (
    <div className="relative rounded-2xl overflow-hidden shadow-xl border border-slate-700">
      <canvas 
        ref={ref} 
        width={width} 
        height={height} 
        onClick={handleCanvasClick}
        onMouseMove={handleCanvasMove}
        onMouseLeave={() => { setHoveredNode(null); setTooltip(null); }}
        style={{ cursor: hoveredNode ? 'pointer' : 'default' }}
      />
      {tooltip && (
        <div 
          className="fixed z-50 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-xs text-white shadow-lg pointer-events-none"
          style={{ left: tooltip.x + 10, top: tooltip.y + 10 }}
        >
          <div className="font-semibold mb-1">Node {tooltip.node.id}</div>
          <div className="text-slate-300">Role: {tooltip.node.role}</div>
          <div className="text-slate-300">PHY: {tooltip.node.phy}</div>
          <div className="text-slate-300">Position: ({tooltip.node.x.toFixed(0)}, {tooltip.node.y.toFixed(0)})</div>
          <div className="text-slate-300">Energy: {tooltip.node.energy.toFixed(1)}%</div>
        </div>
      )}
    </div>
  );
}
