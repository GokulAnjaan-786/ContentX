FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend:/app/ai-services:/app/ai_services:/app/worker

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY backend /app/backend
COPY ai-services /app/ai-services
COPY ai_services /app/ai_services
COPY worker /app/worker

WORKDIR /app

CMD ["celery", "-A", "worker.celery_app.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
