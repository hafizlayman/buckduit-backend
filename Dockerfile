# ======================================
# BuckDuit Backend — Final Clean Build (Supabase 2.4.5)
# ======================================
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy dependencies
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# --- Sequential Installer with override patch ---
RUN pip install "supabase==2.4.5"
RUN pip install "httpx==0.27.0"
RUN pip install "python-telegram-bot==21.1.1"
RUN pip install "flask==3.0.3" "flask-cors==4.0.0" "gunicorn==21.2.0" "python-dotenv==1.0.1"
RUN pip install "aiohttp==3.9.3" "apscheduler==3.10.4"
RUN pip install "requests==2.31.0" "pandas==2.2.2" "numpy==1.26.4" "scikit-learn==1.5.0" "joblib==1.3.2"
RUN pip install "pydantic==2.9.2" "cachetools==5.5.0" "psycopg2-binary==2.9.9" "tqdm==4.66.1"

# Safety fallback
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy app source
COPY backend ./backend

CMD ["bash", "backend/start_worker.sh"]
