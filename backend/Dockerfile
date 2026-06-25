FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend:/app
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl netcat-openbsd && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend /app/backend
COPY mlops /app/mlops
COPY load_tests /app/load_tests
RUN chmod +x /app/backend/scripts/start.sh /app/backend/scripts/start-dev.sh
EXPOSE 8000
CMD ["bash", "/app/backend/scripts/start.sh"]
