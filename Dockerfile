# Dockerfile for Osool Guide - NATO Asset Codifier
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (excluding large embeddings)
COPY . .

# Download embedding files from Hugging Face Space
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /app/embeddings && \
    wget -O /app/embeddings/inc_index.faiss "https://huggingface.co/spaces/aksworks00/osool_guide/resolve/main/embeddings/inc_index.faiss" && \
    wget -O /app/embeddings/metadata.pkl "https://huggingface.co/spaces/aksworks00/osool_guide/resolve/main/embeddings/metadata.pkl"

# Create cache directory with proper permissions
RUN mkdir -p /app/.cache && chmod 777 /app/.cache

# Expose port 7860 (HuggingFace default)
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=7860
ENV HF_HOME=/app/.cache
ENV TRANSFORMERS_CACHE=/app/.cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "7860"]
