FROM python:3.12-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    -o Acquire::Retries=3 \
    -o Acquire::ForceIPv4=true \
    libpq-dev \
    curl \
    git \
    wget \
    gnupg \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and their system deps
# [HYDRA]: Install full playwright with dependencies for Chromium
RUN pip install playwright && playwright install --with-deps chromium

# Copy project files
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# The command is overridden by docker-compose
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
