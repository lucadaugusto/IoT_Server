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
sudo git clone https://github.com/lucadaugusto/IoT_Server
```
```bash
cd IoT_Server
```
```bash
sudo chmod +x install_docker.sh
```
```bash
sudo ./install_docker.sh
```
## Configuração Inicial (Linux/Cloud)
Antes de subir os containers pela primeira vez, você precisa criar as pastas do Mosquitto e dar a permissão correta para evitar erros de escrita:

```bash
sudo mkdir -p data log
```
```bash
sudo chown -R 1883:1883 data log
```
## 🐳 **Inicializando o Docker Compose**

Na raiz do projeto, execute o comando abaixo para construir e subir os containers em segundo plano:

```bash
sudo docker compose up -d
```

## 📄 **Licença**

Este projeto é disponibilizado sob a **Licença MIT**. 

Ele foi desenvolvido com propósitos educacionais e é **livre para uso, modificação e distribuição** (académica ou profissional). A única exigência é que o aviso de direitos de autor e os créditos aos criadores originais sejam incluídos em qualquer cópia ou modificação do código.

Veja o ficheiro [LICENSE](LICENSE) para ler os termos completos.
