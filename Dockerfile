# Dockerfile
FROM python:3.11-slim

# Install OS packages
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy everything
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Start the Flask app via Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "app:app", "--timeout", "90", "--workers", "2", "--threads", "4", "--worker-class", "gthread"]
