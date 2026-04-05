import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator
import paho.mqtt.client as mqtt
import json
import threading
import asyncio
from typing import List, Union
from datetime import datetime
from pymongo import MongoClient

# --- Configurações MQTT ---
MQTT_BROKER    = os.getenv("MQTT_BROKER_HOST", "test.mosquitto.org")
MQTT_PORT      = 1883
MQTT_TOPIC_SUB = "v1/dispositivos/sensor/dados"  # Tópico padronizado (igual ao ESP32.ino)
MQTT_USER      = os.getenv("MQTT_USER")
MQTT_PASSWORD  = os.getenv("MQTT_PASSWORD")

# --- Configurações MongoDB ---
MONGO_URI  = os.getenv("MONGO_URI", "mongodb://admin:admin@localhost:27017/")
mongo_client = MongoClient(MONGO_URI)
db         = mongo_client["iot_database"]
collection = db["sensor_data"]

# --- Estado global thread-safe ---
_message_lock = threading.Lock()
last_received_message = {
    "topic": None,
    "payload": None,
    "timestamp": None,
    "status": "Aguardando dados..."
}

# --- Gerenciador de WebSockets ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self._lock:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Envia para todos os clientes e remove conexões mortas."""
        dead: List[WebSocket] = []
        with self._lock:
            connections = list(self.active_connections)
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        if dead:
            with self._lock:
                for conn in dead:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)

manager = ConnectionManager()
event_loop = None

# --- Callbacks MQTT ---

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Conectado ao Broker MQTT em {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC_SUB)
        print(f"Inscrito no tópico: {MQTT_TOPIC_SUB}")
    else:
        print(f"Falha na conexão MQTT, código: {rc}")

def on_message(client, userdata, msg):
    """
    Callback executado na thread interna do paho-mqtt.
    Valida que o payload é um JSON objeto (dict) antes de persistir.
    Usa threading.Lock para acesso seguro à variável global.
    """
    global last_received_message
    try:
        payload_str = msg.payload.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"Payload com encoding inválido: {e}")
        return

    # Validação: exige JSON bem-formado
    try:
        payload_data = json.loads(payload_str)
    except json.JSONDecodeError as e:
        print(f"Payload ignorado (JSON inválido): {e} | Raw: {payload_str[:120]}")
        return

    # Validação: exige objeto JSON (dict), não lista/string/número
    if not isinstance(payload_data, dict):
        print(f"Payload ignorado: esperado objeto JSON, recebido {type(payload_data).__name__}")
        return

    timestamp_now = datetime.utcnow()
    novo_estado = {
        "topic": msg.topic,
        "payload": payload_data,
        "timestamp": timestamp_now.isoformat(),
        "status": "Atualizado"
    }

    with _message_lock:
        last_received_message = novo_estado

    print(f"[{timestamp_now.isoformat()}] Mensagem recebida em '{msg.topic}': {payload_data}")

    try:
        collection.insert_one({
            "timestamp": timestamp_now,
            "topico": msg.topic,
            "dados": payload_data
        })
    except Exception as e:
        print(f"Erro ao persistir no MongoDB: {e}")

    if event_loop and not event_loop.is_closed():
        asyncio.run_coroutine_threadsafe(manager.broadcast(novo_estado), event_loop)

# --- Inicialização do Cliente MQTT ---
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except AttributeError:
    mqtt_client = mqtt.Client()

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

if MQTT_USER and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

# --- Lifespan: substitui os deprecated @app.on_event ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_loop
    event_loop = asyncio.get_running_loop()
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        print("MQTT loop iniciado.")
    except Exception as e:
        print(f"Erro ao conectar ao Broker MQTT: {e}")
    yield
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("MQTT desconectado.")

app = FastAPI(
    title="Gateway MQTT <-> REST API com MongoDB",
    lifespan=lifespan
)

# --- Modelos Pydantic ---

class MessagePayload(BaseModel):
    topic: str
    message: Union[str, dict]

    @field_validator("topic")
    @classmethod
    def topic_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("O campo 'topic' não pode ser vazio.")
        return v

# --- Endpoints REST ---

@app.get("/api/dados")
def get_mqtt_data():
    """Retorna o último dado recebido pelo subscriber MQTT."""
    with _message_lock:
        return dict(last_received_message)

@app.get("/api/historico")
def get_historico(limite: int = 50):
    """Retorna os últimos N registros do MongoDB, ordenados por timestamp decrescente."""
    if limite < 1 or limite > 1000:
        raise HTTPException(status_code=400, detail="O parâmetro 'limite' deve estar entre 1 e 1000.")
    dados = list(collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limite))
    return {"historico": dados}

@app.post("/api/publicar")
def post_mqtt_data(payload: MessagePayload):
    """Recebe um JSON via HTTP e publica no Broker MQTT."""
    try:
        msg_content = payload.message
        if isinstance(msg_content, dict):
            msg_content = json.dumps(msg_content)
        info = mqtt_client.publish(payload.topic, msg_content)
        info.wait_for_publish()
        return {"status": "Mensagem enviada com sucesso", "topic": payload.topic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao publicar: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
                #ws-status { font-weight: bold; }
                pre { text-align: left; background: #eee; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Gateway MQTT &harr; WebSocket</h1>
            <div class="card">
                <p>Status do WebSocket: <span id="ws-status" style="color:orange">Conectando...</span></p>
                <h3>Tópico: <code>v1/dispositivos/sensor/dados</code></h3>
                <h3>Último Dado Recebido:</h3>
                <pre id="data">Aguardando dados...</pre>
            </div>
            <script>
                var ws = new WebSocket("ws://" + window.location.host + "/ws");
                var statusSpan = document.getElementById("ws-status");
                ws.onopen = function() { statusSpan.innerText = "Conectado"; statusSpan.style.color = "green"; };
                ws.onmessage = function(event) { document.getElementById("data").innerText = JSON.stringify(JSON.parse(event.data), null, 2); };
                ws.onclose = function() { statusSpan.innerText = "Desconectado"; statusSpan.style.color = "red"; };
                ws.onerror = function() { statusSpan.innerText = "Erro de conexão"; statusSpan.style.color = "red"; };
            </script>
        </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

