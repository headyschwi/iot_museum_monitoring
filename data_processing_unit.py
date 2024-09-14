import threading
import paho.mqtt.client as mqtt
import json
import socket
from influxdb_client_3 import InfluxDBClient3, Point
import datetime
import configparser

class DataProcessor:
    def __init__(self, broker_address, broker_port, central_ip, central_port, influx_token, influx_org, influx_host, influx_bucket, group_id):
        self.group_id = group_id
        self.broker_address = broker_address
        self.broker_port = broker_port
        
        self.central_ip = central_ip
        self.central_port = central_port
        
        self.influx_client = InfluxDBClient3(host=influx_host, token=influx_token, org=influx_org)
        self.influx_bucket = influx_bucket
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.config = self.read_config()

        self.alarm = True
        self.rooms = {}
        self.connected_rooms = []  # Lista para armazenar os números das salas conectadas

    def read_config(self):
        config = {}
        with open("intervals.cfg", "r") as file:
            for line in file:
                values = line.strip().split()
                config["temperature"] = {"low": float(values[0]), "high": float(values[1]), "ideal": float(values[2])}
                values = next(file).strip().split()
                config["humidity"] = {"low": float(values[0]), "high": float(values[1]), "ideal": float(values[2])}
        return config

    def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, self.broker_port, 60)
        
        threading.Thread(target=self.client.loop_forever).start()
        threading.Thread(target=self.check_connected_rooms).start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Conectado ao Broket MQTT endereco {self.broker_address}")
        client.subscribe("#")  # Subscreve a todos os tópicos

    def on_message(self, client, userdata, message):
        payload = json.loads(message.payload)
        topic = message.topic
        if topic == f"{self.group_id}_ROOM_DATA":
            self.process_sensor_data(payload, f"{self.group_id}_ACT")

        elif topic == "OTHER_ROOMS":
            self.process_sensor_data(payload, f"{self.group_id}_OTHER_ROOMS_ACT")

        elif topic == f"{self.group_id}_ALARM_CONTROL":
            self.process_alarm_control(payload, f"{self.group_id}_ALARM_ACT")

    def check_connected_rooms(self):
        while True:
            for room_number in self.connected_rooms.copy():  # Faz uma cópia da lista
                last_update = datetime.datetime.strptime(self.rooms[room_number]["last_update"], "%Y-%m-%d %H:%M:%S")
                current_time = datetime.datetime.now()
                time_diff = current_time - last_update
                if time_diff.total_seconds() > 15:
                    self.rooms[room_number]["connected"] = False
                    self.connected_rooms.remove(room_number)

            for room_number in self.connected_rooms.copy():
                if not self.rooms[room_number]["connected"]:
                    self.send_disconnect_alert(room_number)

                    point = (
                        Point("room_status")
                        .tag("room_number", room_number)
                        .field("connected", False)
                    )

                    self.influx_client.write(database=self.influx_bucket, record=point)


    def process_sensor_data(self, data, response_topic):
        room_number = data["numero_sala"]
        temperature = data["temperatura"]
        humidity = data["umidade"]
        sensor_type = data["tipo_sensor"]
        ac_funcionando = data["ac_funcionando"]
        hc_funcionando = data["hc_funcionando"]
        movement = data["movimento"]
        timestamp = data["timestamp"]

        if movement and self.alarm:
            alarm_data = {"numero_sala": room_number, "tipo_controle": "ALARM", "acao": "MOVEMENT", "response_topic": response_topic, "timestamp": timestamp}
            self.send_to_central(alarm_data)

            point = (
                Point("alarm_data")
                .tag("room_number", room_number)
                .field("intrusion", True)
            )

            self.influx_client.write(database=self.influx_bucket, record=point)

        else:
            point = (
                Point("alarm_data")
                .tag("room_number", room_number)
                .field("intrusion", False)
            )

            self.influx_client.write(database=self.influx_bucket, record=point)

        if sensor_type != 1 and sensor_type != 2:
            alarm_data = {"numero_sala": room_number, "tipo_controle": "DATA", "acao": "DESCART", "response_topic": response_topic, "timestamp": timestamp}
            self.send_to_central(alarm_data)

            point = (
                Point("invalid_data")
                .tag("room_number", room_number)
                .field("invalid_data", True)
            )

            self.influx_client.write(database=self.influx_bucket, record=point)

            return

        if room_number not in self.rooms:
            self.rooms[room_number] = {
                "temperature": temperature,
                "humidity": humidity,
                "last_update": timestamp,
                "hc_cost": 0,
                "ac_cost": 0,
                "ac_power_consumption": 0,
                "hc_power_consumption": 0,
                "connected": True,
                "ac_funcionando": ac_funcionando,
                "hc_funcionando": hc_funcionando,
                "movement": movement,
            }
            self.connected_rooms.append(room_number)  # Adiciona a sala à lista de salas conectadas

            point = (
                Point("room_status")
                .tag("room_number", room_number)
                .field("connected", True)
            )

            self.influx_client.write(database=self.influx_bucket, record=point)
        
        else:
            last_update = datetime.datetime.strptime(self.rooms[room_number]["last_update"], "%Y-%m-%d %H:%M:%S")
            current_update = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_diff = current_update - last_update

            if ac_funcionando:
                self.rooms[room_number]["ac_cost"] += time_diff.total_seconds() / 3600 * 3 * 0.15  # Calculating cost based on power consumption (Watts)
                self.rooms[room_number]["ac_power_consumption"] += time_diff.total_seconds() / 3600 * 3000  # Calculating power consumption (Watts)
            
            if hc_funcionando:
                self.rooms[room_number]["hc_cost"] += time_diff.total_seconds() / 3600 * 1 * 0.15  # Calculating cost based on power consumption (Watts)
                self.rooms[room_number]["hc_power_consumption"] += time_diff.total_seconds() / 3600 * 1000  # Calculating power consumption (Watts)

            self.rooms[room_number]["temperature"] = temperature
            self.rooms[room_number]["humidity"] = humidity
            self.rooms[room_number]["last_update"] = timestamp
            self.rooms[room_number]["connected"] = True
            self.rooms[room_number]["ac_funcionando"] = ac_funcionando
            self.rooms[room_number]["hc_funcionando"] = hc_funcionando
            self.rooms[room_number]["movement"] = movement
            self.connected_rooms.append(room_number)  # Adiciona a sala à lista de salas conectadas

            

        if sensor_type == 1 or sensor_type == 2:
            if sensor_type == 2:
                temperature = (temperature - 32) * 5 / 9  # Conversão de Fahrenheit para Celsius
            if self.config:
                if temperature > self.config["temperature"]["high"] and not ac_funcionando:
                    print(f"{timestamp}: Alta temperatura registrada na sala {room_number}, enviando comando para a central ligar o ar condicionado.")
                    self.send_ac_command(room_number, "DOWN", self.config["temperature"]["ideal"], response_topic)

                elif temperature < self.config["temperature"]["low"] and not ac_funcionando:
                    print(f"{timestamp}: Baixa temperatura registrada na sala {room_number}, enviando comando para a central ligar o ar condicionado.")
                    self.send_ac_command(room_number, "UP", self.config["temperature"]["ideal"], response_topic)

                elif temperature > self.config["temperature"]["low"]+3 and temperature < self.config["temperature"]["high"]-3 and ac_funcionando:
                    print(f"{timestamp}: Temperatura ideal registrada na sala {room_number}, enviando comando para a central desligar o ar condicionado.")
                    self.send_ac_command(room_number, "OFF", self.config["temperature"]["ideal"], response_topic)

                if humidity > self.config["humidity"]["high"] and not hc_funcionando:
                    print(f"{timestamp}: Alta umidade registrada na sala {room_number}, enviando comando para a central diminuir a umidade.")
                    self.send_hc_command(room_number, "DOWN", self.config["humidity"]["ideal"], response_topic)

                elif humidity < self.config["humidity"]["low"] and not hc_funcionando:
                    print(f"{timestamp}: Baixa umidade registrada na sala {room_number}, enviando comando para a central aumentar a umidade.")
                    self.send_hc_command(room_number, "UP", self.config["humidity"]["ideal"], response_topic)

                elif humidity > self.config["humidity"]["low"]+5 and humidity < self.config["humidity"]["high"]-5 and hc_funcionando:
                    print(f"{timestamp}: Umidade ideal registrada na sala {room_number}, enviando comando para a central desligar o controlador de umidade.")
                    self.send_hc_command(room_number, "OFF", self.config["humidity"]["ideal"], response_topic)

            # Salva os dados no InfluxDB
            self.update_rooms_database(room_number)

    def process_alarm_control(self, data, response_topic):
        command = data["command"]
        for room_number in self.connected_rooms:  # Itera sobre as salas conectadas
            if command == "ON":
                self.alarm = True
                print("Alarme de movimento ativado.")
            elif command == "OFF":
                self.alarm = False
                print("Alarme de movimento desativado.")

            data = {"numero_sala": room_number, "tipo_controle": "ALARM", "acao": "OFF", "response_topic": response_topic, "timestamp": datetime.datetime.now().isoformat()}
            self.send_to_central(data)

    def send_ac_command(self, room_number, action, ideal_value, response_topic):
        ac_data = {"numero_sala":room_number, "tipo_controle": "AC", "acao": action, "valor_ideal": ideal_value, "response_topic": response_topic, "timestamp": datetime.datetime.now().isoformat()}
        self.send_to_central(ac_data)

    def send_hc_command(self, room_number, action, ideal_value, response_topic):
        hc_data = {"numero_sala":room_number, "tipo_controle": "HC", "acao": action, "valor_ideal": ideal_value, "response_topic": response_topic, "timestamp": datetime.datetime.now().isoformat()}
        self.send_to_central(hc_data)

    def send_to_central(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as central_socket:
            central_socket.connect((self.central_ip, self.central_port))
            central_socket.send(json.dumps(data).encode())

    def send_disconnect_alert(self, room_number):
        data = {"numero_sala": room_number, "tipo_controle": "DISCONNECT", "acao": "DISCONNECT", "response_topic": f"{self.group_id}_ACT", "timestamp": datetime.datetime.now().isoformat()}
        self.send_to_central(data)
    
    def update_rooms_database(self, room_number):
        temperature = self.rooms[room_number]["temperature"]
        humidity = self.rooms[room_number]["humidity"]
        ac_cost = self.rooms[room_number]["ac_cost"]
        hc_cost = self.rooms[room_number]["hc_cost"]
        ac_power_consumption = self.rooms[room_number]["ac_power_consumption"]
        hc_power_consumption = self.rooms[room_number]["hc_power_consumption"]
        ac_funcionando = self.rooms[room_number]["ac_funcionando"]
        hc_funcionando = self.rooms[room_number]["hc_funcionando"]
        movement = self.rooms[room_number]["movement"]
        connected = self.rooms[room_number]["connected"]

        point = (
            Point("room_data")
            .tag("room_number", room_number)
            .field("temperature", float(temperature))
            .field("humidity", float(humidity))
            .field("ac_cost", float(ac_cost))
            .field("hc_cost", float(hc_cost))
            .field("ac_power_consumption", float(ac_power_consumption))
            .field("hc_power_consumption", float(hc_power_consumption))
            .field("ac_funcionando", ac_funcionando)
            .field("hc_funcionando", hc_funcionando)
            .field("connected", connected)
            .field("movement", movement)
            .field("alarm", self.alarm)
        )

        self.influx_client.write(database=self.influx_bucket, record=point)

if __name__ == "__main__":
    # Configurações iniciais
    group_id = 1
    broker_address = "192.168.1.66"
    broker_port = 1883

    central_ip = "192.168.1.66"
    central_port = 5000

    config = configparser.ConfigParser()
    config.read("config.ini")

    influx_api_key = config['influxdb']['api_key']
    influx_url = config['influxdb']['url']
    influx_org = config['influxdb']['org']
    influx_bucket = config['influxdb']['bucket']

    processor = DataProcessor(broker_address, broker_port, central_ip, central_port, influx_api_key, influx_org, influx_url, influx_bucket, group_id)
    processor.start()
