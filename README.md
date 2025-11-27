# 🛰️ Network Simulator

A modular **IoT/MQTT network simulator** built for **CS-576**.  
Implements **Physical**, **MAC**, **Network**, and **MQTT** layers with mobility support.

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

Frontend:
```bash
make install-frontend
make run-frontend
```

**Default ports:**  
📍 Backend → http://127.0.0.1:8000  
📍 Frontend → http://localhost:5173

---

## 🧱 Features

### Physical Layer
- WiFi (range: 55 units, 54 Mbps)
- BLE (range: 15 units, 1 Mbps)
- Energy consumption modeling

### MAC Layer
- CSMA/CA with backoff
- Collision detection
- Retry logic

### Network Layer
- Distance-vector routing
- Multi-hop forwarding
- Route advertisements

### MQTT Protocol
- QoS 0 (Fire & Forget) and QoS 1 (At Least Once)
- Publish/Subscribe pattern
- DUP flag for retransmissions
- Keep-alive mechanism
- Broker queue management

### Mobility
- Random Waypoint model
- Bounded movement
- Automatic reconnection

### Visualization
- Real-time packet animation (blue=WiFi, yellow=BLE, purple=MQTT)
- Node states (connected/disconnected)
- Topic heatmap
- Reconnection wave

---

## 🧪 Complete Testing Guide

