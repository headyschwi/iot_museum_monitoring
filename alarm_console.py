import json
import sys
import paho.mqtt.client as mqtt
import time

class AlarmConsole:
    def __init__(self, broker_address, broker_port, group_id):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.group_id = group_id
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

    def start(self):
        self.client.on_connect = self.on_connect
        self.client.connect(self.broker_address, self.broker_port, 60)
        self.client.loop_start()
        time.sleep(1)
        self.run_console()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Conectado ao Broker MQTT de endereco {self.broker_address}.")

    def run_console(self):
        print("Bem-vindo ao Alarm Console!")
        print("Digite 'ON' para ativar os alarmes de movimento ou 'OFF' para desativar.")
        while True:
            command = input("Digite o comando: ").strip().upper()
            if command == "ON" or command == "OFF":
                self.send_command(command)
            else:
                print("Comando inválido. Por favor digite 'ON' ou 'OFF'.")

    def send_command(self, command):
        topic = f"{self.group_id}_ALARM_CONTROL"
        payload = {"command": command}
        self.client.publish(topic, json.dumps(payload))
        print(f"Comando '{command}' enviado para a Unidade de Processamento de Dados.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python alarm_console.py <group_id>")
        sys.exit(1)

    group_id = sys.argv[1]

    broker_address = "192.168.1.66"  # Change to your broker's address
    broker_port = 1883  # Change to your broker's port

    alarm_console = AlarmConsole(broker_address, broker_port, group_id)
    alarm_console.start()
