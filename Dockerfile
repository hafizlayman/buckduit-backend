# ================================
# 🧩 BuckDuit AI Core - Dockerfile
# Production-ready Railway deployment
# ================================

# 1️⃣ Base image (lightweight + secure)
FROM python:3.10-slim

# 2️⃣ Set working directory
WORKDIR /app

# 3️⃣ Copy all files
COPY . .

# 4️⃣ Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Environment variables
# Railway will inject PORT dynamically (usually 8080)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# 6️⃣ Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 7️⃣ Start the Gunicorn server
CMD ["gunicorn", "buckduit_ai_core:app", "--workers", "2", "--threads", "2", "--timeout", "120", "--bind", "0.0.0.0:8080"]
