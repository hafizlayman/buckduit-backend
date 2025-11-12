# ==========================================================
# BuckDuit Backend — Stage 14.14
# Supervisor Daemon Entrypoint
# ==========================================================
FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN apt-get update -y && apt-get install -y --no-install-recommends curl
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /app/start.sh

EXPOSE 5000
CMD ["sh", "/app/start.sh"]
