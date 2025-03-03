FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY user_service.py models.py .
EXPOSE 5000
CMD ["python", "user_service.py"]