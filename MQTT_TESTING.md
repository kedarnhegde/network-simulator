# MQTT Protocol Testing Guide

## 🎯 What's Implemented:
- ✅ MQTT Broker with pub/sub
- ✅ QoS 0 (Fire and Forget)
- ✅ QoS 1 (At Least Once) with ACK
- ✅ DUP flag for retransmissions
- ✅ Retained messages
- ✅ Broker queue management
- ✅ Statistics tracking

## 🧪 UI Testing Steps (for Screenshots/Recording):

### Setup:
1. Start backend: `source .venv/bin/activate && make run-backend`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser: http://localhost:5173

### Test Scenario 1: Basic Pub/Sub with QoS 0

**Step 1: Create Nodes**
- Create Node 1: Role=**publisher**, PHY=WiFi, X=100, Y=100
- Create Node 2: Role=**subscriber**, PHY=WiFi, X=130, Y=100
- Create Node 3: Role=**broker**, PHY=WiFi, X=115, Y=100

**Step 2: Start Simulation**
- Click "Start" button

**Step 3: Subscribe**
- In MQTT Panel:
  - Topic: `sensor/temperature`
  - QoS: `0 (Fire & Forget)`
  - Subscriber ID: `2`
  - Click "Subscribe"
- ✅ Should show: "Subscribed: {ok: true, ...}"

**Step 4: Publish**
- In MQTT Panel:
  - Publisher ID: `1`
  - Payload: `25.5`
  - Click "Publish"
- ✅ Should show: "Published: {ok: true, subscribers: 1}"

**Step 5: Check Stats**
- Broker Stats should show:
  - `messages_received: 1`
  - `qos0_messages: 1`
  - `queue_depth: 0` (processed)
- Client Stats should show:
  - Publisher 1: `messages_published: 1`
  - Subscriber 2: `messages_received: 1`

### Test Scenario 2: QoS 1 with DUP Handling

**Step 1: Change QoS**
- Set QoS to `1 (At Least Once)`

**Step 2: Subscribe & Publish**
- Subscribe node 2 to topic
- Publish from node 1

**Step 3: Observe DUP Handling**
- Wait 5-10 seconds
- Check Broker Stats:
  - `qos1_messages` should increment
  - `duplicates_sent` may show retransmissions if ACK delayed
  - `acks_received` should match delivered messages

**Step 4: Multiple Subscribers**
- Create Node 4: Role=subscriber, PHY=WiFi, X=145, Y=100
- Subscribe node 4 to same topic
- Publish again
- ✅ Should show: "subscribers: 2"

### Test Scenario 3: Multiple Topics

**Step 1: Different Topics**
- Subscribe node 2 to `sensor/temperature`
- Subscribe node 4 to `sensor/humidity`

**Step 2: Publish to Each**
- Publish to `sensor/temperature` → Only node 2 receives
- Publish to `sensor/humidity` → Only node 4 receives

**Step 3: Wildcard (Future)**
- Currently exact match only

## 📊 What to Capture for Demo:

### Screenshots:
1. **Initial Setup**: 3 nodes (publisher, subscriber, broker) on canvas
2. **MQTT Panel**: Showing subscribe/publish controls
3. **After Subscribe**: Message showing successful subscription
4. **After Publish**: Message showing delivery to subscribers
5. **Broker Stats**: Queue depth, messages received/delivered
6. **Client Stats**: Published/received counts, DUP detection
7. **QoS 1 Demo**: Showing ACKs and retransmissions

### Screen Recording Flow:
1. Create 3 nodes (publisher, subscriber, broker)
2. Start simulation
3. Subscribe to topic
4. Publish message
5. Show stats updating in real-time
6. Publish multiple messages
7. Show QoS 0 vs QoS 1 behavior
8. Demonstrate DUP flag (wait for retransmission)

## 🔬 API Testing (curl):

```bash
# Reset
curl -X POST http://localhost:8000/control/reset

# Create nodes
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role":"publisher","phy":"WiFi","x":100,"y":100}'
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role":"subscriber","phy":"WiFi","x":130,"y":100}'
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role":"broker","phy":"WiFi","x":115,"y":100}'

# Start simulation
curl -X POST http://localhost:8000/control/start

# Subscribe
curl -X POST "http://localhost:8000/mqtt/subscribe?client_id=2&topic=sensor/temp&qos=0"

# Publish
curl -X POST "http://localhost:8000/mqtt/publish?publisher_id=1&topic=sensor/temp&payload=25.5&qos=0"

# Check stats
curl http://localhost:8000/mqtt/stats | jq .
```

## ✅ Rubric Coverage:

### PHY/MAC/Network fidelity & MQTT correctness (22 pts):
- ✅ MQTT broker implementation
- ✅ Publish/Subscribe semantics
- ✅ QoS 0 and QoS 1
- ✅ DUP flag handling
- ✅ Message routing through broker
- ✅ ACK mechanism for QoS 1
- ✅ Retransmission logic

### What's Demonstrated:
1. **Broker**: Central message routing
2. **Publishers**: Send messages to topics
3. **Subscribers**: Receive messages from subscribed topics
4. **QoS 0**: Fire and forget (no ACK)
5. **QoS 1**: At least once delivery with ACK
6. **DUP Flag**: Set on retransmissions
7. **Statistics**: Real-time tracking of all MQTT operations

## 📝 Notes for PR:
- MQTT protocol fully integrated with existing PHY/MAC/Network layers
- Broker manages subscriptions and routes messages
- QoS levels properly implemented with ACK/retransmission
- DUP flag correctly set for QoS 1 retransmissions
- Statistics panel shows real-time MQTT metrics
- Ready for experiments comparing QoS levels
