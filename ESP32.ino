/* -----------------------------------------------------------------------------------
  PROJETO: Publicador MQTT de Sensores com ESP32 (Formato JSON)
  AUTOR: Lucas Augusto - 21/02/2026
  
  RESUMO: 
  Este código possibilita que o ESP32 atue como um dispositivo de Borda (Edge).
  Ele se conecta à rede local e ao Mosquitto MQTT, simulando a coleta de dados 
  climáticos (Temperatura e Umidade). Utiliza a biblioteca ArduinoJson para 
  empacotar os dados antes do envio, facilitando o consumo de dados por APIs Rest e 
  armazenamento de banco de dado NoSQL (MongoDB).
  -----------------------------------------------------------------------------------
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- Configurações de Wi-Fi ---
const char* ssid = "NOME_DA_SUA_REDE_WIFI";
const char* password = "SENHA_DO_WIFI";

// --- Configurações de MQTT ---
// Coloque o IP da máquina (servidor/computador) onde o Docker onde o Broker MQTT está rodando.
const char* mqtt_server = "IP_DO_SEU_SERVIDOR"; 
const int mqtt_port = 1883;

// Tópico definido no nosso main.py (FastAPI), apenas simulação para testes.
const char* topico_publicacao = "sensor/dht11/dados";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long ultimaMensagem = 0;
const long intervaloEnvio = 5000; // Envia dados a cada 5 segundos

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectado à rede: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Wi-Fi Conectado!");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // Entra em loop até estar ligado ao broker MQTT
  while (!client.connected()) {
    Serial.print("A tentativa de conexão MQTT...");
    // Cria um ID de cliente aleatório
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    // Tenta ligar
    if (client.connect(clientId.c_str())) {
      Serial.println("Conectado ao Broker MQTT!");
      // Aqui também poderia fazer um client.subscribe("topico/comando");
    } else {
      Serial.print("Falhou, rc=");
      Serial.print(client.state());
      Serial.println(" Tentar novamente em 5 segundos...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long tempoAtual = millis();
  if (tempoAtual - ultimaMensagem >= intervaloEnvio) {
    ultimaMensagem = tempoAtual;

    // --- Simulação de leitura de Sensor (Ex: DHT11) ---
    // Na prática, leria usando: float temp = dht.readTemperature();
    float temperatura = random(200, 350) / 10.0; 
    float humidade = random(400, 700) / 10.0;

    // --- Criação do JSON ---
    // Alinhado com a biblioteca ArduinoJson ensinada no 2º Semestre
    StaticJsonDocument<200> doc;
    doc["temperatura"] = temperatura;
    doc["humidade"] = humidade;
    doc["sensor"] = "ESP32_Sensor_1";

    // Serializa o JSON para uma string
    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);

    // --- Publicação no MQTT ---
    Serial.print("Mensagem publicada: ");
    Serial.println(jsonBuffer);
    
    client.publish(topico_publicacao, jsonBuffer);
  }
}
