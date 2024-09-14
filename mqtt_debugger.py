import paho.mqtt.client as mqtt
import datetime

class MQTTDebugger:
    def __init__(self, broker_address, broker_port):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

    def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, self.broker_port, 60)
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT Broker with result code", rc)
        client.subscribe("#")  # Subscribe to all topics on connect

    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode("utf-8")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}]:[{topic}]:[{payload}]")

if __name__ == "__main__":
    broker_address = "192.168.1.66"  # Change to your broker's address
    broker_port = 1883  # Change to your broker's port

    debugger = MQTTDebugger(broker_address, broker_port)
    debugger.start()
