import { api } from "./client";
import type { NodeView, Metrics, RoutingTable, Role, Phy } from "./types";

export const getHealth = () => api.get("/health").then(r=>r.data);
export const getNodes = () => api.get<NodeView[]>("/nodes").then(r=>r.data);
export const createNode = (n:{role:Role; phy:Phy; x:number; y:number; mobile?:boolean; speed?:number}) =>
  api.post<NodeView>("/nodes", n).then(r=>r.data);
export const deleteNode = (id:number) =>
  api.delete(`/nodes/${id}`).then(r=>r.data);

export const startSim = () => api.post("/control/start").then(r=>r.data);
export const pauseSim = () => api.post("/control/pause").then(r=>r.data);
export const resetSim = () => api.post("/control/reset").then(r=>r.data);

export const getMetrics = () => api.get<Metrics>("/metrics").then(r=>r.data);
export const getRouting = () => api.get<RoutingTable[]>("/routing").then(r=>r.data);

export const postTraffic = (p:{src:number; dst:number; n:number; size:number; kind:Phy}) =>
  api.post("/traffic", null, { params: p }).then(r=>r.data);
