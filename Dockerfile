# ======================================
# BuckDuit Worker — Clean Build (Railway)
# ======================================
FROM python:3.10-slim

# 1️⃣ Working directory
WORKDIR /app

# 2️⃣ Environment
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 3️⃣ Copy and upgrade pip first
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel

# 4️⃣ Force pre-install clean dependency alignment
RUN pip install "httpx==0.27.0" "supabase==2.3.1"

# 5️⃣ Install remaining packages
RUN pip install --no-cache-dir -r requirements.txt

# 6️⃣ Copy backend source
COPY backend ./backend

# 7️⃣ Entrypoint
CMD ["bash", "backend/start_worker.sh"]
