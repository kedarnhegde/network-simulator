# 🛰️ Network Simulator

A modular simulation platform built for the **CS-576 project**.  
Uses **backend (FastAPI)** and **frontend (React + Vite)**.

---

## ⚙️ Setup Instructions

### 🪟 Windows (PowerShell)

```powershell
# 1. Clone the repository
git clone https://github.com/kedarnhegde/network-simulator.git
cd network-simulator

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install backend dependencies
pip install -r backend\requirements.txt

# 4. Fix pydantic if needed (Python 3.14 compatibility)
pip install --force-reinstall pydantic pydantic-core --no-cache-dir
```

**Run Backend:**
```powershell
cd backend
python -m uvicorn server.app.main:app --reload --host 127.0.0.1 --port 8000
```

**Run Frontend (separate terminal):**
```powershell
cd frontend
npm install  # First time only
npm run dev
```

### 🐧 Unix/Mac/Linux

```bash
# 1. Clone the repository
git clone https://github.com/kedarnhegde/network-simulator.git
cd network-simulator

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies and run
make install-backend
make run-backend  # In one terminal
make install-frontend
make run-frontend  # In another terminal
```

By default, the servers run on:  
📍 **Backend:** http://127.0.0.1:8000  
📍 **Frontend:** http://localhost:5173

---

## 🧪 API Endpoints

| Endpoint            | Method              | Description                                 |
|---------------------|---------------------|---------------------------------------------|
| `/health`           | GET                 | Health check (returns `{"status":"ok"}`)    |
| `/nodes`            | GET / POST / DELETE | Manage network nodes                         |
| `/traffic`          | POST                | Enqueue packets for MAC layer transmission   |
| `/control/start`    | POST                | Start the simulation                         |
| `/control/pause`    | POST                | Pause the simulation                          |
| `/control/reset`    | POST                | Reset the simulation                          |
| `/metrics`          | GET                 | MAC layer metrics (PDR, latency, etc.)       |
| `/routing`          | GET                 | Get all routing tables                       |
| `/routing/{node_id}`| GET                 | Get routing table for specific node          |

---

## 🌐 Network Layer

The simulator implements a **distance-vector routing protocol** with periodic route advertisements:

- **Hop-count metric** - Routes chosen based on minimum hops
- **Periodic route advertisements** - Nodes broadcast routing tables every 2 seconds
- **Multi-hop forwarding** - Packets routed through intermediate nodes
- **Automatic route discovery** - Routes built as nodes exchange advertisements

**View Routing Tables:**
```powershell
# PowerShell - Get all routing tables
Invoke-RestMethod http://localhost:8000/routing

# PowerShell - Get routing table for node 1
Invoke-RestMethod http://localhost:8000/routing/1

# Unix/Mac/Linux
curl http://localhost:8000/routing
curl http://localhost:8000/routing/1
```

**Example routing table output:**
```json
{
  "nodeId": 1,
  "routes": [
    {"dest": 2, "nextHop": 2, "metric": 1},
    {"dest": 3, "nextHop": 2, "metric": 2}
  ]
}
```

This shows node 1 can reach:
- Node 2 directly (1 hop)
- Node 3 via node 2 (2 hops total)

---

## 🧪 Testing MAC Layer

### Quick Test Sequence (PowerShell)

```powershell
# 1. Reset simulation
Invoke-RestMethod -Method POST http://localhost:8000/control/reset

# 2. Create 3 nodes (2 sensors + 1 broker)
Invoke-RestMethod -Method POST http://localhost:8000/nodes -ContentType "application/json" -Body '{"role": "sensor", "phy": "WiFi", "x": 10, "y": 10}'
Invoke-RestMethod -Method POST http://localhost:8000/nodes -ContentType "application/json" -Body '{"role": "sensor", "phy": "WiFi", "x": 20, "y": 20}'
Invoke-RestMethod -Method POST http://localhost:8000/nodes -ContentType "application/json" -Body '{"role": "broker", "phy": "WiFi", "x": 30, "y": 30}'

# 3. Start simulation
Invoke-RestMethod -Method POST http://localhost:8000/control/start

# 4. Generate traffic (tests CSMA/CA, collisions, retries)
Invoke-RestMethod -Method POST "http://localhost:8000/traffic?src=1&dst=3&n=20&size=100&kind=WiFi"
Invoke-RestMethod -Method POST "http://localhost:8000/traffic?src=2&dst=3&n=20&size=100&kind=WiFi"

# 5. Wait and check metrics
Start-Sleep -Seconds 5
Invoke-RestMethod http://localhost:8000/metrics
```

