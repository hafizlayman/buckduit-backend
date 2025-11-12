# ==========================================================
# BuckDuit Backend — Stage 14.13.4
# (Absolute Build Path Fix + Auto-Heal Bootstrap)
# ==========================================================
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy everything from local repo into /app/
COPY . .

# Install system dependencies
RUN apt-get update -y && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Give execution rights
RUN chmod +x /app/start.sh

# Expose Flask port
EXPOSE 5000

# Run app via start.sh
CMD ["/bin/sh", "/app/start.sh"]
