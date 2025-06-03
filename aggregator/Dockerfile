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

COPY aggregator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/ ./proto/
COPY aggregator/ ./

CMD ["python", "aggregator.py"]