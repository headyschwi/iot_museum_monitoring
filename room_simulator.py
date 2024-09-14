import paho.mqtt.client as mqtt
import json
import random
import time
import sys
import threading
import datetime

class RoomSimulator:
    def __init__(self, broker_address, broker_port, group_id, temp_time, mov_time, room_id):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.group_id = group_id
        self.room_id = room_id
        self.temp_time = temp_time
        self.mov_time = mov_time
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.ac_funcionando = False
        self.hc_funcionando = False

    def start(self):
        self.temperatura = random.uniform(20, 25)
        self.umidade = random.uniform(40, 60)
        self.movimento = 0

        self.hc_acao = None
        self.ac_acao = None

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, self.broker_port, 60)

        threading.Thread(target=self.client.loop_forever).start()
        time.sleep(3)
        threading.Thread(target=self.simulate_room_data).start()
        threading.Thread(target=self.simulate_intrusion).start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Conectado ao Broker MQTT endereco {self.broker_address}")
        self.client.subscribe(f"{self.group_id}_ACT")

    def on_message(self, client, userdata, message):
        payload = json.loads(message.payload)
        tipo_controle = payload.get("tipo_controle")

        if payload.get("numero_sala") != self.room_id:
            return

        if tipo_controle == "AC":
            if payload.get("acao") == "UP" or payload.get("acao") == "DOWN":
                self.ac_funcionando = True
                self.ac_acao = payload.get("acao")

            elif payload.get("acao") == "OFF":
                self.ac_funcionando = False
                self.ac_acao = None

        elif tipo_controle == "HC":
            if payload.get("acao") == "UP" or payload.get("acao") == "DOWN":
                self.hc_funcionando = True
                self.hc_acao = payload.get("acao")

            elif payload.get("acao") == "OFF":
                self.hc_funcionando = False
                self.hc_acao = None

    def simulate_room_data(self):
        while True:
            self.temperatura = self.simulate_temperature()
            self.umidade = self.simulate_humidity()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.publish_room_data(self.temperatura, self.umidade, self.movimento, timestamp)
            time.sleep(self.temp_time)

    def simulate_temperature(self):
        if self.ac_funcionando:
            if self.ac_acao == "DOWN":
                self.temperatura -= 0.5
            elif self.ac_acao == "UP":
                self.temperatura += 0.5
        else:
            self.temperatura += random.uniform(-0.1, 0.5)

        return self.temperatura
        
    def simulate_humidity(self):
        if self.hc_funcionando:
            if self.hc_acao == "DOWN":
                self.umidade -= 5
            elif self.hc_acao == "UP":
                self.umidade += 5
        else:
            self.umidade += random.uniform(-5, 10)
        return max(min(self.umidade, 100), 0)

    def simulate_intrusion(self):
        while True:
            time.sleep(self.mov_time)
            if self.movimento == 0:
                self.movimento = 1
            else:
                self.movimento = 0

    def publish_room_data(self, temperatura, umidade, movimento, timestamp):
        dados_sala = {
            "temperatura": round(temperatura, 2),
            "umidade": round(umidade, 2),
            "movimento": movimento,
            "ac_funcionando": int(self.ac_funcionando),
            "hc_funcionando": int(self.hc_funcionando),
            "tipo_sensor": 1,
            "numero_sala": self.room_id,
            "timestamp": timestamp
        }
        self.client.publish(f"{self.group_id}_ROOM_DATA", json.dumps(dados_sala))
        print(f"{timestamp}: Temperatura: {dados_sala['temperatura']}°C, Umidade: {dados_sala['umidade']}%, Movimento: {dados_sala['movimento']}, AC: {dados_sala['ac_funcionando']}, HC: {dados_sala['hc_funcionando']}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py <group_id> <temp_time> <mov_time> <room_id>")
        sys.exit(1)

    broker_address = "192.168.1.66"
    broker_port = 1883
    group_id = sys.argv[1]
    temp_time = int(sys.argv[2])
    mov_time = int(sys.argv[3])
    room_id = int(sys.argv[4])

    try:
        simulator = RoomSimulator(broker_address, broker_port, group_id, temp_time, mov_time, room_id)
        simulator.start()
    except Exception as e:
        print("Erro ao iniciar a simulação:", e)
