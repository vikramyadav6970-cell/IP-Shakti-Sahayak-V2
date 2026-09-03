# ==============================================================================
# IP-SAKTI Sahayak — Production Dockerfile (Backend + AI Multi-Agent RAG Service)
# Multi-stage build with CPU-optimized PyTorch and BAAI/bge-m3 neural embeddings
# ==============================================================================

# --- Stage 1: Build Dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies required for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lightweight CPU-only PyTorch first (saves ~3-4GB of unnecessary CUDA bloat)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy and install unified python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Production Runtime ---
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/backend:/app/ai" \
    PORT=8000 \
    ENVIRONMENT=production

# Install runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python site-packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy AI algorithms, classification models, prompts, and orchestration
COPY ai /app/ai

# Copy Backend FastAPI application, models, services, and repositories
COPY backend /app/backend

# Create non-root user for security best practices (UID 1000 compatible with HF Spaces)
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

EXPOSE 7860
EXPOSE 8000

WORKDIR /app/backend

# Start Uvicorn production server with dynamic port resolution
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
