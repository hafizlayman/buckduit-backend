# ======================================
# BuckDuit Worker — Iron Build Fix (Railway)
# ======================================
FROM python:3.10-slim

# 1️⃣ Working directory
WORKDIR /app

# 2️⃣ Environment setup
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 3️⃣ Copy dependencies
COPY requirements.txt .

# 4️⃣ Upgrade pip + install dependencies cleanly
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copy backend source
COPY backend ./backend

# 6️⃣ Entrypoint
CMD ["bash", "backend/start_worker.sh"]
