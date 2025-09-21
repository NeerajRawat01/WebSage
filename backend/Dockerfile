# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium) if enabled at runtime
RUN python -m playwright install --with-deps chromium || true

# Copy the backend code
COPY . .

# Expose default FastAPI port 8000 (and allow override via $PORT)
EXPOSE 8000

# Run FastAPI with uvicorn; bind to $PORT if provided (default 8000)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
