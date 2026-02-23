# Start with a slim Python image (Debian 12 Bookworm)
FROM python:3.11-slim

# 1. Install System Dependencies
# REMOVED: libgconf-2-4 (Obsolete/Caused the error)
# ADDED: libgbm1 (Required for modern Chrome headless/rendering)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    procps \
    libxi6 \
    libnss3 \
    libxss1 \
    libasound2 \
    libgbm1 \
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Google Chrome Stable (Modern Method)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | \
    gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Python Dependencies
RUN pip install nodriver redis

# 4. Set Environment Variables
ENV PYTHONUNBUFFERED=1
ENV REDIS_HOST=redis
ENV DISPLAY=:99

WORKDIR /app
COPY harvester.py .

# 5. The Command
CMD ["xvfb-run", "--server-args=-screen 0 1920x1080x24", "python", "harvester.py"]
