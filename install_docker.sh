#!/bin/bash
# -----------------------------------------------------------------------
# install_docker.sh — Instalação do Docker + Docker Compose no Ubuntu
# Compatível com: Ubuntu 20.04, 22.04, 24.04 | amd64, arm64
# Uso: bash install_docker.sh
# -----------------------------------------------------------------------
set -e  # Para imediatamente se qualquer comando falhar

# --- Detecta usuário atual (funciona em AWS, GCP, Azure e máquinas locais) ---
USUARIO="${SUDO_USER:-$USER}"

echo "==> Atualizando pacotes..."
sudo apt-get update -y

echo "==> Instalando dependências..."
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# --- Adiciona chave GPG oficial do Docker (método atual — sem apt-key) ---
echo "==> Adicionando chave GPG do Docker..."
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# --- Adiciona repositório detectando versão e arquitetura automaticamente ---
echo "==> Adicionando repositório Docker..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "==> Instalando Docker Engine e Docker Compose..."
sudo apt-get update -y
sudo apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-compose-plugin

# --- Adiciona o usuário atual ao grupo docker ---
echo "==> Adicionando usuário '$USUARIO' ao grupo docker..."
sudo usermod -aG docker "$USUARIO"

# --- Habilita Docker para iniciar automaticamente no boot ---
sudo systemctl enable docker
sudo systemctl start docker

# --- Verifica instalação ---
echo ""
echo "==> Versões instaladas:"
docker --version
docker compose version

echo ""
echo "Docker instalado com sucesso!"

# --- Aplica permissões de grupo sem precisar reconectar via SSH ---
echo "==> Aplicando permissões do grupo docker na sessão atual..."
exec newgrp docker
