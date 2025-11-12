# ======================================
# 🚀 BuckDuit Backend — Stage 14.12.13
# Absolute Entrypoint Enforcement
# ======================================

FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Make sure our script is always executable
RUN chmod +x /app/start_worker.sh

# ======================================
# ✅ Final Override: Direct Command Mode
# ======================================
CMD ["/bin/bash", "-c", "/app/start_worker.sh"]
