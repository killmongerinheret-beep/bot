# Chrome Profile in Headless Mode - Complete Guide

## 🎯 Yes! You CAN Use Chrome Profiles Headless

### The Solution: Chrome with Persistent Profile + Xvfb

**What this means:**
- ✅ Use your browser extension
- ✅ Run headless on server (with Xvfb)
- ✅ Persistent profile (cookies, settings saved)
- ✅ Multiple profiles (multiple agencies)
- ✅ More stable than pure headless

---

## 🏗️ Three Approaches Compared

### Approach 1: Pure Playwright (Recommended Earlier)
```
Pros:
✅ True headless (no X server)
✅ Lightweight
✅ Easy to setup

Cons:
❌ No extension support
❌ Need to rewrite booking logic
```

### Approach 2: Chrome + Xvfb + Extension (NEW - Best!)
```
Pros:
✅ Use existing extension
✅ Persistent profiles
✅ Multiple agencies
✅ Cookies/sessions saved
✅ More realistic (looks like real user)

Cons:
⚠️ Needs Xvfb (virtual display)
⚠️ Slightly more resources
```

### Approach 3: Hybrid (Best of Both)
```
Pros:
✅ Playwright for monitoring
✅ Chrome+Extension for booking
✅ Fallback options

Cons:
⚠️ More complex setup
```

---

## 🚀 Implementation: Chrome Profile Headless

### Architecture:
```
Hetzner Server
├── Xvfb (Virtual Display)
├── Chrome with Profile 1 (Agency 1)
├── Chrome with Profile 2 (Agency 2)
├── Chrome with Profile 3 (Agency 3)
└── Extension loaded in each profile
```

---

## Part 1: Setup Xvfb (Virtual Display)

### What is Xvfb?
**X Virtual Framebuffer** - Creates a virtual display so Chrome thinks it has a screen.

### Install Xvfb:
```bash
# On Ubuntu/Debian
apt-get update
apt-get install -y xvfb x11vnc fluxbox

# Verify
xvfb-run --help
```

### Start Xvfb:
```bash
# Start virtual display :99
Xvfb :99 -screen 0 1920x1080x24 &

# Set display environment variable
export DISPLAY=:99
```

---

## Part 2: Chrome with Profile

### Create Profile Directory:
```bash
# Create profiles directory
mkdir -p /root/chrome-profiles

# Create profile for each agency
mkdir -p /root/chrome-profiles/agency-1
mkdir -p /root/chrome-profiles/agency-2
mkdir -p /root/chrome-profiles/agency-3
```

### Install Chrome:
```bash
# Download Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Install
apt install -y ./google-chrome-stable_current_amd64.deb

# Verify
google-chrome --version
```

### Load Extension:
```bash
# Copy extension to server
scp -r browser-extension root@YOUR_SERVER_IP:/root/

# Or unzip the package
unzip vatican-auto-booking-extension-v1.0.zip -d /root/browser-extension
```

---

## Part 3: Run Chrome with Profile + Extension

### Basic Command:
```bash
# Run Chrome with profile and extension
xvfb-run google-chrome \
  --user-data-dir=/root/chrome-profiles/agency-1 \
  --load-extension=/root/browser-extension \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --remote-debugging-port=9222 \
  --start-maximized \
  "https://tickets.museivaticani.va"
```

### With All Options:
```bash
xvfb-run -a -s "-screen 0 1920x1080x24" \
  google-chrome \
  --user-data-dir=/root/chrome-profiles/agency-1 \
  --load-extension=/root/browser-extension \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --disable-software-rasterizer \
  --disable-extensions-except=/root/browser-extension \
  --remote-debugging-port=9222 \
  --window-size=1920,1080 \
  --start-maximized \
  --no-first-run \
  --no-default-browser-check \
  "https://tickets.museivaticani.va"
```

---

## Part 4: Docker Setup

### Dockerfile for Chrome + Xvfb:
```dockerfile
# chrome_bot/Dockerfile

FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    x11vnc \
    fluxbox \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /root/chrome-profiles /root/browser-extension /root/scripts

# Copy extension
COPY browser-extension /root/browser-extension

# Copy startup script
COPY start-chrome.sh /root/scripts/
RUN chmod +x /root/scripts/start-chrome.sh

# Expose remote debugging port
EXPOSE 9222

# Start script
CMD ["/root/scripts/start-chrome.sh"]
```