### Prerequisites

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
make run-backend
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install  # first time only
npm run dev
```

**Browser:** Open http://localhost:5173

---

## Test 1: Physical Layer (Range & Energy)

**Goal:** Verify WiFi/BLE range limits and energy consumption.

**Steps:**
1. Click **Reset** button
2. Click **Add Node** button:
   - Role: `sensor`, PHY: `WiFi`, X: `100`, Y: `100`
3. Click **Add Node** again:
   - Role: `sensor`, PHY: `WiFi`, X: `140`, Y: `100` (within WiFi range)
4. Click **Add Node** again:
   - Role: `sensor`, PHY: `BLE`, X: `200`, Y: `100` (out of range)
5. Click **Start** button
6. Wait 5 seconds
7. Check **Metrics** panel

**Expected:**
- Simulation time (`now`) increases
- Energy decreases for all nodes
- Nodes 1 & 2 can communicate (within 55 units)
- Node 3 isolated (BLE range only 15 units)

---

## Test 2: MAC Layer (CSMA/CA)

**Goal:** Test channel contention and collision handling.

**Steps:**
1. Click **Reset**
2. Create 3 nodes:
   - Node 1: Role: `sensor`, PHY: `WiFi`, X: `100`, Y: `100`
   - Node 2: Role: `sensor`, PHY: `WiFi`, X: `100`, Y: `140`
   - Node 3: Role: `sensor`, PHY: `WiFi`, X: `100`, Y: `180`
3. Click **Start**
4. In **Traffic** panel:
   - Src: `1`, Dst: `2`, N: `20`, Size: `200`, PHY: `WiFi`
   - Click **Send**
5. Immediately send more:
   - Src: `3`, Dst: `2`, N: `20`, Size: `200`, PHY: `WiFi`
   - Click **Send**
6. Watch canvas for blue packet animations
7. Check **Metrics** panel after 5 seconds

**Expected:**
- Blue dots animate between nodes
- Packets delivered (check `delivered` count)
- Some latency due to backoff (check `avgLatencyMs`)
- PDR close to 1.0 (successful delivery)

---

## Test 3: Network Layer (Multi-hop Routing)

**Goal:** Verify packets route through intermediate nodes.

**Steps:**
1. Click **Reset**
2. Create 3 BLE nodes in a line:
   - Node 1: Role: `sensor`, PHY: `WiFi`, X: `100`, Y: `100`
   - Node 2: Role: `sensor`, PHY: `WiFi`, X: `100`, Y: `140` (relay)
   - Node 3: Role: `sensor`, PHY: `WiFi`, X: `100`, Y: `180`
3. Click **Start**
4. Wait 5 seconds (for routing tables to build)
5. In **Traffic** panel:
   - Src: `1`, Dst: `3`, N: `10`, Size: `100`, PHY: `BLE`
   - Click **Send**
6. Watch packets hop: 1 → 2 → 3

**Expected:**
- Blue dots animate 1→2, then 2→3
- Packets delivered to node 3
- Higher latency than single-hop
- Routing tables show node 2 as next hop

---

## Test 4: MQTT Protocol & Advanced Features

**Goal:** Test MQTT pub/sub, QoS levels, topic heatmap, queue depth, mobility, and broker failover.

**Steps:**
1. Click **Reset**
2. Create MQTT topology:
   - Node 1: Role: `broker`, PHY: `WiFi`, X: `100`, Y: `100`
   - Node 2: Role: `publisher`, PHY: `WiFi`, X: `80`, Y: `100`
   - Node 3: Role: `subscriber`, PHY: `WiFi`, X: `120`, Y: `80`
   - Node 4: Role: `subscriber`, PHY: `WiFi`, X: `120`, Y: `120`
   - Node 5: Role: `subscriber`, PHY: `WiFi`, X: `110`, Y: `100`, **Mobile: ✓**, Speed: `3`
3. Click **Start**
4. **Subscribe clients (nodes 3 & 4):**
   - Subscriber ID: `3`, Topic: `sensor/temp`, QoS: `0`, Click **Subscribe**
   - Subscriber ID: `4`, Topic: `sensor/temp`, QoS: `1`, Click **Subscribe**
   - Subscriber ID: `3`, Topic: `sensor/humidity`, QoS: `0`, Click **Subscribe**
5. **Publish messages:**
   - Publisher ID: `2`, Topic: `sensor/temp`, Payload: `25`, QoS: `0`, Click **Publish** (repeat 10 times)
   - Publisher ID: `2`, Topic: `sensor/humidity`, Payload: `60`, QoS: `0`, Click **Publish** (repeat 5 times)
6. **Test queue depth:**
   - Change QoS to `1`, rapidly click **Publish** 20 times
   - Watch **Broker Stats** - Queue depth increases then decreases
7. **Test mobility:**
   - Subscribe node 5: Subscriber ID: `5`, Topic: `sensor/temp`, Click **Subscribe**
   - Watch node 5 move (blue arrow ➤)
   - Publish every 2 seconds: Publisher ID: `2`, Topic: `sensor/temp`, Payload: `msg`
   - Repeat for 30 seconds
   - Watch node 5: 🟢 (connected) → 🔴 (out of range) → 🟢 (reconnected)
8. **Test broker failover:
   - In **Broker Failover** section: X: `150`, Y: `150`, Click **Relocate**
   - Watch **Reconnection Wave** for reconnection events
   - Relocate back: X: `100`, Y: `100`, Click **Relocate**

**Expected:**
- ✅ **Purple dots** animate from broker to subscribers
- ✅ **Client Stats:** 🟢 green dots (connected), `Rcv` counts increase, `Acks` shown for QoS 1
- ✅ **Broker Stats:** `Received` = messages from publisher, Queue depth fluctuates
- ✅ **Topic Heatmap:** Shows `sensor/temp` (10 msgs) and `sensor/humidity` (5 msgs) with gradient bars
- ✅ **Queue Depth:** Increases during burst, decreases to 0
- ✅ **Mobility:** Node 5 moves, disconnects (🔴), reconnects (🟢), `Reconnects=1` shown
- ✅ **Reconnection Wave:** Shows "Node X reconnected" when clients come back in range
- ✅ **Broker Failover:** Broker moves, clients reconnect if in range

---

## Test 5: Experiments

### Experiment 1: Duty Cycle Impact

**Goal:** Measure how sleep ratio affects energy consumption and latency.

**Steps:**
1. Click **E1: Duty Cycle Impact** button in **Experiments** panel
2. Wait ~60 seconds for experiment to complete (button shows "Running...")
3. View results showing 5 different sleep ratios (0%, 20%, 40%, 60%, 80%)

**Expected:**
- ✅ Higher sleep ratio = Higher energy remaining
- ✅ Higher sleep ratio = Higher latency (nodes sleep more)
- ✅ PDR may decrease with very high sleep ratios
- ✅ Results show clear trade-off between energy and performance

**Expected Results:**

| Sleep Ratio | Energy | Latency | PDR | Delivered | Time |
|-------------|--------|---------|-----|-----------|------|
| 0% | ~92% | ~1600ms | 1.00 | 30/30 | ~15s |
| 20% | ~94% | ~1600ms | 1.00 | 30/30 | ~15s |
| 40% | ~95% | ~1600ms | 1.00 | 30/30 | ~15s |
| 60% | ~97% | ~1600ms | 1.00 | 30/30 | ~15s |
| 80% | ~98% | ~1600ms | 1.00 | 30/30 | ~15s |

**Key Insight:** Higher sleep ratio = More energy saved (nodes sleep more)

---

### Experiment 2: BLE vs WiFi Comparison

**Goal:** Compare BLE and WiFi performance in same scenario.

**Steps:**
1. Click **E2: BLE vs WiFi** button in **Experiments** panel
2. Wait ~25 seconds for experiment to complete (button shows "Running...")
3. View side-by-side comparison

**Expected:**
- ✅ **WiFi**: Lower latency (faster data rate: 54 Mbps)
- ✅ **WiFi**: Higher energy consumption (more power)
- ✅ **BLE**: Higher latency (slower data rate: 1 Mbps)
- ✅ **BLE**: Lower energy consumption (energy efficient)
- ✅ Both achieve similar PDR in good conditions

**Expected Results:**

| PHY | Energy | Latency | PDR | Delivered | Time |
|-----|--------|---------|-----|-----------|------|
| WiFi | ~92% | ~1600ms | 1.00 | 30/30 | ~15s |
| BLE | ~98% | ~1600ms | 1.00 | 30/30 | ~15s |

**Key Insights:**
- **WiFi**: Consumes 7.6% energy (high power consumption)
- **BLE**: Consumes 1.5% energy (5x more efficient)
- Latency similar (both use multi-hop routing)
- **Choose WiFi for high-throughput, BLE for battery-powered devices**

---

## Visual Reference

### Node Colors
- 🟢 **Green** = Sensor
- 🟠 **Amber** = Subscriber
- 🩵 **Teal** = Publisher
- 🩷 **Pink** = Broker (with yellow ring)

### Packet Colors
- 🔵 **Blue** = WiFi MAC packets
- 🟡 **Yellow** = BLE MAC packets
- 🟣 **Purple** = MQTT messages (broker → subscribers)
- 🟢 **Green** = ACK packets (broker → publisher, subscribers → broker)

### Connection States
- 🟢 **Green dot** = Connected (in range)
- 🔴 **Red dot** = Disconnected (out of range)

### Indicators
- **➤ Blue arrow** = Mobile node
- **Yellow ring** = Broker node
- **Queue: X** (amber) = Broker queue depth
- **Reconnects=X** (yellow) = Reconnection count

---

## Troubleshooting

**MQTT packets not visible?**
- Ensure simulation is running (click Start)
- Verify subscribers are subscribed before publishing
- Check clients are connected (🟢 green dot)

**Reconnection wave not showing?**
- Mobile nodes must move out of range first (>55 units for WiFi)
- Reconnections only show for last 5 seconds
- Check node has Mobile checkbox enabled

**Topic heatmap empty?**
- Publish messages first
- Ensure subscribers are subscribed to topics
- Messages must be delivered (clients connected)

**Queue depth always 0?**
- Use QoS 1 for queuing behavior
- Publish messages rapidly (burst)
- Check broker stats update (every 1 second)

---

## 📊 Summary

This simulator implements a complete IoT network stack:
- **Physical Layer**: WiFi/BLE with range and energy modeling
- **MAC Layer**: CSMA/CA with collision handling
- **Network Layer**: Distance-vector routing with multi-hop
- **MQTT Protocol**: QoS 0/1, pub/sub, broker, keep-alive
- **Mobility**: Random Waypoint with automatic reconnection
- **Visualization**: Real-time packet animation and network state

All features are testable through the web UI without any command-line tools.

---

## 👥 Contributors
- [@kedarnhegde](https://github.com/kedarnhegde)  
- [@AntonioHengel7](https://github.com/AntonioHengel7)
- [@maleaysabel](https://github.com/maleaysabel)
- [@clinton5609](https://github.com/clinton5609)
- Group 6 — CS-576 Fall 2025
