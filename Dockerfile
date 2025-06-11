# Base image
FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set workdir
WORKDIR /app

# Copy code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (for local clarity only)
EXPOSE 4000

# Start Gunicorn with higher timeout
CMD gunicorn -b 0.0.0.0:${PORT:-4000} app:app --timeout 300 --workers 1 --threads 1 --worker-class gthread
