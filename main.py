import os
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import paho.mqtt.client as mqtt
import json
import threading
import asyncio
from typing import List

# --- Configurações ---
# Se a variável de ambiente existir (no Docker), usa ela via 'mosquitto'.
# Se não, usa o 'test.mosquitto.org' ou 'localhost' para testes locais.
MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "test.mosquitto.org") 
MQTT_PORT = 1883
MQTT_TOPIC_SUB = "sensor/dht11/dados"

app = FastAPI(title="Gateway MQTT <-> REST API")

# Variável global para armazenar a última mensagem recebida
last_received_message = {
    "topic": None,
    "payload": None,
    "status": "Aguardando dados..."
}

# --- Gerenciador de WebSockets ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()
event_loop = None # Para acessar o loop principal da thread do MQTT

# --- Cliente MQTT ---

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Conectado ao Broker MQTT com código: {rc}")
    client.subscribe(MQTT_TOPIC_SUB)

def on_message(client, userdata, msg):
    global last_received_message
    try:
        payload_str = msg.payload.decode()
        # Tenta converter para JSON, se não der, mantém como string
        try:
            payload_data = json.loads(payload_str)
        except json.JSONDecodeError:
            payload_data = payload_str
            
        last_received_message = {
            "topic": msg.topic,
            "payload": payload_data,
            "status": "Atualizado"
        }
        print(f"Mensagem recebida via MQTT: {payload_data}")
        
        # Envia para os WebSockets conectados (Thread Safe)
        if event_loop:
            asyncio.run_coroutine_threadsafe(manager.broadcast(last_received_message), event_loop)
    except Exception as e:
        print(f"Erro ao processar mensagem MQTT: {e}")

# Inicialização do Cliente MQTT (com suporte a versões novas e antigas da lib)
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except AttributeError:
    mqtt_client = mqtt.Client()

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# --- Eventos da API (Startup/Shutdown) ---

@app.on_event("startup")
async def start_mqtt():
    """Inicia a conexão MQTT em background quando a API sobe."""
    global event_loop
    event_loop = asyncio.get_running_loop()
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start() # Roda em uma thread separada
    except Exception as e:
        print(f"Erro na conexão MQTT: {e}")

@app.on_event("shutdown")
def stop_mqtt():
    """Encerra a conexão MQTT quando a API cai."""
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

# --- Modelos de Dados (Pydantic) ---

class MessagePayload(BaseModel):
    topic: str
    message: str | dict # Aceita string ou dicionário (JSON)

# --- Endpoints REST ---

@app.get("/api/dados")
def get_mqtt_data():
    """
    Método GET: Retorna o último dado recebido pelo subscriber MQTT.
    Equivalente a 'consumir' o dado do sensor.
    """
    return last_received_message

@app.post("/api/publicar")
def post_mqtt_data(payload: MessagePayload):
    """
    Método POST: Recebe um JSON via HTTP e publica no Broker MQTT.
    Equivalente a 'enviar comando' para um atuador.
    """
    try:
        msg_content = payload.message
        # Se for dict, converte para string JSON antes de enviar
        if isinstance(msg_content, dict):
            msg_content = json.dumps(msg_content)
            
        info = mqtt_client.publish(payload.topic, msg_content)
        info.wait_for_publish() # Garante que saiu do cliente
        
        return {"status": "Mensagem enviada com sucesso", "topic": payload.topic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao publicar: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket: Envia dados em tempo real para o cliente.
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Mantém a conexão aberta
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Frontend (Página Inicial) ---

@app.get("/", response_class=HTMLResponse)
async def get():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Gateway IoT - Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; }
                .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; }
                h1 { color: #333; }
                #status { color: orange; font-weight: bold; }
                pre { text-align: left; background: #eee; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Gateway MQTT <-> WebSocket</h1>
            <div class="card">
                <p>Status do WebSocket: <span id="ws-status">Desconectado</span></p>
                <h3>Último Dado Recebido:</h3>
                <pre id="data">Aguardando dados...</pre>
            </div>
            <script>
                var ws = new WebSocket("ws://" + window.location.host + "/ws");
                var statusSpan = document.getElementById("ws-status");
                
                ws.onopen = function() {
                    statusSpan.innerText = "Conectado";
                    statusSpan.style.color = "green";
                };
                
                ws.onmessage = function(event) {
                    var data = JSON.parse(event.data);
                    document.getElementById("data").innerText = JSON.stringify(data, null, 2);
                };
                
                ws.onclose = function() {
                    statusSpan.innerText = "Desconectado";
                    statusSpan.style.color = "red";
                };
            </script>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Roda o servidor Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
