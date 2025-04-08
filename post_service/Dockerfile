FROM python:3.9-slim
WORKDIR /app
COPY post_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest
COPY . .
COPY proto/ ./proto/
EXPOSE 50051
CMD ["python", "post_service/main.py"]