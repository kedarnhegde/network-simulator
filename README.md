# 🛰️ Network Simulator

A modular simulation platform built for the **CS-576 project**.  
Uses **backend (FastAPI)** and **frontend (React + Vite)**.

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/kedarnhegde/network-simulator.git
cd network-simulator
```

### 2️⃣ Create and activate virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

*(On Windows PowerShell):*
```powershell
.\.venv\Scripts\activate
```

---

## 🧩 Backend Setup

### Install dependencies
```bash
make install-backend # Make sure you're in .venv 
```

### Run the FastAPI backend
```bash
make run-backend # Make sure you're in .venv 
```

By default, the backend runs on:  
📍 **http://localhost:8000**

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

---

## 🧪 Testing MAC Layer

### Quick Test Sequence

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
```bash
curl http://localhost:8000/health
```

**List Nodes:**
```bash
curl http://localhost:8000/nodes
```

**Add Node (BLE):**
```bash
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role": "sensor", "phy": "BLE", "x": 15, "y": 25}'
```

**Delete Node:**
```bash
curl -X DELETE http://localhost:8000/nodes/1
```

**Pause Simulation:**
```bash
curl -X POST http://localhost:8000/control/pause
```

### Traffic Parameters

```bash
curl -X POST "http://localhost:8000/traffic?src=<SRC_ID>&dst=<DST_ID>&n=<COUNT>&size=<BYTES>&kind=<PHY>"
```

- `src` - Source node ID
- `dst` - Destination node ID
- `n` - Number of packets (default: 1)
- `size` - Packet size in bytes (default: 100)
- `kind` - PHY type: WiFi, BLE, or Zigbee (default: WiFi)

---

## 💻 Frontend Setup

```bash
make install-frontend
make run-frontend
```

Default Vite dev server: **http://localhost:5173**

---

## 🧰 Available Makefile Commands

| Command                 | Description                                      |
|-------------------------|--------------------------------------------------|
| `make run-backend`      | Start FastAPI backend with auto-reload           |
| `make install-backend`  | Install backend dependencies                      |
| `make run-frontend`     | Start React frontend                              |
| `make install-frontend` | Install frontend dependencies                     |
| `make clean`            | Remove cache, build, and node_modules             |
| `make help`             | Show available commands                            |

---

## 🧹 Cleaning Up

Remove Python caches, build artifacts, and node modules:
```bash
make clean
```

---

## 👥 Contributors

- [@kedarnhegde](https://github.com/kedarnhegde)  
- Group 6 — CS-576, Fall 2025
