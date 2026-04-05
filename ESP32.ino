/* -----------------------------------------------------------------------------------
  PROJETO: Publicador MQTT de Sensores com ESP32 (Formato JSON)
  AUTOR: Lucas Augusto - 21/02/2026

  RESUMO:
  Este código possibilita que o ESP32 atue como um dispositivo de Borda (Edge).
  Ele se conecta à rede local e ao Mosquitto MQTT, simulando a coleta de dados
  climáticos (Temperatura e Umidade). Utiliza a biblioteca ArduinoJson para
  empacotar os dados antes do envio, facilitando o consumo de dados por APIs Rest e
  armazenamento de banco de dado NoSQL (MongoDB).

  MELHORIAS (Refatoração):
  - Tópico padronizado para v1/dispositivos/sensor/device1/dados (alinhado ao main.py)
  - Reconexão Wi-Fi e MQTT não-bloqueante usando millis() (sem delay() nos loops)
  - Timeout de Wi-Fi com reinicialização automática via ESP.restart()
  -----------------------------------------------------------------------------------
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- Configurações de Wi-Fi ---
const char* ssid     = "NOME_DA_SUA_REDE_WIFI";
const char* password = "SENHA_DO_WIFI";

// --- Configurações de MQTT ---
const char* mqtt_server = "IP_DO_SEU_SERVIDOR";
const int   mqtt_port   = 1883;

// Tópico: cada aluno troca "device1" pelo seu dispositivo
// Exemplos: v1/dispositivos/sensor/device1/dados
//           v1/dispositivos/sensor/device2/dados
//           v1/dispositivos/sensor/device3/dados
const char* topico_publicacao = "v1/dispositivos/sensor/device1/dados";

WiFiClient   espClient;
PubSubClient client(espClient);

unsigned long ultimaMensagem      = 0;
unsigned long ultimaTentativaMQTT = 0;
const long    intervaloEnvio      = 5000;
const long    intervaloReconexao  = 5000;
const long    timeoutWifi         = 20000;

void setup_wifi() 
{
  delay(10);
  Serial.print("Conectando à rede: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED)
  {
    if (millis() - inicio >= timeoutWifi) 
    {
      Serial.println("\nTimeout Wi-Fi. Reiniciando...");
      ESP.restart();
    }
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Conectado! IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() 
{
  unsigned long agora = millis();
  if (agora - ultimaTentativaMQTT < intervaloReconexao) return;
  ultimaTentativaMQTT = agora;
  Serial.print("Tentando conexão MQTT...");
  String clientId = "ESP32Client-";
  clientId += String(random(0xffff), HEX);
  if (client.connect(clientId.c_str())) 
  {
    Serial.println(" Conectado!");
  } 
  else 
  {
    Serial.print(" Falhou rc=");
    Serial.print(client.state());
    Serial.println(" — nova tentativa em 5s");
  }
}

void setup() 
{
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() 
{
  if (!client.connected()) 
  {
    reconnect();
    return;
  }
  client.loop();
  unsigned long tempoAtual = millis();
  if (tempoAtual - ultimaMensagem >= intervaloEnvio) 
  {
    ultimaMensagem = tempoAtual;
    float temperatura = random(200, 350) / 10.0;
    float humidade    = random(400, 700) / 10.0;
    StaticJsonDocument<200> doc;
    doc["temperatura"] = temperatura;
    doc["humidade"]    = humidade;
    doc["sensor"]      = "ESP32_Sensor_1";
    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);
    Serial.print("Publicando em [");
    Serial.print(topico_publicacao);
    Serial.print("]: ");
    Serial.println(jsonBuffer);
    client.publish(topico_publicacao, jsonBuffer);
  }
}
