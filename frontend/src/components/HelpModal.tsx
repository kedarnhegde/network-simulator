import { useState } from "react";

export default function HelpModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Help Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed right-6 top-1/2 -translate-y-1/2 bg-blue-600 hover:bg-blue-500 text-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg transition-all z-40"
        title="Help & Testing Guide"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Modal Content */}
          <div className="relative bg-slate-800 rounded-xl shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto border border-slate-700">
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 p-4 flex justify-between items-center">
              <h2 className="text-xl font-bold">📚 Testing Guide</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-6 text-sm">
              {/* Test 1 */}
              <section>
                <h3 className="text-lg font-semibold mb-3 text-blue-400">Test 1: Physical, MAC & Network Layers</h3>
                <p className="text-slate-300 mb-2"><strong>Goal:</strong> Verify WiFi/BLE range, energy consumption, CSMA/CA collision handling, and multi-hop routing.</p>
                <ol className="list-decimal list-inside space-y-1 text-slate-300 ml-2">
                  <li>Click <strong>Reset</strong></li>
                  <li>Create 3 WiFi nodes in a line:
                    <ul className="list-disc list-inside ml-6 text-xs mt-1">
                      <li>Node 1: Role: sensor, PHY: WiFi, X: 100, Y: 100</li>
                      <li>Node 2: Role: sensor, PHY: WiFi, X: 100, Y: 140 (relay)</li>
                      <li>Node 3: Role: sensor, PHY: WiFi, X: 100, Y: 180</li>
                    </ul>
                  </li>
                  <li>Add BLE node out of range: Role: sensor, PHY: BLE, X: 200, Y: 100</li>
                  <li>Click <strong>Start</strong></li>
                  <li>Wait 5 seconds (for routing tables to build)</li>
                  <li>Send traffic: Src: 1, Dst: 3, N: 10, Size: 100, PHY: WiFi → Click <strong>Send</strong></li>
                  <li>Send concurrent traffic: Src: 3, Dst: 1, N: 20, Size: 200, PHY: WiFi → Click <strong>Send</strong></li>
                </ol>
                <p className="text-green-400 mt-2"><strong>Expected:</strong> Energy decreases, Node 4 isolated, blue packet animations, PDR ~1.0, packets hop 1→2→3</p>
              </section>

              {/* Test 2 */}
              <section>
                <h3 className="text-lg font-semibold mb-3 text-purple-400">Test 2: MQTT Protocol & Advanced Features</h3>
                <p className="text-slate-300 mb-2"><strong>Goal:</strong> Test MQTT pub/sub, QoS levels, topic heatmap, queue depth, mobility, and broker failover.</p>
                <ol className="list-decimal list-inside space-y-1 text-slate-300 ml-2">
                  <li>Click <strong>Reset</strong></li>
                  <li>Create MQTT topology:
                    <ul className="list-disc list-inside ml-6 text-xs mt-1">
                      <li>Node 1: Role: broker, PHY: WiFi, X: 100, Y: 100</li>
                      <li>Node 2: Role: publisher, PHY: WiFi, X: 80, Y: 100</li>
                      <li>Node 3: Role: subscriber, PHY: WiFi, X: 120, Y: 80</li>
                      <li>Node 4: Role: subscriber, PHY: WiFi, X: 120, Y: 120</li>
                      <li>Node 5: Role: subscriber, PHY: WiFi, X: 110, Y: 100, Mobile: ✓, Speed: 3</li>
                    </ul>
                  </li>
                  <li>Click <strong>Start</strong></li>
                  <li>Subscribe clients:
                    <ul className="list-disc list-inside ml-6 text-xs mt-1">
                      <li>Subscriber ID: 3, Topic: sensor/temp, QoS: 0 → <strong>Subscribe</strong></li>
                      <li>Subscriber ID: 4, Topic: sensor/temp, QoS: 1 → <strong>Subscribe</strong></li>
                    </ul>
                  </li>
                  <li>Publish messages: Publisher ID: 2, Topic: sensor/temp, Payload: 25, QoS: 0 → <strong>Publish</strong> (repeat 10 times)</li>
                  <li><strong>Test queue depth:</strong> Change QoS to 1, rapidly click <strong>Publish</strong> 20 times → Watch Broker Stats Queue depth increase then decrease</li>
                  <li><strong>Test mobility:</strong> Subscribe node 5 (Subscriber ID: 5, Topic: sensor/temp) → Watch node 5 move (blue arrow ➤) → Publish every 2 seconds for 30 seconds → Watch node 5: 🟢 (connected) → 🔴 (out of range) → 🟢 (reconnected)</li>
                  <li><strong>Test broker failover:</strong> In Broker Failover section, enter X: 200, Y: 200 → Click <strong>Relocate</strong> → Watch Reconnection Wave for reconnection events → Relocate back: X: 100, Y: 100</li>
                </ol>
                <p className="text-green-400 mt-2"><strong>Expected:</strong> Purple MQTT packets, green ACK packets for QoS 1, topic heatmap updates, queue depth fluctuates, mobile node reconnects, broker moves and clients reconnect</p>
              </section>

              {/* Test 3 */}
              <section>
                <h3 className="text-lg font-semibold mb-3 text-amber-400">Test 3: Experiments</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-slate-300 font-semibold">Experiment 1: Duty Cycle Impact</p>
                    <p className="text-slate-400 text-xs">Click <strong>E1: Duty Cycle Impact</strong> button → Wait ~60s → View results → Download CSV</p>
                    <p className="text-green-400 text-xs mt-1">Expected: Higher sleep ratio = More energy saved</p>
                  </div>
                  <div>
                    <p className="text-slate-300 font-semibold">Experiment 2: BLE vs WiFi</p>
                    <p className="text-slate-400 text-xs">Click <strong>E2: BLE vs WiFi</strong> button → Wait ~25s → View comparison → Download CSV</p>
                    <p className="text-green-400 text-xs mt-1">Expected: WiFi faster but uses more energy, BLE slower but more efficient</p>
                  </div>
                </div>
              </section>

              {/* Legend */}
              <section className="border-t border-slate-700 pt-4">
                <h3 className="text-lg font-semibold mb-2">Legend</h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="text-green-500">●</span> Sensor</div>
                  <div><span className="text-amber-500">●</span> Subscriber</div>
                  <div><span className="text-teal-500">●</span> Publisher</div>
                  <div><span className="text-pink-500">●</span> Broker</div>
                  <div><span className="text-cyan-500">●</span> WiFi Packet</div>
                  <div><span className="text-yellow-500">●</span> BLE Packet</div>
                  <div><span className="text-purple-500">●</span> MQTT Packet</div>
                  <div><span className="text-green-500">●</span> ACK Packet</div>
                </div>
              </section>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
