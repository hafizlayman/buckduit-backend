# ======================================
# BuckDuit Backend — Final Worker Entrypoint Fix
# ======================================
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy all files
COPY . .

# Upgrade pip and dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Ensure script is executable
RUN chmod +x /app/start_worker.sh

# Start worker script directly from root
CMD ["bash", "/app/start_worker.sh"]
