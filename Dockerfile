# Use a lightweight Python base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files
COPY requirements.txt .

# ✅ Force clean install (ignore old cache)
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --force-reinstall -r requirements.txt

# Copy everything else
COPY . .

# Expose port 5000
EXPOSE 5000

# Start app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
