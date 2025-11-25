# Testing Packet Visualization

## Steps:

1. **Start Backend** (Terminal 1):
```bash
cd /Users/kedar.hegde/Desktop/dev/cs-576/network-simulator
source .venv/bin/activate
make run-backend
```

2. **Start Frontend** (Terminal 2):
```bash
cd /Users/kedar.hegde/Desktop/dev/cs-576/network-simulator/frontend
npm run dev
```

3. **Open Browser**: http://localhost:5173

4. **Create 2 Nodes**:
   - Node 1: Role=sensor, PHY=WiFi, X=150, Y=150 → Click "Create"
   - Node 2: Role=broker, PHY=WiFi, X=450, Y=300 → Click "Create"

5. **Start Simulation**: Click "Start" button

6. **Send Traffic**:
   - Src: 1
   - Dst: 2
   - N: 10
   - Size: 100
   - PHY: WiFi
   - Click "Send"

7. **Watch**: You should see blue glowing dots moving from node 1 to node 2

## Debugging:
- Open browser console (F12) to see logs
- Should see: "Adding packet 1/5", "Adding packet 2/5", etc.
- Packets animate over ~3 seconds

## Colors:
- Nodes: Green (sensor), Teal with yellow ring (broker)
- Packets: Blue (WiFi), Purple (BLE)
