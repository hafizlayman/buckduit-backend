# Use a known-stable base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy everything
COPY . .

# Install dependencies (force mode)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --no-deps -r requirements.txt

# Expose the Render port
ENV PORT=10000
EXPOSE 10000

# Start both the AI core and Flask API
CMD ["bash", "-c", "python buckduit_ai_core.py & gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120"]
