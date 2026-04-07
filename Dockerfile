FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install dependencies in layers (lighter first)
COPY requirements.txt .
RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt

# Copy source
COPY . .

# Expose port (HF Spaces uses 7860)
EXPOSE 7860
# Run server
CMD ["python", "server.py"]