FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment
ENV PORT=5001
ENV PYTHONUNBUFFERED=1

EXPOSE 5001

# Run with Gunicorn production server
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5001", "app:app"]
