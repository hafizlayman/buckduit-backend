# force rebuild v2 - clean image for Railway
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files into container
COPY . /app

# Install system dependencies (for compiling Python packages)
RUN apt-get update && apt-get install -y build-essential curl

# Upgrade pip, setuptools, and wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for Railway (Flask/Gunicorn)
EXPOSE 8080

# Start the app using Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
