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

# Expose a default port (platforms like Render provide $PORT at runtime)
EXPOSE 10000

# Run FastAPI with uvicorn; bind to $PORT if provided
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
