# Testing Mobile Node Reconnection

## 🎯 Goal: See node disconnect and reconnect as it moves

### Setup for Best Results:

**Node Positions:**
- **Broker (Node 3)**: X=115, Y=100 (center)
- **Publisher (Node 1)**: X=100, Y=100 (stationary, close to broker)
- **Mobile Subscriber (Node 2)**: X=130, Y=100 (starts 15 units from broker)

**Why these positions?**
- Mobile node starts CLOSE to broker (15 units)
- Will move up to 70 units away from starting point (130,100)
- WiFi range = 55 units
- So it will go: In range → Out of range → Back in range

---

## 📋 Step-by-Step Test:

### 1. Setup Nodes
```
1. Click "Reset"
2. Create Node 1: publisher, WiFi, X=100, Y=100 → "Create"
3. Create Node 2: subscriber, WiFi, X=130, Y=100
   ✅ Check "Mobile"
   Speed=1.5
   → "Create"
4. Create Node 3: broker, WiFi, X=115, Y=100 → "Create"
5. Click "Start"
```

### 2. Subscribe
```
MQTT Panel:
- Topic: sensor/temp
- QoS: 0
- Subscriber ID: 2
- Click "Subscribe"
```

### 3. Publish Repeatedly
```
Every 5 seconds, publish a message:
- Publisher ID: 1
- Payload: (increment each time: "1", "2", "3", etc.)
- Click "Publish"

Do this 6-8 times over 30-40 seconds
```

### 4. Watch the Magic! ✨

**What to observe:**

**Phase 1: Connected (0-10 seconds)**
- Node 2 near starting position
- 🟢 Green dot next to "subscriber 2"
- `Rcv=` count increases with each publish
- Example: Pub=3, Rcv=3

**Phase 2: Moving Away (10-20 seconds)**
- Node 2 moves away from broker
- When distance > 55 units:
  - 🔴 Red dot appears!
  - `connected: false`
  - `Rcv=` stops increasing
  - `Disconnects=1` appears
- Example: Pub=5, Rcv=3 (missed 2 messages)

**Phase 3: Coming Back (20-30 seconds)**
- Node 2 moves back toward starting position
- When distance < 55 units:
  - 🟢 Green dot returns!
  - `connected: true`
  - `Reconnects=1` appears (yellow text)
  - `Rcv=` starts increasing again
- Example: Pub=7, Rcv=5 (received 2 more after reconnect)

---

## 📊 Expected Stats After 30 Seconds:

**Broker Stats:**
```
messages_received: 6-8
messages_delivered: 0 (some pending)
queue_depth: 2-3 (undelivered messages)
```

**Publisher Stats:**
```
messages_published: 6-8
```

**Subscriber Stats:**
```
🟢 connected: true (if back in range)
Rcv: 4-6 (less than published due to disconnection)
Disconnects: 1-2
Reconnects: 1-2 (yellow text)
```

---

## 🎥 Perfect Screenshot Moments:

1. **Initial State**: Green dot, Rcv=2
2. **Disconnected**: Red dot, Rcv=2 (stopped), Disconnects=1
3. **Reconnected**: Green dot, Rcv=4, Reconnects=1 (yellow)
4. **Final Stats**: Show Pub vs Rcv mismatch due to mobility

---

## 💡 Tips:

**If node doesn't disconnect:**
- It might not have moved far enough yet
- Wait longer (20-30 seconds)
- Try higher speed (2.0 m/s)

**If node never reconnects:**
- It will! Bounded mobility keeps it within 70 units
- Just wait a bit longer
- Node pauses 2 seconds at each waypoint

**To see it faster:**
- Use Speed=2.0 (moves faster)
- Publish every 3 seconds instead of 5

---

## 🔬 Technical Details:

**Mobility Model:**
- Random Waypoint with 70-unit radius
- Starts at (130, 100)
- Picks random points within 70 units
- Moves at 1.5 m/s
- Pauses 2 seconds at each waypoint

**Range Checking:**
- WiFi range: 55 units
- Broker at (115, 100)
- Subscriber starts at (130, 100) = 15 units (in range)
- Can move up to (130±70, 100±70)
- Max distance from broker: ~100 units (out of range!)
- Will cycle in and out of range

**Connection States:**
- 🟢 Green = within 55 units of broker
- 🔴 Red = beyond 55 units from broker
- Checked every 100ms in simulation loop
