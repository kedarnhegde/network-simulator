import threading
import time
from collections import defaultdict


#broker
class Broker:
    def __init__(self):
        self.subs = defaultdict(set)   # topic -> set of Subscriber objects
        self.metrics = {"rx_publish": 0, "tx_forward": 0}
        self.clients = {} # id -> Client

    #add subscriber to a list of specified topic 
    def handle_sub(self, topic: str, subscriber: "Client"): 
        self.subs[topic].add(subscriber)

    # used by a publisher to handle publish requests
    def handle_pub(self, topic: str, payload, qos: int = 0, meta: dict | None = None):
        self.metrics["rx_publish"] += 1 # successful publish received
        for sub in self.subs.get(topic, ()): # publish to all subscribers of the topic
            sub.receive(topic, payload, {"qos": qos, "dup": False} | (meta or {}))  # prevent sending to the same subscriber
            self.metrics["tx_forward"] += 1 # successful forward to subscriber

        #qos1 broker ack to publisher
        if qos == 1 and meta and "src" in meta and "mid" in meta:
            pub_client = self.clients.get(meta["src"])
            if pub_client:
                if self.ack_drop_count > 0:
                    # simulate ack drop for testing
                    self.ack_drop_count -= 1
                else:
                    pub_client.puback(meta["mid"])

    def register(self, client: "Client"):
        self.clients[client.id] = client

#client
class Client:
    def __init__(self, client_id: str, broker: Broker):
        self.id = client_id
        self.broker = broker
        self._on_message = None
        self.metrics = {"tx_publish": 0, "rx_app": 0, "qos1_retries": 0, "inflight": 0} # messages sent and received
        #qoS1 
        self._next_mid = 1
        self._inflight = {}
        self._retry_limit = 3 # tune later
        self._timeout_ms = 800 # tune later against MAC timing
        #register with broker
        self.broker.register(self)

    def on_message(self, cb):
        self._on_message = cb

    def subscribe(self, topic: str):
        self.broker.handle_sub(topic, self) #add this cleint as a subscriber to the topic

    def publish(self, topic: str, payload, qos: int = 0): # client publishes a message to the broker
        self.metrics["tx_publish"] += 1
        #qos0 handling
        if qos == 0:
            self.broker.handle_pub(topic, payload, qos=qos, meta={"src": self.id})
            return

        # qos1 handling
        mid = self._alloc_mid()
        entry = {"topic": topic, "payload": payload, "qos": qos, "retries": 0, "timer": None}
        self._inflight[mid] = entry
        self.metrics["inflight"] = len(self._inflight)
        # send false dup on first attempt
        self._send_qos1(mid, dup = False)

    def receive(self, topic: str, payload, meta: dict): # used by a broker to deliver a message to this client
        self.metrics["rx_app"] += 1
        if self._on_message:
            self._on_message(topic, payload, meta)

    # allocate message id for qos1 messages
    def _alloc_mid(self):
        mid = self._next_mid
        self._next_mid = 1 if self._next_mid == 65535 else self._next_mid + 1 # 65535 as per the MQTT spec
        return mid
    
    def _send_qos1(self, mid: int, dup: bool):
        entry = self._inflight.get(mid)
        if not entry:
            return
        # message is in flight, send to broker with source id, mid and dupe flag
        meta = {"src": self.id, "mid": mid, "dup": dup}
        self.broker.handle_pub(entry["topic"], entry["payload"], qos=1, meta=meta)

        # start or restart timer for ack
        if entry["timer"]:
            entry["timer"].cancel()
                                # convert time to ms
        t = threading.Timer(self._timeout_ms / 1000.0, lambda: self._on_qos1_timeout(mid))
        entry["timer"] = t
        t.start()

    def _on_qos1_timeout(self, mid: int):
        entry = self._inflight.get(mid)
        if not entry:
            return
        # check if reached retry limit
        if entry["retries"] < self._retry_limit:
            entry["retries"] += 1
            self.metrics["qos1_retries"] += 1
            self._send_qos1(mid, dup=True)
            return
        if entry["timer"]:
            entry["timer"].cancel()
        
        self._inflight.pop[mid, None]
        self.metrics["inflight"] = len(self._inflight)

    def puback(self, mid: int):
        # pop entry to stop retrying
        entry = self._inflight.pop(mid, None)
        if entry and entry["timer"]:
            entry["timer"].cancel()
        self.metrics["inflight"] = len(self._inflight)

# example usage qos1 and qos0
if __name__ == "__main__":
    # --- setup ---
    b = Broker()
    a = Client("A", b)
    c = Client("C", b)

    # faster retry cycle for the demo
    a._timeout_ms = 300   # 0.3s between retries

    # observe deliveries (you'll see dup=True on retries reaching the subscriber)
    c.on_message(lambda t, p, m: print(f"[SUB] topic={t}, payload={p}, meta={m}"))
    c.subscribe("temp")

    # drop the first 2 PUBACKs to force 2 retries
    b.ack_drop_count = 2

    print("\n--- QoS1 publish with forced PUBACK loss (expect retries & dup=True) ---")
    a.publish("temp", 42, qos=1)

    # wait long enough for two timeouts (~0.6s) plus a successful third send
    time.sleep(1.2)

    print("\nBroker metrics:", b.metrics)
    print("Client A metrics:", a.metrics)
    print("Client C metrics:", c.metrics)
    print("A inflight (should be 0 after final PUBACK):", len(a._inflight))

    print("\n--- QoS0 single publish (expect exactly one delivery, no dup) ---")
    b = Broker()
    pub = Client("PUB", b)
    sub1 = Client("SUB1", b)
    sub2 = Client("SUB2", b)

    # subscribe two clients to the same topic
    topic = "temp"
    sub1_events, sub2_events = [], []
    sub1.on_message(lambda t, p, m: sub1_events.append((t, p, m)))
    sub2.on_message(lambda t, p, m: sub2_events.append((t, p, m)))
    sub1.subscribe(topic)
    sub2.subscribe(topic)

    # one QoS0 publish
    pub.publish(topic, 22.5, qos=0)

    # Assertions (simple, script-style)
    assert b.metrics["rx_publish"] == 1, "broker should see one publish"
    assert b.metrics["tx_forward"] == 2, "broker should forward to 2 subs"
    assert pub.metrics["tx_publish"] == 1 and pub.metrics["rx_app"] == 0, "publisher sent once, received none"
    assert len(sub1_events) == 1 and len(sub2_events) == 1, "each subscriber should get exactly one"
    assert sub1_events[0][2]["qos"] == 0 and sub1_events[0][2]["dup"] is False, "QoS0, not duplicate"
    assert sub2_events[0][2]["qos"] == 0 and sub2_events[0][2]["dup"] is False, "QoS0, not duplicate"

    print("[OK] QoS0: one publish → delivered once to each subscriber, no duplicates")
    print("Broker metrics:", b.metrics)
    print("Publisher metrics:", pub.metrics)
    print("Sub1 metrics:", Client('dummy', b).metrics | {"rx_app": len(sub1_events)})
    print("Sub2 metrics:", Client('dummy', b).metrics | {"rx_app": len(sub2_events)})