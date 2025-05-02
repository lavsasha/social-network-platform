FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY post_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest

COPY proto/ ./proto/
COPY broker/ ./broker/

COPY post_service/ ./post_service/

ENV PYTHONPATH=/app

EXPOSE 50051

CMD ["python", "post_service/main.py"]