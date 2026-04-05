FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8000
ENV MQTT_BROKER_HOST=mosquitto
CMD ["python", "main.py"]
