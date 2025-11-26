# Mobility & Keep-Alive Testing Guide

## ✅ MQTT Keep-Alive Complete:
- Connection state tracking
- Keep-alive timeout (60s default)
- Automatic reconnection with exponential backoff
- Connection status shown in UI (green/red dot)

## ✅ Mobility Complete:
- Random Waypoint movement
- Mobile nodes (0.5-2 m/s speed)
- Visual indicator (arrow) on mobile nodes
- Position updates in real-time

## 🧪 Testing Mobility:

### Test 1: 70% Stationary + 30% Mobile Mix

**Setup:**
1. Create 7 stationary sensors:
   - Nodes at various positions, Mobile=unchecked
2. Create 3 mobile nodes:
   - Check "Mobile" checkbox
   - Set Speed: 1.0 m/s
   - Role: subscriber or publisher

**Expected:**
- Mobile nodes show blue arrow (➤) indicator
- Mobile nodes move around canvas
- Stationary nodes stay in place
- Tooltip shows speed when hovering mobile nodes

### Test 2: Mobile Node Connectivity

**Step-by-Step:**

1. **Click "Reset" button** (in Simulation panel)

2. **Create 3 Nodes:**
   - Node 1 (Publisher):
     - Role: publisher
     - PHY: WiFi
     - X: 100, Y: 100
     - Mobile: ❌ unchecked
     - Click "Create"
   
   - Node 2 (Subscriber - MOBILE):
     - Role: subscriber
     - PHY: WiFi
     - X: 130, Y: 100
     - Mobile: ✅ checked
     - Speed: 1.5
     - Click "Create"
   
   - Node 3 (Broker):
     - Role: broker
     - PHY: WiFi
     - X: 115, Y: 100
     - Mobile: ❌ unchecked
     - Click "Create"

3. **Start Simulation:**
   - Click "Start" button
   - Watch node 2 move around (has blue arrow ➤)

4. **Subscribe:**
   - In MQTT Panel:
     - Topic: `sensor/temp`
     - QoS: 0
     - Subscriber ID: `2`
     - Click "Subscribe"
   - ✅ Should see: "Subscribed: {ok: true}"

5. **Publish Messages:**
   - In MQTT Panel:
     - Publisher ID: `1`
     - Payload: `25.5`
     - Click "Publish"
   - Wait 2 seconds
   - Click "Publish" again
   - Repeat 3-4 times

6. **Check Results:**
   - Look at "Client Stats" in MQTT Panel:
     - subscriber 2: Check connection dot color
     - 🟢 Green dot = in range, receiving messages
     - 🔴 Red dot = out of range, NOT receiving messages
     - `Rcv=` count shows messages actually received
     - `Disconnects=` shows how many times went out of range

**What You'll See:**
- Node 2 moves around canvas with arrow indicator (➤)
- When in range (within 55 units of broker):
  - 🟢 Green dot
  - Messages received (`Rcv` increments)
- When out of range (>55 units from broker):
  - 🔴 Red dot appears
  - Messages NOT received (`Rcv` stays same)
  - `Disconnects` counter increments
- When moves back in range:
  - 🟢 Green dot returns
  - `Reconnects` counter increments
  - Pending messages may be delivered

---

### Test 3: MQTT Keep-Alive (Connection Timeout)

**Step-by-Step:**

1. **Click "Reset" button** (in Simulation panel)

2. **Create 3 Nodes:**
   - Node 1 (Publisher):
     - Role: publisher, PHY: WiFi
     - X: 100, Y: 100
     - Click "Create"
   
   - Node 2 (Subscriber):
     - Role: subscriber, PHY: WiFi
     - X: 130, Y: 100
     - Click "Create"
   
   - Node 3 (Broker):
     - Role: broker, PHY: WiFi
     - X: 115, Y: 100
     - Click "Create"

3. **Start Simulation:**
   - Click "Start" button

4. **Subscribe:**
   - In MQTT Panel:
     - Topic: `sensor/temp`
     - Subscriber ID: `2`
     - Click "Subscribe"

5. **Publish ONE Message:**
   - Publisher ID: `1`
   - Payload: `25.5`
   - Click "Publish" ONCE
   - ✅ Check Client Stats: subscriber 2 should show `Rcv=1`

6. **Wait and Watch:**
   - Look at "Client Stats" section
   - Initially: 🟢 Green dot next to "subscriber 2" (connected)
   - **Wait 90 seconds** (1.5 minutes) without doing anything
   - After 90s: 🔴 Red dot appears (disconnected due to keep-alive timeout)
   - Client automatically attempts reconnect
   - 🟢 Green dot returns (reconnected)
   - Yellow text appears: "Reconnects=1"

7. **Verify:**
   - Client Stats for subscriber 2:
     - `connected: false` → `true` (after reconnect)
     - `Reconnects=1` (or more)

**What You'll See:**
- Green dot = client is connected
- After 90s of inactivity → Red dot = disconnected
- Automatic reconnection → Green dot returns
- "Reconnects=" counter increments

**Why 90 seconds?**
- Keep-alive timeout = 60 seconds
- System waits 1.5x timeout = 90 seconds before marking disconnected
- This simulates real MQTT keep-alive behavior

## 📊 UI Indicators:

**Mobile Nodes:**
- Blue arrow (➤) next to node ID
- Moves smoothly across canvas
- Tooltip shows: "mobile: true, speed: X m/s"

**Connection State:**
- 🟢 Green dot = Connected
- 🔴 Red dot = Disconnected
- Yellow "Reconnects=N" if reconnections occurred

## 🔬 API Testing:

```bash
# Create mobile node
curl -X POST http://localhost:8000/nodes -H "Content-Type: application/json" \
  -d '{"role":"subscriber","phy":"WiFi","x":100,"y":100,"mobile":true,"speed":1.5}'

# Check positions update
curl http://localhost:8000/nodes | jq '.[] | select(.mobile==true) | {id, x, y, speed}'

# Monitor MQTT connection state
curl http://localhost:8000/mqtt/stats | jq '.clients[] | {role, connected, stats}'
```

## ✅ Rubric Coverage:

### Mobility (6 pts):
- ✅ Mobile clients with 0.5-2 m/s speed
- ✅ Random Waypoint movement model
- ✅ 70% stationary / 30% mobile mix supported
- ✅ Visual indicators for mobile nodes

### MQTT Keep-Alive (part of 22 pts):
- ✅ Keep-alive mechanism (60s timeout)
- ✅ Automatic reconnection
- ✅ Connection state tracking
- ✅ Exponential backoff (max 5 attempts)

## 📝 Demo Script:

1. **Show Stationary Network:**
   - Create 7 stationary sensors in grid
   - Create 1 broker in center
   - Start simulation

2. **Add Mobile Nodes:**
   - Create 3 mobile subscribers (speed 1.0-1.5 m/s)
   - Show arrow indicators
   - Watch them move

3. **Test Connectivity:**
   - Subscribe mobile nodes to topic
   - Publish from stationary node
   - Show messages received when in range

4. **Show Keep-Alive:**
   - Point to green dots (connected)
   - Explain 60s keep-alive timeout
   - Show reconnect stats

5. **Demonstrate Movement Impact:**
   - Mobile node moves out of range
   - Connection drops
   - Moves back in range
   - Reconnects automatically

## 🎥 Screenshot Checklist:
- [ ] 70/30 mix of stationary/mobile nodes
- [ ] Mobile nodes with arrow indicators
- [ ] Nodes at different positions (before/after movement)
- [ ] MQTT stats showing connection states
- [ ] Reconnect counts after mobility
- [ ] Tooltip showing mobile=true and speed
