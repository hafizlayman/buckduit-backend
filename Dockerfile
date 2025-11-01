# Use stable, Render-friendly Python base
FROM python:3.10-slim

WORKDIR /app
COPY . /app

# Install system deps for pip builds
RUN apt-get update && apt-get install -y build-essential curl

# Clean Python install
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Expose Render dynamic port
ENV PORT=10000

# Start app
CMD ["bash", "./start.sh"]