### Startup Script:
```bash
# chrome_bot/start-chrome.sh

#!/bin/bash

# Get agency ID from environment
AGENCY_ID=${AGENCY_ID:-1}
BACKEND_URL=${BACKEND_URL:-http://backend:8000}

echo "🚀 Starting Chrome for Agency ${AGENCY_ID}..."

# Create profile directory
PROFILE_DIR="/root/chrome-profiles/agency-${AGENCY_ID}"
mkdir -p "$PROFILE_DIR"

# Start Xvfb
echo "📺 Starting virtual display..."
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Wait for Xvfb
sleep 2

# Configure extension (write config to profile)
cat > "$PROFILE_DIR/extension-config.json" << EOF
{
  "backendUrl": "$BACKEND_URL",
  "agencyId": $AGENCY_ID,
  "backendListenerEnabled": true,
  "pollInterval": 10000
}
EOF

echo "✅ Starting Chrome with extension..."

# Start Chrome
google-chrome \
  --user-data-dir="$PROFILE_DIR" \
  --load-extension=/root/browser-extension \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --remote-debugging-port=9222 \
  --window-size=1920,1080 \
  --start-maximized \
  --no-first-run \
  --no-default-browser-check \
  "https://tickets.museivaticani.va" &

CHROME_PID=$!

echo "✅ Chrome started (PID: $CHROME_PID)"
echo "🔍 Remote debugging: http://localhost:9222"

# Keep container running
wait $CHROME_PID
```

### Docker Compose:
```yaml
# docker-compose.yml

services:
  # ... existing services ...
  
  chrome_bot_agency_1:
    build: ./chrome_bot
    container_name: chrome-bot-agency-1
    restart: unless-stopped
    environment:
      - AGENCY_ID=1
      - BACKEND_URL=http://backend:8000
      - DISPLAY=:99
    volumes:
      - ./chrome-profiles/agency-1:/root/chrome-profiles/agency-1
      - ./browser-extension:/root/browser-extension:ro
      - /dev/shm:/dev/shm  # Shared memory for Chrome
    ports:
      - "9222:9222"  # Remote debugging
    networks:
      - vatican-network
    shm_size: '2gb'  # Increase shared memory
  
  chrome_bot_agency_2:
    build: ./chrome_bot
    container_name: chrome-bot-agency-2
    restart: unless-stopped
    environment:
      - AGENCY_ID=2
      - BACKEND_URL=http://backend:8000
      - DISPLAY=:99
    volumes:
      - ./chrome-profiles/agency-2:/root/chrome-profiles/agency-2
      - ./browser-extension:/root/browser-extension:ro
      - /dev/shm:/dev/shm
    ports:
      - "9223:9222"
    networks:
      - vatican-network
    shm_size: '2gb'
  
  # Add more agencies as needed...
```

---

## Part 5: Remote Debugging & Monitoring

### Access Chrome Remotely:
```bash
# From your local machine, create SSH tunnel
ssh -L 9222:localhost:9222 root@YOUR_SERVER_IP

# Then open in browser:
http://localhost:9222
```

**You can see:**
- ✅ All open tabs
- ✅ Console logs
- ✅ Network requests
- ✅ Screenshots
- ✅ DOM inspector

### Take Screenshots:
```bash
# Using Chrome DevTools Protocol
curl http://localhost:9222/json

# Get page info
curl http://localhost:9222/json/list

# Take screenshot (via CDP)
# Use chrome-remote-interface or puppeteer
```

### Monitor Extension:
```bash
# Check extension console
# Via remote debugging at http://localhost:9222
# Click on extension background page
```

---

## Part 6: VNC Access (Optional)

### Setup VNC for Visual Access:
```bash
# Install VNC server
apt-get install -y x11vnc

# Start VNC server
x11vnc -display :99 -forever -shared -rfbport 5900 &
```

### Connect from Local:
```bash
# Create SSH tunnel
ssh -L 5900:localhost:5900 root@YOUR_SERVER_IP

# Use VNC client to connect to:
localhost:5900

# You can SEE the Chrome browser!
```

---

## Part 7: Multiple Profiles Management

