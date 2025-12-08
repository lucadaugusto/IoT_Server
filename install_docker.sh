#!/bin/bash
# Script de instalação do Docker no Ubuntu

# Atualiza pacotes
sudo apt update

# Instala dependências
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Adiciona a chave GPG oficial do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Adiciona o repositório estável do Docker
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

# Atualiza novamente
sudo apt update

# Exibe informações sobre o pacote Docker
apt-cache policy docker-ce

# Instala o Docker
sudo apt install -y docker-ce

# Mostra o status do serviço Docker
sudo systemctl status docker
