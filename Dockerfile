FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies in layers (lighter first)
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 fastapi==0.111.0 uvicorn==0.29.0 pydantic==2.7.1 requests==2.31.0
RUN pip install --no-cache-dir --timeout=300 openenv-core>=0.2.0
RUN pip install --no-cache-dir --timeout=300 gradio

# Copy source
COPY . .

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

# Run server
CMD ["python", "server.py"]