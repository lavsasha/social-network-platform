FROM python:3.9-slim
WORKDIR /app

# Копируем брокер из корня проекта
COPY broker/ ./broker/

# Копируем зависимости
COPY user_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем сам сервис
COPY user_service/ .

EXPOSE 5000
CMD ["python", "user_service.py"]