# ======================================
# BuckDuit Backend — Final Worker Path Map (Railway Verified)
# ======================================
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy everything to /app (including backend + start_worker.sh)
COPY . .

# Upgrade and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Ensure script permission
RUN chmod +x /app/start_worker.sh

# Run the worker startup script
ENTRYPOINT ["bash", "/app/start_worker.sh"]
