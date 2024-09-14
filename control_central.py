import socket
import json
import datetime
import paho.mqtt.client as mqtt
import sys
import threading
from queue import Queue

class ControlCentral:
    def __init__(self, group_id, broker_address, broker_port, central_ip, central_port):
        self.group_id = group_id
        self.central_ip = central_ip
        self.central_port = central_port

        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.queue = Queue()

    def start(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, self.broker_port, 60)
        self.start_tcp_server()

    def start_tcp_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.central_ip, self.central_port))
        server_socket.listen(5)
        print(f"Bem-vindo ao Sistema de Controle Central ({self.group_id})")
        print(f"Servidor TCP iniciado em {self.central_ip}:{self.central_port}")
        print("Aguardando alarmes...")
        while True:
            client_socket, address = server_socket.accept()
            data = client_socket.recv(1024).decode()
            if data:
                alarm_data = json.loads(data)
                self.queue.put(alarm_data)  # Coloca os dados na fila
            client_socket.close()

    def on_connect(self, client, userdata, flags, rc):
        print("Conectado ao Broker MQTT com código de resultado", rc)
        client.subscribe("#")  # Subscreve a todos os tópicos

    def on_message(self, client, userdata, message):
        payload = json.loads(message.payload)
        # Implementar conforme necessário

    def send_mqtt_message(self, room_number, control_type, action):
        topic = f"{self.group_id}_ACT"
        payload = {
            "numero_sala": room_number,
            "tipo_controle": control_type,
            "acao": action,
            "timestamp": datetime.datetime.now().isoformat()
        }

        try:
            self.client.publish(topic, json.dumps(payload)) # Envia a mensagem para o tópico
        except Exception as e:
            print(f"Erro ao enviar mensagem para o tópico {topic}: {e}")
            print("Tentando reconectar...")
            self.client.reconnect()

    def handle_alarm(self, alarm_data):
        print("\n--- Alarme Recebido ---")
        self.print_alarm(alarm_data)

        room_number = alarm_data["numero_sala"]
        control_type = alarm_data["tipo_controle"]
        action = alarm_data["acao"]
        response_topic = alarm_data["response_topic"]

        if control_type == "AC":
            if action == "DOWN":
                print(f"Alarme de temperatura alta na sala {room_number}, ligando ar-condicionado para diminuir a temperatura.")
            elif action == "UP":
                print(f"Alarme de temperatura baixa na sala {room_number}, ligando ar-condicionado para aumentar a temperatura.")
            else:
                print(f"Alarme de temperatura ideal na sala {room_number}, desligando ar-condicionado.")
        
        elif control_type == "HC":
            if action == "DOWN":
                print(f"Alarme de umidade alta na sala {room_number}, ligando controlador de umidade.")
            elif action == "UP":
                print(f"Alarme de umidade baixa na sala {room_number}, ligando controlador de umidade.")
            else:
                print(f"Alarme de umidade ideal na sala {room_number}, desligando controlador de umidade.")

        elif control_type == "DISCONNECT":
            print(f"{room_number} desconectou-se do sistema, desligando controladores..")

        elif control_type == "ALARM":
            if action == "MOVEMENT":
                print(f"Alarme de movimento na sala {room_number}, acionando alarme.")
                ## Implementar alarme de movimento
                
        self.send_mqtt_message(room_number, control_type, action)

    def print_alarm(self, alarm_data):
        print(f"Sala: {alarm_data['numero_sala']}")
        print(f"Tipo de Controle: {alarm_data['tipo_controle']}")
        print(f"Ação: {alarm_data['acao']}")
        print(f"Timestamp: {alarm_data['timestamp']}")

    def handle_alarm_queue(self):
        while True:
            if not self.queue.empty():
                alarm_data = self.queue.get()  # Pega o próximo item da fila
                self.handle_alarm(alarm_data)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Por favor, forneça o ID do grupo como argumento.")
        sys.exit(1)
    
    group_id = sys.argv[1]
    broker_address = "192.168.1.66"
    broker_port = 1883

    central_ip = "192.168.1.66"
    central_port = 5000

    control_central = ControlCentral(group_id, broker_address, broker_port, central_ip, central_port)
    threading.Thread(target=control_central.handle_alarm_queue).start()  # Inicia o tratamento da fila em uma thread separada
    control_central.start()
