FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api_gateway.py .
EXPOSE 8080
CMD ["python", "api_gateway.py"]