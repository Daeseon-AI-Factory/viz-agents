FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    "uvicorn[standard]==0.32.0" \
    httpx==0.27.2

# Copy application
COPY . .

# Volume mount points (declared so fly.io knows about them)
# library/ and sessions/ are mounted from a Fly Volume in production
RUN mkdir -p library sessions concepts

EXPOSE 8765

# Use uvicorn directly (production-grade) instead of `python server.py`
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8765"]
