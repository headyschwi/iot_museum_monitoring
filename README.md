# Sistema de Monitoramento Ambiental IoT para Museu

## Visão Geral

Este projeto simula uma solução IoT para monitoramento e controle automático dos parâmetros ambientais (temperatura, umidade, movimento) em várias salas de um museu. O sistema utiliza o protocolo MQTT para transferência de dados, processa dados de sensores em tempo real, armazena-os em um banco de dados InfluxDB e visualiza métricas chave em um painel Grafana. O objetivo é garantir que a temperatura e umidade em cada sala permaneçam dentro de intervalos saudáveis, enquanto previne acessos não autorizados por meio da detecção de movimento.

## Funcionalidades

- **Coleta de Dados em Tempo Real**: Simulação de dados de sensores de temperatura, umidade e movimento nas salas do museu.
- **Mensagens MQTT**: Publicação de dados dos sensores e inscrição para comandos dos atuadores via protocolo MQTT.
- **Processamento de Dados**: Detecta anomalias nos dados (temperatura/umidade fora do intervalo), aciona alarmes e gerencia os sistemas de ar condicionado e controle de umidade.
- **Integração com InfluxDB**: Armazena dados de sensores e eventos em um banco de dados de séries temporais.
- **Painel Grafana**: Visualiza os dados dos sensores, o status dos dispositivos e o consumo de energia.
- **Cálculo de Custo de Energia**: Acompanha o consumo de energia dos sistemas de ar condicionado e controle de umidade.

## Arquitetura do Sistema

O sistema é composto pelos seguintes componentes:

1. Sensores das Salas: Simulam sensores de temperatura, umidade e movimento em várias salas do museu. Os dados são publicados em um broker MQTT.
2. Broker MQTT: Gerencia a troca de mensagens entre publicadores (sensores) e assinantes (unidade de processamento de dados, central de controle).
3. Unidade de Processamento de Dados: Processa os dados dos sensores, detecta anomalias, envia alertas e armazena os dados no InfluxDB.
4. Central de Controle: Recebe alertas da unidade de processamento e gerencia os atuadores (ar condicionado, controle de umidade).
5. Console de Alarme: Permite o controle manual dos alarmes de detecção de movimento.
6. Depurador MQTT: Exibe todas as mensagens MQTT trocadas na rede.
7. Armazenamento: O banco de dados InfluxDB armazena todas as leituras dos sensores e eventos.
8. Painel de Controle: O painel Grafana exibe os dados em tempo real, históricos e o consumo de energia.

## Tecnologias Utilizadas

- Python: Linguagem de programação principal utilizada para simular as salas, processar dados e gerenciar a comunicação.
- MQTT (Mosquitto): Protocolo de mensagens para transferência de dados dos sensores e comandos de controle.
- InfluxDB: Banco de dados de séries temporais para armazenar leituras de sensores e eventos.
- Grafana: Plataforma de visualização de dados por meio de painéis personalizáveis.
- Raspberry Pi: Utilizado como o broker MQTT físico no sistema.

## Fluxo do Sistema

1. Coleta de Dados: Cada sala simula dados ambientais (temperatura, umidade, movimento), enviados ao broker MQTT como objetos JSON.
2. Processamento de Dados: A unidade de processamento analisa os dados, verifica se estão dentro dos intervalos saudáveis e armazena os dados no InfluxDB. Alertas são enviados à Central de Controle quando necessário.
3. Controle: A Central de Controle ajusta os atuadores (ar condicionado, controle de umidade) com base nos dados recebidos dos sensores e também lida com alertas de movimento.
4. Visualização: Os dados são visualizados no Grafana, com seções para monitoramento em tempo real, dados históricos e consumo de energia.

## Configuração

### Pré-requisitos

- Python 3.x
- Mosquitto MQTT Broker
- Conta no InfluxDB (plano gratuito)
- Conta no Grafana (plano gratuito)

### Configurando o Projeto

Este projeto utiliza um arquivo `config.ini` para armazenar a chave da API e as configurações do InfluxDB, permitindo que os usuários troquem essas informações sem precisar alterar o código.

Crie um arquivo `config.ini` na raiz do projeto com o seguinte formato:

```ini
[influxdb]
api_key = SEU_API_KEY
url = https://us-west-2-1.aws.cloud2.influxdata.com
org = sua-organizacao
bucket = seu-bucket
```

Certifique-se de não adicionar o arquivo `config.ini` ao repositório Git, mantendo-o em segurança e fora do controle de versão. Para isso, adicione o arquivo ao `.gitignore`:

```
config.ini
```

### Executando o Projeto

1. Simulação das Salas:
   ```bash
   python3 room.py {GroupID} {TEMP_TIME} {MOV_TIME}
   ```

2. Unidade de Processamento de Dados:
   ```bash
   python3 data_processing.py
   ```

3. Central de Controle:
   ```bash
   python3 control_central.py
   ```

4. Console de Alarme:
   ```bash
   python3 alarm_console.py
   ```

5. Depurador MQTT:
   ```bash
   python3 mqtt_debugger.py
   ```

### Configuração do InfluxDB

1. Crie uma conta no InfluxDB Cloud e configure um bucket e organização.
2. Atualize o arquivo `config.ini` com a chave da API e as configurações do InfluxDB.

### Configuração do Painel Grafana

1. Crie uma conta no Grafana Cloud e configure um painel para ler os dados do InfluxDB.
2. Configure os painéis para mostrar dados em tempo real, consumo de energia e tendências históricas.

## Painel Grafana

O painel Grafana é dividido em três seções:

1. Resumo: Mostra as principais leituras dos sensores e o status dos dispositivos de ar condicionado e controle de umidade.
2. Detalhes: Exibe os últimos valores dos sensores, intervalos saudáveis e dados históricos, incluindo médias móveis.
3. Energia: Visualiza o consumo de energia e o custo ao longo do tempo para cada sala.

![image](https://github.com/user-attachments/assets/46e67421-9007-4a72-978f-691587e3cab8)


## Estrutura do Projeto

```
.
├── room.py                # Simula dados de sensores da sala
├── data_processing.py     # Processa dados dos sensores e gerencia alarmes
├── control_central.py     # Gerencia atuadores e recebe alertas
├── alarm_console.py       # Interface do usuário para gerenciar alarmes de movimento
├── mqtt_debugger.py       # Depura mensagens MQTT
├── config.ini             # Arquivo de configuração do InfluxDB (não incluído no Git)
├── README.md              # Documentação do projeto
```

## Autores

Este projeto foi desenvolvido como parte da disciplina Sensing and Actuation Networks and Systems no DEI-FCTUC por Ederjofre Filho e Dalton Erthal.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.
