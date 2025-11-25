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

# ---- MQTT ----

@app.post("/mqtt/subscribe")
def mqtt_subscribe(client_id: int, topic: str, qos: int = 0):
    """Subscribe a client to an MQTT topic"""
    if client_id not in store.mqtt_clients:
        raise HTTPException(status_code=404, detail="client not found")
    
    client = store.mqtt_clients[client_id]
    client.subscribed_topics.add(topic)
    
    # Find broker (assume first broker for now)
    broker_id = next(iter(store.mqtt_brokers.keys()), None)
    if not broker_id:
        raise HTTPException(status_code=404, detail="no broker available")
    
    broker = store.mqtt_brokers[broker_id]
    retained_msgs = broker.subscribe(client_id, topic, qos)
    
    return {"ok": True, "topic": topic, "retained_messages": len(retained_msgs)}

@app.post("/mqtt/publish")
def mqtt_publish(publisher_id: int, topic: str, payload: str, qos: int = 0, retained: bool = False):
    """Publish an MQTT message"""
    if publisher_id not in store.mqtt_clients:
        raise HTTPException(status_code=404, detail="publisher not found")
    
    # Find broker
    broker_id = next(iter(store.mqtt_brokers.keys()), None)
    if not broker_id:
        raise HTTPException(status_code=404, detail="no broker available")
    
    client = store.mqtt_clients[publisher_id]
    msg_id = store._next_msg_id
    store._next_msg_id += 1
    
    message = client.publish_message(topic, payload, qos, retained, msg_id)
    broker = store.mqtt_brokers[broker_id]
    deliveries = broker.publish(message)
    
    # Actually deliver messages to subscribers
    delivered_count = 0
    for sub_id, msg in deliveries:
        if sub_id in store.mqtt_clients:
            ack_msg_id = store.mqtt_clients[sub_id].receive_message(msg)
            if ack_msg_id:
                broker.receive_ack(ack_msg_id, sub_id)
            delivered_count += 1
    
    return {"ok": True, "msg_id": msg_id, "subscribers": delivered_count}

@app.get("/mqtt/stats")
def mqtt_stats():
    """Get MQTT statistics"""
    broker_stats = {}
    for broker_id, broker in store.mqtt_brokers.items():
        broker_stats[broker_id] = broker.stats
    
    client_stats = {}
    for client_id, client in store.mqtt_clients.items():
        client_stats[client_id] = {
            "role": client.role,
            "subscribed_topics": list(client.subscribed_topics),
            "stats": client.stats
        }
    
    return {
        "brokers": broker_stats,
        "clients": client_stats
    }

@app.post("/mqtt/reset")
def mqtt_reset():
    """Reset MQTT subscriptions and stats"""
    for broker in store.mqtt_brokers.values():
        broker.subscriptions.clear()
        broker.retained_messages.clear()
        broker.pending_acks.clear()
        broker.message_queue.clear()
        broker.stats = {
            'messages_received': 0,
            'messages_delivered': 0,
            'qos0_messages': 0,
            'qos1_messages': 0,
            'duplicates_sent': 0,
            'acks_received': 0,
            'queue_depth': 0
        }
    
    for client in store.mqtt_clients.values():
        client.subscribed_topics.clear()
        client.received_messages.clear()
        client.received_msg_ids.clear()
        client.stats = {
            'messages_published': 0,
            'messages_received': 0,
            'duplicates_received': 0,
            'acks_sent': 0
        }
    
    return {"ok": True}
