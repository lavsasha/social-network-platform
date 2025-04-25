FROM python:3.9-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/* \

WORKDIR /app

COPY broker/ ./broker/
COPY user_service/ ./user_service/
COPY user_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
WORKDIR /app/user_service
CMD ["python", "user_service.py"]