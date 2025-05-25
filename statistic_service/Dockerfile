FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    gcc \
    python3-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY statistic_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest

COPY proto/ ./proto/
COPY broker/ ./broker/
COPY statistic_service/ ./statistic_service/

ENV PYTHONPATH=/app:/app/proto:/app/broker
ENV CLICKHOUSE_URL=clickhouse://default:password@clickhouse:8123/default
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092

EXPOSE 50052

CMD sh -c "while ! curl -s 'http://clickhouse:8123/' >/dev/null; do sleep 2; done && python statistic_service/main.py"