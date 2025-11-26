export type Phy = "WiFi" | "BLE" | "Zigbee";
export type Role = "sensor" | "broker" | "subscriber" | "publisher";

export interface PacketInFlight {
  id: string;
  srcId: number;
  dstId: number;
  srcX: number;
  srcY: number;
  dstX: number;
  dstY: number;
  progress: number; // 0 to 1
  kind: Phy;
}

export interface NodeView {
  id: number;
  role: Role;
  phy: Phy;
  x: number; y: number;
  energy: number;
  awake: boolean;
  sleepRatio: number;
  isBroker: boolean;
  mobile: boolean;
  speed: number;
}

export interface Metrics {
  now: number;
  pdr: number;
  avgLatencyMs: number;
  delivered: number;
  duplicates: number;
}

export interface RouteEntry { dest: number; nextHop: number; metric: number; }
export interface RoutingTable { nodeId: number; routes: RouteEntry[]; }
