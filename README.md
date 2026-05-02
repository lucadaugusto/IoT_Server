# 🛰️ IoT Docker Gateway

Servidor IoT em Docker com Mosquitto (MQTT), FastAPI e MongoDB. Permite conectar dispositivos (como o ESP32), persistir dados em séries temporais e visualizar tudo em tempo real por meio de WebSockets e de uma página web.

A solução funciona como um gateway IoT completo, fazendo a ponte entre a Camada de Borda (Edge) e o Banco de Dados.

---

## 🚀 Funcionalidades

- **Broker Mosquitto MQTT** em execução.
- **Banco de Dados NoSQL (MongoDB)** configurado com segurança e otimizado para armazenamento de Séries Temporais (Time Series).
- **Aplicação FastAPI** com:
  - Cliente MQTT integrado rodando em *background*.
  - WebSockets para envio de dados em tempo real para o *frontend*.
  - API REST para publicar comandos e consultar o histórico de mensagens.
  - Swagger UI (`/docs`) para documentação e testes automáticos da API.

---

## 🎯 Objetivo

Este projeto serve como base para:

- Aulas e laboratórios de IoT (Internet das Coisas).
- Demonstrações práticas de integração entre Edge Computing e Cloud.
- Protótipos rápidos com ESP32 ou Arduino.
- Estudos de APIs REST, MQTT, persistência de dados e conteinerização.

---

## 🐳 Instalação do Docker no Ubuntu

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

## ⚙️ Configuração Inicial (Linux/Cloud)

Antes de executar os containers pela primeira vez, é necessário criar as pastas do Mosquitto e definir as permissões corretas para evitar erros de escrita:

```bash
sudo mkdir -p data log
```
```bash
sudo chown -R 1883:1883 data log
```

---

## 🐳 Inicialização do Docker Compose

Na pasta do projeto, execute o comando abaixo para construir e iniciar os containers em segundo plano:

```bash
sudo docker compose up -d --build
```
---

## 🔌 Liberação de Portas (Firewall)

Para que os serviços do projeto fiquem acessíveis externamente, certifique-se de que as seguintes portas estão liberadas no seu firewall (UFW, Security Groups da AWS, Regras de Rede GCP, etc.):

| Serviço | Porta | Descrição |
| :--- | :--- | :--- |
| **API / Backend** | `8000` | Comunicação com a interface e rotas REST |
| **MQTT Broker** | `1883` | Conexão de dispositivos via protocolo MQTT |
| **MongoDB** | `27017` | Acesso direto ao banco de dados (se necessário) |

### Comando para liberar via UFW (Linux)

Se você estiver utilizando o `ufw`, execute os comandos abaixo para permitir o tráfego de entrada:

```bash
sudo ufw allow 8000/tcp
sudo ufw allow 1883/tcp
sudo ufw allow 27017/tcp
sudo ufw reload
```

## 🌐 Acesso e Endpoints Úteis

Após o ambiente estar pronto, é possível acessar as seguintes funcionalidades através do navegador/browser:

- **Dashboard (Tempo Real):** `http://IP_Servidor:8000/` (Página HTML com WebSockets).
- **Testes da API (Swagger):** `http://IP_Servidor:8000/docs` (Ideal para simular envios JSON e testar rotas sem precisar do Postman).
- **Histórico de Dados:** `http://IP_Servidor:8000/api/historico?limite=50`
- **MongoDB (Acesso Externo):** Porta `27017` (Administrador: `admin` | Senha: `admin`).

*(**Nota:** Substituir `IP_Servidor` pelo IP da máquina onde os containers Docker estão rodando, ou por `localhost` se estiverem rodando na própria máquina).*

---

## 📄 Licença

Este projeto é disponibilizado sob a **Licença MIT**.

Foi desenvolvido com fins educacionais e é **livre para uso, modificação e distribuição** (acadêmica ou profissional). A única exigência é que o aviso de direitos autorais e os créditos aos criadores originais sejam incluídos em qualquer cópia ou modificação dos arquivos de código e do projeto.

Consulte o arquivo [LICENSE](LICENSE) para ler os termos completos.
