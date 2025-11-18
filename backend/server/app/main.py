from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .sim.store import store
from .sim.models import NodeCreate, NodeView, MetricsView, RoutingTableView, RouteEntryView
from .sim.types import MacConfig
import asyncio

app = FastAPI(title="IoT/MQTT Simulator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def _startup():
    # start the background simulation loop
    asyncio.create_task(store.loop())

@app.get("/health")
def health():
    return {"status": "ok"}

# ---- nodes ----

@app.get("/nodes", response_model=list[NodeView])
def list_nodes():
    return [
        NodeView(
            id=n.id, role=n.role, phy=n.phy,
            x=n.pos.x, y=n.pos.y,
            energy=n.energy, awake=n.awake,
            sleepRatio=n.sleep_ratio, isBroker=n.is_broker
        )
        for n in store.nodes
    ]

@app.post("/nodes", response_model=NodeView)
def add_node(payload: NodeCreate):
    nid = store.add_node(payload.role, payload.phy, payload.x, payload.y)
    n = next(n for n in store.nodes if n.id == nid)
    return NodeView(
        id=n.id, role=n.role, phy=n.phy,
        x=n.pos.x, y=n.pos.y,
        energy=n.energy, awake=n.awake,
        sleepRatio=n.sleep_ratio, isBroker=n.is_broker
    )

@app.delete("/nodes/{nid}")
def delete_node(nid: int):
    if not any(n.id == nid for n in store.nodes):
        raise HTTPException(status_code=404, detail="node not found")
    store.remove_node(nid)
    return {"ok": True}

@app.post("/traffic")
def traffic(src: int, dst: int, n: int = 1, size: int = 100, kind: str = "WiFi"):
    enq = store.enqueue(src_id=src, dst_id=dst, n=n, size=size, kind=kind)
    return {"enqueued_ok": enq}

# ---- control ----

@app.post("/control/start")
def start():
    store.running = True
    return {"running": store.running}

@app.post("/control/pause")
def pause():
    store.running = False
    return {"running": store.running}

@app.post("/control/reset")
def reset():
    store.reset()
    return {"ok": True}

# ---- metrics (placeholder in PR1) ----

@app.get("/metrics", response_model=MetricsView)
def metrics():
    now = store.engine.now
    m = store.mac.metrics
    delivered = m.dequeued_ok
    duplicates = m.duplicates
    pdr = m.pdr
    avg_latency_ms = (m.rtt_ms_total / m.rtt_samples) if m.rtt_samples else 0.0
    return MetricsView(now=now, pdr=pdr, avgLatencyMs=avg_latency_ms, delivered=delivered, duplicates=duplicates)

# ---- network layer ----

@app.get("/routing/{node_id}", response_model=RoutingTableView)
def get_routing_table(node_id: int):
    """Get routing table for a specific node"""
    if not any(n.id == node_id for n in store.nodes):
        raise HTTPException(status_code=404, detail="node not found")
    
    routes_dict = store.network.get_routing_table(node_id)
    routes = [
        RouteEntryView(dest=dest, nextHop=next_hop, metric=metric)
        for dest, (next_hop, metric) in routes_dict.items()
    ]
    return RoutingTableView(nodeId=node_id, routes=routes)

@app.get("/routing", response_model=list[RoutingTableView])
def get_all_routing_tables():
    """Get routing tables for all nodes"""
    tables = []
    for node in store.nodes:
        routes_dict = store.network.get_routing_table(node.id)
        routes = [
            RouteEntryView(dest=dest, nextHop=next_hop, metric=metric)
            for dest, (next_hop, metric) in routes_dict.items()
        ]
        tables.append(RoutingTableView(nodeId=node.id, routes=routes))
    return tables
