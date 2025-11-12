# ======================================
# 🚀 BuckDuit Backend — Stage 14.12.12
# Hard Override Mode (ENTRYPOINT Fix)
# ======================================

# Base image
FROM python:3.10-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy all project files into container
COPY . /app

# Install system dependencies (if any additional required)
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Make worker script executable
RUN chmod +x /app/start_worker.sh

# ===========================
# ✅ Hard Override Entrypoint
# ===========================
ENTRYPOINT ["/bin/bash", "/app/start_worker.sh"]
