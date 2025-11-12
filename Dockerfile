# ==========================================================
# BuckDuit Backend — Stage 14.13.6
# Stable Root Entrypoint (100% Guarantee)
# ==========================================================
FROM python:3.10-slim

# Working directory inside container
WORKDIR /app

# Copy everything from your repo
COPY . /app

# Install dependencies
RUN apt-get update -y && apt-get install -y --no-install-recommends curl
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /app/start.sh

# Expose Flask port
EXPOSE 5000

# Start app
CMD ["sh", "/app/start.sh"]