### Script to Manage Multiple Agencies:
```bash
# manage-chrome-bots.sh

#!/bin/bash

ACTION=$1
AGENCY_ID=$2

case $ACTION in
  start)
    echo "🚀 Starting Chrome bot for agency $AGENCY_ID..."
    docker-compose up -d chrome_bot_agency_$AGENCY_ID
    ;;
  
  stop)
    echo "🛑 Stopping Chrome bot for agency $AGENCY_ID..."
    docker-compose stop chrome_bot_agency_$AGENCY_ID
    ;;
  
  restart)
    echo "🔄 Restarting Chrome bot for agency $AGENCY_ID..."
    docker-compose restart chrome_bot_agency_$AGENCY_ID
    ;;
  
  logs)
    echo "📋 Logs for agency $AGENCY_ID..."
    docker-compose logs -f chrome_bot_agency_$AGENCY_ID
    ;;
  
  debug)
    echo "🔍 Remote debugging for agency $AGENCY_ID..."
    PORT=$((9221 + $AGENCY_ID))
    echo "Access at: http://localhost:$PORT"
    ;;
  
  *)
    echo "Usage: $0 {start|stop|restart|logs|debug} AGENCY_ID"
    exit 1
    ;;
esac
```

---

## Part 8: Comparison: Playwright vs Chrome Profile

### Resource Usage:

**Playwright (per instance):**
```
Memory: ~200MB
CPU: Low
Disk: Minimal
```

**Chrome + Xvfb (per instance):**
```
Memory: ~500MB
CPU: Medium
Disk: ~100MB (profile data)
```

### Capabilities:

| Feature | Playwright | Chrome+Profile |
|---------|-----------|----------------|
| Extension Support | ❌ No | ✅ Yes |
| Persistent Cookies | ⚠️ Manual | ✅ Auto |
| Remote Debugging | ✅ Yes | ✅ Yes |
| Screenshots | ✅ Yes | ✅ Yes |
| Multiple Instances | ✅ Easy | ✅ Easy |
| Resource Usage | ✅ Low | ⚠️ Medium |
| Setup Complexity | ✅ Easy | ⚠️ Medium |
| Stability | ✅ High | ✅ High |

---

## Part 9: Recommended Hybrid Approach

### Best of Both Worlds:

```yaml
services:
  # Playwright for monitoring (lightweight)
  playwright_monitor:
    build: ./playwright_bot
    environment:
      - MODE=monitor
    # Just checks availability, doesn't book
  
  # Chrome + Extension for booking (when slot found)
  chrome_bot_agency_1:
    build: ./chrome_bot
    environment:
      - AGENCY_ID=1
      - MODE=booking
    # Only starts when slot is available
```

**Flow:**
```
1. Playwright monitors Vatican (lightweight)
   ↓
2. Finds available slot
   ↓
3. Triggers Chrome bot with extension
   ↓
4. Chrome books the slot
   ↓
5. Chrome shuts down (save resources)
```

---

## Part 10: Production Setup

### Server Requirements:

**For 5 Chrome instances:**
```
CPU: 4 vCPU
RAM: 16GB
Disk: 50GB SSD
Server: Hetzner CX41 (€23.79/month)
```

**For 10 Chrome instances:**
```
CPU: 8 vCPU
RAM: 32GB
Disk: 100GB SSD
Server: Hetzner CCX23 (€47.90/month)
```

### Optimization:

```bash
# Limit Chrome memory
google-chrome --max-old-space-size=512 ...

# Use Chrome flags
--disable-features=TranslateUI
--disable-background-networking
--disable-sync
--disable-default-apps
```

---

## ✅ Final Recommendation

### For Your Use Case:

**Use Chrome + Profile + Extension** if:
- ✅ You already have working extension
- ✅ Want to reuse existing code
- ✅ Need persistent sessions
- ✅ Have enough server resources
- ✅ Want visual debugging (VNC)

**Use Playwright** if:
- ✅ Want lowest resource usage
- ✅ Don't mind rewriting booking logic
- ✅ Need maximum scalability
- ✅ Want simplest setup

**Use Hybrid** if:
- ✅ Want best of both worlds
- ✅ Monitor with Playwright
- ✅ Book with Chrome+Extension
- ✅ Optimize resource usage

---

## 🚀 Quick Start: Chrome Profile Headless

```bash
# 1. Create Dockerfile (see Part 4)
# 2. Build image
docker-compose build chrome_bot_agency_1

# 3. Start
docker-compose up -d chrome_bot_agency_1

# 4. Check logs
docker-compose logs -f chrome_bot_agency_1

# 5. Remote debug
ssh -L 9222:localhost:9222 root@YOUR_SERVER_IP
# Open: http://localhost:9222

# 6. VNC access (optional)
ssh -L 5900:localhost:5900 root@YOUR_SERVER_IP
# Connect with VNC client
```

---

**Answer:** ✅ YES, you can deploy Chrome profile in headless using Xvfb!

**Best approach:** Chrome + Xvfb + Extension for your use case (reuse existing extension)

**Next:** See implementation files in next response!
