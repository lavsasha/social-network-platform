FROM python:3.9-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/*
RUN curl -o /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && \
    chmod +x /usr/local/bin/wait-for-it.sh

WORKDIR /app

COPY proto/ ./proto/

COPY api_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api_gateway/ .
ENV PYTHONPATH=/app

EXPOSE 8080
CMD ["python", "app.py"]