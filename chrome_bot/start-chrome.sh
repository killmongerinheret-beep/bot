#!/bin/bash

# Chrome Bot Startup Script
# Starts Chrome with extension in headless mode using Xvfb

set -e

# Configuration from environment variables
AGENCY_ID=${AGENCY_ID:-1}
BACKEND_URL=${BACKEND_URL:-http://backend:8000}
DISPLAY_NUM=${DISPLAY_NUM:-99}
VNC_ENABLED=${VNC_ENABLED:-false}
SCREEN_WIDTH=${SCREEN_WIDTH:-1920}
SCREEN_HEIGHT=${SCREEN_HEIGHT:-1080}
SCREEN_DEPTH=${SCREEN_DEPTH:-24}

echo "========================================="
echo "🚀 Vatican Bot - Chrome Instance"
echo "========================================="
echo "Agency ID: $AGENCY_ID"
echo "Backend URL: $BACKEND_URL"
echo "Display: :$DISPLAY_NUM"
echo "Screen: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}"
echo "VNC: $VNC_ENABLED"
echo "========================================="

# Create profile directory
PROFILE_DIR="/root/chrome-profiles/agency-${AGENCY_ID}"
mkdir -p "$PROFILE_DIR"
echo "✅ Profile directory: $PROFILE_DIR"

# Start Xvfb (Virtual Display)
echo "📺 Starting virtual display..."
Xvfb :$DISPLAY_NUM -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} -ac +extension GLX +render -noreset &
XVFB_PID=$!
export DISPLAY=:$DISPLAY_NUM

# Wait for Xvfb to start
sleep 3

# Check if Xvfb is running
if ! ps -p $XVFB_PID > /dev/null; then
    echo "❌ Failed to start Xvfb"
    exit 1
fi
echo "✅ Xvfb started (PID: $XVFB_PID)"

# Start window manager (optional, helps with some sites)
echo "🪟 Starting window manager..."
fluxbox &
sleep 2

# Start VNC server if enabled
if [ "$VNC_ENABLED" = "true" ]; then
    echo "🔍 Starting VNC server..."
    x11vnc -display :$DISPLAY_NUM -forever -shared -rfbport 5900 -nopw &
    VNC_PID=$!
    echo "✅ VNC server started (PID: $VNC_PID)"
    echo "   Connect to: localhost:5900"
fi

# Configure extension settings
# This creates a preferences file that the extension can read
EXTENSION_CONFIG="$PROFILE_DIR/extension-config.json"
cat > "$EXTENSION_CONFIG" << EOF
{
  "backendUrl": "$BACKEND_URL",
  "agencyId": $AGENCY_ID,
  "backendListenerEnabled": true,
  "pollInterval": 10000,
  "maxConcurrentBookings": 10,
  "autoConfirm": true,
  "autoPay": false
}
EOF
echo "✅ Extension config created: $EXTENSION_CONFIG"

# Chrome flags
CHROME_FLAGS=(
    --user-data-dir="$PROFILE_DIR"
    --load-extension=/root/browser-extension
    --no-sandbox
    --disable-dev-shm-usage
    --disable-gpu
    --disable-software-rasterizer
    --disable-extensions-except=/root/browser-extension
    --remote-debugging-address=0.0.0.0
    --remote-debugging-port=9222
    --window-size=$SCREEN_WIDTH,$SCREEN_HEIGHT
    --start-maximized
    --no-first-run
    --no-default-browser-check
    --disable-features=TranslateUI
    --disable-background-networking
    --disable-sync
    --disable-default-apps
    --disable-popup-blocking
    --disable-prompt-on-repost
    --disable-hang-monitor
    --disable-backgrounding-occluded-windows
    --disable-renderer-backgrounding
    --disable-background-timer-throttling
    --disable-ipc-flooding-protection
    --password-store=basic
    --use-mock-keychain
)

# Log file
LOG_FILE="/root/logs/chrome-agency-${AGENCY_ID}.log"
mkdir -p /root/logs

echo "✅ Starting Chrome with extension..."
echo "   Extension: /root/browser-extension"
echo "   Profile: $PROFILE_DIR"
echo "   Remote debugging: http://0.0.0.0:9222"
echo "   Log file: $LOG_FILE"

# Start Chrome
google-chrome "${CHROME_FLAGS[@]}" \
    "https://tickets.museivaticani.va" \
    > "$LOG_FILE" 2>&1 &

CHROME_PID=$!

echo "✅ Chrome started (PID: $CHROME_PID)"
echo ""
echo "========================================="
echo "✅ Chrome Bot Ready!"
echo "========================================="
echo "Agency ID: $AGENCY_ID"
echo "Chrome PID: $CHROME_PID"
echo "Xvfb PID: $XVFB_PID"
if [ "$VNC_ENABLED" = "true" ]; then
    echo "VNC PID: $VNC_PID"
fi
echo ""
echo "🔍 Remote Debugging:"
echo "   http://localhost:9222"
echo ""
if [ "$VNC_ENABLED" = "true" ]; then
    echo "🖥️  VNC Access:"
    echo "   localhost:5900"
    echo ""
fi
echo "📋 Logs:"
echo "   tail -f $LOG_FILE"
echo "========================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    
    if [ ! -z "$CHROME_PID" ]; then
        echo "   Stopping Chrome (PID: $CHROME_PID)..."
        kill $CHROME_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$VNC_PID" ]; then
        echo "   Stopping VNC (PID: $VNC_PID)..."
        kill $VNC_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$XVFB_PID" ]; then
        echo "   Stopping Xvfb (PID: $XVFB_PID)..."
        kill $XVFB_PID 2>/dev/null || true
    fi
    
    echo "✅ Cleanup complete"
    exit 0
}

# Trap signals
trap cleanup SIGTERM SIGINT SIGQUIT

# Monitor Chrome process
while true; do
    if ! ps -p $CHROME_PID > /dev/null; then
        echo "❌ Chrome process died (PID: $CHROME_PID)"
        echo "   Check logs: $LOG_FILE"
        
        # Auto-restart if configured
        if [ "${AUTO_RESTART:-true}" = "true" ]; then
            echo "🔄 Auto-restarting Chrome in 5 seconds..."
            sleep 5
            
            # Restart Chrome
            google-chrome "${CHROME_FLAGS[@]}" \
                "https://tickets.museivaticani.va" \
                >> "$LOG_FILE" 2>&1 &
            
            CHROME_PID=$!
            echo "✅ Chrome restarted (PID: $CHROME_PID)"
        else
            cleanup
        fi
    fi
    
    sleep 10
done