### Quick Test Sequence (Unix/Mac/Linux - curl)

```bash
# 1. Reset simulation
curl -X POST http://localhost:8000/control/reset

# 2. Create 3 nodes (2 sensors + 1 broker)
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role": "sensor", "phy": "WiFi", "x": 10, "y": 10}'
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role": "sensor", "phy": "WiFi", "x": 20, "y": 20}'
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role": "broker", "phy": "WiFi", "x": 30, "y": 30}'

# 3. Start simulation
curl -X POST http://localhost:8000/control/start

# 4. Generate traffic (tests CSMA/CA, collisions, retries)
curl -X POST "http://localhost:8000/traffic?src=1&dst=3&n=20&size=100&kind=WiFi"
curl -X POST "http://localhost:8000/traffic?src=2&dst=3&n=20&size=100&kind=WiFi"

# 5. Wait and check metrics
sleep 5
curl http://localhost:8000/metrics
```

### Expected Metrics Output

```json
{
  "now": 4.8,
  "pdr": 1.0,
  "avgLatencyMs": 922.75,
  "delivered": 40,
  "duplicates": 0
}
```

**Metrics Explained:**
- `pdr` - Packet Delivery Ratio (0.0 to 1.0)
- `avgLatencyMs` - Average end-to-end latency in milliseconds
- `delivered` - Total packets successfully delivered
- `duplicates` - Duplicate packets detected

### Individual Endpoint Tests

**Health Check:**
```powershell
# PowerShell
Invoke-RestMethod http://localhost:8000/health

# Unix/Mac/Linux
curl http://localhost:8000/health
```

**List Nodes:**
```powershell
# PowerShell
Invoke-RestMethod http://localhost:8000/nodes

# Unix/Mac/Linux
curl http://localhost:8000/nodes
```

**Add Node (BLE):**
```powershell
# PowerShell
Invoke-RestMethod -Method POST http://localhost:8000/nodes -ContentType "application/json" -Body '{"role": "sensor", "phy": "BLE", "x": 15, "y": 25}'

# Unix/Mac/Linux
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role": "sensor", "phy": "BLE", "x": 15, "y": 25}'
```

**Delete Node:**
```powershell
# PowerShell
Invoke-RestMethod -Method DELETE http://localhost:8000/nodes/1

# Unix/Mac/Linux
curl -X DELETE http://localhost:8000/nodes/1
```

**Pause Simulation:**
```powershell
# PowerShell
Invoke-RestMethod -Method POST http://localhost:8000/control/pause

# Unix/Mac/Linux
curl -X POST http://localhost:8000/control/pause
```

### Traffic Parameters

```powershell
# PowerShell
Invoke-RestMethod -Method POST "http://localhost:8000/traffic?src=<SRC_ID>&dst=<DST_ID>&n=<COUNT>&size=<BYTES>&kind=<PHY>"

# Unix/Mac/Linux
curl -X POST "http://localhost:8000/traffic?src=<SRC_ID>&dst=<DST_ID>&n=<COUNT>&size=<BYTES>&kind=<PHY>"
```

- `src` - Source node ID
- `dst` - Destination node ID
- `n` - Number of packets (default: 1)
- `size` - Packet size in bytes (default: 100)
- `kind` - PHY type: WiFi, BLE, or Zigbee (default: WiFi)

---

## 🧰 Available Commands

### Windows (PowerShell)

| Task                    | Command                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------|
| Install backend         | `pip install -r backend\requirements.txt`                                                   |
| Run backend             | `cd backend; python -m uvicorn server.app.main:app --reload --host 127.0.0.1 --port 8000` |
| Install frontend        | `cd frontend; npm install`                                                                  |
| Run frontend            | `cd frontend; npm run dev`                                                                  |

### Unix/Mac/Linux (Makefile)

| Command                 | Description                                      |
|-------------------------|--------------------------------------------------|
| `make run-backend`      | Start FastAPI backend with auto-reload           |
| `make install-backend`  | Install backend dependencies                      |
| `make run-frontend`     | Start React frontend                              |
| `make install-frontend` | Install frontend dependencies                     |
| `make clean`            | Remove cache, build, and node_modules             |
| `make help`             | Show available commands                            |

---

## 👥 Contributors

- [@kedarnhegde](https://github.com/kedarnhegde)  
- Group 6 — CS-576, Fall 2025
