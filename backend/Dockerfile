# ==============================================================================
# MeetMind — Backend API Dockerfile
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# --- Production Runner Stage ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Create non-root user
RUN groupadd -g 1001 meetmind && \
    useradd -u 1001 -g meetmind -m -s /bin/bash meetmind

# Copy installed dependencies from builder
COPY --from=builder /root/.local /home/meetmind/.local
ENV PATH=/home/meetmind/.local/bin:$PATH

# Copy application source code
COPY --chown=meetmind:meetmind . .

# Create local storage directory
RUN mkdir -p /app/storage/uploads && chown -R meetmind:meetmind /app/storage

USER meetmind

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
