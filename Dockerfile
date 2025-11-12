# ==========================================================
# BuckDuit Backend — Stage 14.12.20 (Guaranteed Stable)
# ==========================================================
FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY . /app
RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/start.sh
CMD ["/bin/bash", "/app/start.sh"]
