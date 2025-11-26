# Quick Test Guide - Copy & Paste Steps

## Test 1: Basic MQTT Pub/Sub (QoS 0)

```
1. Click "Reset" (Simulation panel)
2. Create Node 1: publisher, WiFi, X=100, Y=100 → "Create"
3. Create Node 2: subscriber, WiFi, X=130, Y=100 → "Create"
4. Create Node 3: broker, WiFi, X=115, Y=100 → "Create"
5. Click "Start"
6. MQTT Panel: Topic="sensor/temp", QoS=0, Subscriber ID=2 → "Subscribe"
7. MQTT Panel: Publisher ID=1, Payload="25.5" → "Publish"
8. Check Client Stats: subscriber 2 should show Rcv=1 ✅
```

**Expected Result:**
- Publisher 1: Pub=1
- Subscriber 2: Rcv=1
- Broker 3: messages_received=1

---

## Test 2: QoS 1 with ACK

```
1. Click "Reset MQTT" button (in MQTT panel)
2. MQTT Panel: Change QoS to "1 (At Least Once)"
3. Subscribe: Subscriber ID=2, Topic="sensor/temp" → "Subscribe"
4. Publish: Publisher ID=1, Payload="30.0" → "Publish"
5. Check Broker Stats: QoS1=1, ACKs=1 ✅
6. Check Client Stats: subscriber 2 shows ACKs_sent=1 ✅
```

**Expected Result:**
- Broker: QoS1=1, acks_received=1
- Subscriber: acks_sent=1

---

## Test 3: Mobile Node

```
1. Click "Reset"
2. Create Node 1: publisher, WiFi, X=100, Y=100 → "Create"
3. Create Node 2: subscriber, WiFi, X=130, Y=100
   ✅ Check "Mobile" box
   Speed=1.5
   → "Create"
4. Create Node 3: broker, WiFi, X=115, Y=100 → "Create"
5. Click "Start"
6. Watch node 2 move around (has blue arrow ➤) ✅
7. Subscribe node 2 to "sensor/temp"
8. Publish from node 1 multiple times
9. Check if subscriber receives messages (depends on position)
```

**Expected Result:**
- Node 2 moves around canvas
- Blue arrow (➤) indicator visible
- Messages received when in range
- May miss messages when out of range

---

## Test 4: Keep-Alive Timeout

```
1. Click "Reset"
2. Create 3 nodes: publisher(1), subscriber(2), broker(3) as in Test 1
3. Click "Start"
4. Subscribe node 2 to topic
5. Publish ONE message (to update last_activity)
6. Check Client Stats: 🟢 Green dot next to subscriber 2
7. WAIT 90 SECONDS (do nothing)
8. After 90s: 🔴 Red dot appears (disconnected)
9. Client auto-reconnects: 🟢 Green dot returns
10. Check stats: "Reconnects=1" appears ✅
```

**Expected Result:**
- Initially: Green dot (connected)
- After 90s: Red dot (disconnected)
- Auto-reconnect: Green dot + "Reconnects=1"

---

## Test 5: Multiple Subscribers

```
1. Click "Reset"
2. Create Node 1: publisher, WiFi, X=100, Y=100
3. Create Node 2: subscriber, WiFi, X=130, Y=100
4. Create Node 3: broker, WiFi, X=115, Y=100
5. Create Node 4: subscriber, WiFi, X=145, Y=100
6. Click "Start"
7. Subscribe node 2 to "sensor/temp"
8. Subscribe node 4 to "sensor/temp"
9. Publish from node 1
10. Check: BOTH subscribers show Rcv=1 ✅
```

**Expected Result:**
- Publish shows: "subscribers: 2"
- Both node 2 and node 4 receive message

---

## Test 6: Different Topics

```
1. Click "Reset MQTT"
2. Subscribe node 2 to "sensor/temp"
3. Subscribe node 4 to "sensor/humidity"
4. Publish to "sensor/temp" → Only node 2 receives ✅
5. Publish to "sensor/humidity" → Only node 4 receives ✅
```

**Expected Result:**
- Topic-based routing works
- Each subscriber only gets messages for their topics

---

## Visual Indicators Reference

**Node Colors:**
- 🟢 Green = Sensor
- 🟠 Amber = Subscriber
- 🩷 Pink = Publisher
- 🩵 Teal = Broker (with yellow ring)

**Mobile Indicator:**
- ➤ Blue arrow = Mobile node

**Connection State:**
- 🟢 Green dot = Connected
- 🔴 Red dot = Disconnected

**Packet Colors:**
- 🔵 Cyan = WiFi packets
- 🟡 Yellow = BLE packets

---

## Common Issues & Solutions

**"No broker available" error:**
- Make sure you created a node with Role=broker

**Subscriber not receiving messages:**
- Check if subscribed to correct topic
- Verify nodes are within range (WiFi=55 units, BLE=15 units)
- Make sure simulation is running (click "Start")

**Mobile node not moving:**
- Verify "Mobile" checkbox is checked
- Speed must be > 0
- Simulation must be running

**Keep-alive not working:**
- Must wait full 90 seconds
- Don't publish/subscribe during wait (resets timer)
- Check simulation is running

---

## Screenshot Checklist for Demo

- [ ] MQTT Panel showing subscribe/publish controls
- [ ] Broker Stats with queue depth and message counts
- [ ] Client Stats showing Pub/Rcv/DUPs/ACKs
- [ ] Mobile node with arrow indicator
- [ ] Connection states (green/red dots)
- [ ] QoS 0 vs QoS 1 comparison
- [ ] Multiple subscribers receiving same message
- [ ] Reconnect counter after keep-alive timeout
- [ ] Packet animation on canvas
- [ ] Tooltip showing node details (mobile, speed, etc.)
