# Use official slim Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies in one layer for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only app files after dependencies
COPY . .

# Run AI Core worker
CMD ["python", "buckduit_ai_core.py"]
