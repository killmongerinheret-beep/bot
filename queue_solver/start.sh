#!/bin/bash

# Start Xvfb in the background
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Check if Xvfb is running
if ! ps -p $XVFB_PID > /dev/null; then
    echo "ERROR: Xvfb failed to start"
    exit 1
fi

echo "✅ Xvfb started successfully (PID: $XVFB_PID)"

# Run the Python script
python harvester.py

# Cleanup
kill $XVFB_PID 2>/dev/null || true
