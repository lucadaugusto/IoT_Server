## 🛰️ **IoT Docker Gateway**

Este repositório apresenta um exemplo simples de arquitetura IoT utilizando Docker, Mosquitto (MQTT) e uma aplicação Python/FastAPI capaz de publicar e consumir mensagens MQTT.
A solução funciona como um pequeno gateway IoT, permitindo testes com ESP32 ou qualquer cliente MQTT.

## 🚀 **Funcionalidades**

Broker Mosquitto MQTT em container
Aplicação FastAPI com:
  - API REST para publicar e consultar mensagens
  - Cliente MQTT integrado

## 🎯 **Objetivo**

Este projeto serve como base para:
  - Aulas e laboratórios de IoT
  - Demonstrações práticas
  - Protótipos rápidos com ESP32
  - Estudos de APIs REST, MQTT e conteinerização

## 🐳 **Instalação do Docker no Ubuntu**

Após baixar ou clonar este repositório, torne o script executável e execute:

```bash
chmod +x install_docker.sh
sudo ./install_docker.sh
```
## 🐳 **Inicializando o Docker Compose**

Na raiz do projeto, execute o comando abaixo para construir e subir os containers em segundo plano:

```bash
docker compose up -d
```

## 📄 **Licença**
  - MIT License — livre para uso acadêmico e profissional.
