# 🛰️ Network Simulator

A modular **IoT network simulator** built for **CS-576**.  
Implements **Physical**, **MAC**, and **Network** layers using a FastAPI backend and a React + Vite frontend.

---

## ⚙️ Setup

### 🪟 Windows (PowerShell)
```powershell
git clone https://github.com/kedarnhegde/network-simulator.git
cd network-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install --force-reinstall pydantic pydantic-core --no-cache-dir  # if needed
cd backend
python -m uvicorn server.app.main:app --reload --port 8000
```

### 🐧 Mac/Linux
```bash
git clone https://github.com/kedarnhegde/network-simulator.git
cd network-simulator
python3 -m venv .venv
source .venv/bin/activate
make install-backend
make run-backend
```

Frontend (Not completed yet):
```bash
make install-frontend
make run-frontend
```

**Default ports:**  
📍 Backend → http://127.0.0.1:8000  
📍 Frontend → http://localhost:5173

---

## 🧪 API Endpoints

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/health` | GET | Health check |
| `/nodes` | GET/POST/DELETE | Manage network nodes |
| `/control/start` | POST | Start simulation |
| `/control/pause` | POST | Pause simulation |
| `/control/reset` | POST | Reset simulation |
| `/traffic` | POST | Send packets through MAC/Network layers |
| `/metrics` | GET | Simulation metrics |
| `/routing` | GET | All routing tables |
| `/routing/{id}` | GET | Routing table for a node |

---

## 🧱 Architecture Overview

```
┌────────────────────────────┐
│ Application Layer          │  → traffic via /traffic API
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Network Layer              │
│ - Distance-vector routing  │
│ - Multi-hop forwarding     │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ MAC Layer (CSMA/CA)        │
│ - Backoff, retries, loss   │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Physical Layer             │
│ - WiFi, BLE, Zigbee models │
│ - Range, data rate, energy │
└────────────────────────────┘
```

---

## 🧩 Testing (PHY → MAC → Network)

### 1️⃣ PHY — Range & Energy
```bash
curl -X POST http://localhost:8000/control/reset
curl -X POST http://localhost:8000/nodes -H "content-type: application/json" \
  -d '{"role":"sensor","phy":"WiFi","x":10,"y":10}'
curl -X POST http://localhost:8000/nodes -H "content-type: application/json" \
  -d '{"role":"broker","phy":"WiFi","x":40,"y":40}'
curl -X POST http://localhost:8000/nodes -H "content-type: application/json" \
  -d '{"role":"sensor","phy":"BLE","x":500,"y":500}'
curl -X POST http://localhost:8000/control/start
sleep 3
curl http://localhost:8000/metrics
```
👉 *Expect:* `now` > 0 s; energy decreases over time; distant node not connected.

---

### 2️⃣ MAC — Channel Contention
```bash
curl -X POST http://localhost:8000/control/reset
curl -X POST http://localhost:8000/nodes -H "content-type: application/json" \
  -d '{"role":"broker","phy":"WiFi","x":100,"y":100}'
for i in 1 2 3 4 5; do
  X=$((100+i*2)); Y=$((100+i))
  curl -s -X POST http://localhost:8000/nodes -H "content-type: application/json" \
    -d "{\"role\":\"sensor\",\"phy\":\"WiFi\",\"x\":$X,\"y\":$Y}"
done
curl -X POST http://localhost:8000/control/start
curl -X POST "http://localhost:8000/traffic?src=2&dst=1&n=50&size=200&kind=WiFi"
sleep 3
curl http://localhost:8000/metrics
```
👉 *Expect:* latency ↑, possible delivery variation (PDR < 1) under heavy contention.

---

### 3️⃣ Network — Multi-Hop Routing
```bash
curl -X POST http://localhost:8000/control/reset
curl -X POST http://localhost:8000/nodes -H "content-type: application/json" \
  -d '{"role":"sensor","phy":"BLE","x":10,"y":10}'
curl -X POST http://localhost:8000/nodes -H "content-type: application/json" \
  -d '{"role":"sensor","phy":"BLE","x":25,"y":10}'
curl -X POST http://localhost:8000/nodes -H "content-type: application/json" \
  -d '{"role":"sensor","phy":"BLE","x":40,"y":10}'
curl -X POST http://localhost:8000/control/start
sleep 5
curl http://localhost:8000/routing | jq .
curl -X POST "http://localhost:8000/traffic?src=1&dst=3&n=20&size=100&kind=BLE"
sleep 3
curl http://localhost:8000/metrics | jq .
```
👉 *Expect:* routes show 1 → 3 via 2, `delivered` > 0, non-zero latency (multi-hop).

---

## 📈 Metrics Explained
| Field | Meaning |
|--------|----------|
| `now` | Simulation time |
| `pdr` | Packet delivery ratio (0–1) |
| `avgLatencyMs` | Average latency (ms) |
| `delivered` | Packets delivered |
| `duplicates` | Duplicate packets seen |

---

## 🎨 Testing Packet Visualization in UI

### Step-by-Step Guide:

1. **Start Backend**
   ```bash
   source .venv/bin/activate
   make run-backend
   ```

2. **Start Frontend** (in new terminal)
   ```bash
   cd frontend
   npm install  # first time only
   npm run dev
   ```

3. **Open Browser**
   - Navigate to http://localhost:5173

4. **Create Nodes**
   - Click "Add Node" or use the API
   - Create at least 2 nodes (e.g., sensor at x=100, y=100 and broker at x=400, y=300)

5. **Start Simulation**
   - Click "Start" button in the Controls panel

6. **Send Traffic**
   - In the Traffic panel:
     - Set **Src**: 1 (source node ID)
     - Set **Dst**: 2 (destination node ID)
     - Set **N**: 10 (number of packets)
     - Set **PHY**: WiFi or BLE
   - Click "Send" button

7. **Watch Packets Move!**
   - You'll see small glowing dots (packets) animate from source to destination
   - **Blue dots** = WiFi packets
   - **Purple dots** = BLE packets
   - Up to 5 packets will be visualized at once

**Node Colors:**
- 🟢 Green = Sensor
- 🟠 Amber = Subscriber
- 🩷 Pink = Publisher
- 🩵 Teal = Broker (with yellow ring)

---

## 👥 Contributors
- [@kedarnhegde](https://github.com/kedarnhegde)  
- [@AntonioHengel7](https://github.com/AntonioHengel7)
- [@maleaysabel](https://github.com/maleaysabel)
- [@clinton5609](https://github.com/clinton5609)
- Group 6 — CS-576 Fall 2025
