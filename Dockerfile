FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

# Run server
CMD ["python", "server.py"]