# Use lightweight Python image
FROM python:3.10-slim

# Disable cache + speed up pip
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install basic system deps (fast)
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache requirements first
COPY requirements.txt .

# Upgrade pip and install deps with wheels where possible
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app files last (to reuse cached layer)
COPY . .

# Start AI Core worker
CMD ["python", "buckduit_ai_core.py"]
