FROM python:3.11-slim

WORKDIR /app

# Camada de dependências — invalida cache somente se requirements.txt mudar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Camada de código — invalida cache somente se main.py mudar
COPY main.py .

# Usuário sem privilégios para reduzir superfície de ataque
RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8000
ENV MQTT_BROKER_HOST=mosquitto
CMD ["python", "main.py"]

