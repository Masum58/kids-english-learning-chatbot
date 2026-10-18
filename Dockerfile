FROM python:3.12-slim

WORKDIR /app

# Install curl for container health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and frontend static assets
COPY app/ ./app/
COPY frontend/ ./frontend/

# Expose port (default 8000)
EXPOSE 8000

# Launch uvicorn listening on ${PORT:-8000} to adapt seamlessly to Render/Railway/Fly/Local
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
