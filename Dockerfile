# ======================================
# BuckDuit Backend — Forced Sequential Installer
# ======================================
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Avoid Python buffering and pip cache
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy dependency list
COPY requirements.txt .

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

# --- Forced Sequential Installer ---
# We install these in sequence to break pip resolver loop
RUN pip install "httpx==0.25.2"
RUN pip install "supabase==2.2.3"
RUN pip install "python-telegram-bot==21.1.1"
RUN pip install "flask==3.0.3" "flask-cors==4.0.0" "gunicorn==21.2.0" "python-dotenv==1.0.1"
RUN pip install "aiohttp==3.9.3" "apscheduler==3.10.4"
RUN pip install "requests==2.31.0" "pandas==2.2.2" "numpy==1.26.4" "scikit-learn==1.5.0" "joblib==1.3.2"
RUN pip install "pydantic==2.9.2" "cachetools==5.5.0" "psycopg2-binary==2.9.9" "tqdm==4.66.1"

# Install any remaining deps (safe fallback)
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy backend source code
COPY backend ./backend

# Launch worker
CMD ["bash", "backend/start_worker.sh"]
