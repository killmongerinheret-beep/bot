#!/bin/bash

echo "=========================================="
echo "Starting ngrok tunnel for backend"
echo "=========================================="
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed"
    echo ""
    echo "Please install ngrok:"
    echo "  1. Go to: https://ngrok.com/download"
    echo "  2. Download for your OS"
    echo "  3. Extract and add to PATH"
    echo ""
    exit 1
fi

echo "✅ ngrok is installed"
echo ""

# Check if backend is running
echo "Checking if backend is running..."
if curl -s http://localhost:8000/api/v1/tasks/ > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "❌ Backend is not running on port 8000"
    echo ""
    echo "Please start your backend first:"
    echo "  docker-compose up -d"
    echo ""
    exit 1
fi

echo ""
echo "=========================================="
echo "Starting ngrok tunnel..."
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT:"
echo "  1. Copy the HTTPS URL from below"
echo "  2. Go to Vercel Dashboard"
echo "  3. Settings → Environment Variables"
echo "  4. Set: NEXT_PUBLIC_API_URL = <ngrok-url>/api/v1"
echo "  5. Redeploy your frontend"
echo ""
echo "Press Ctrl+C to stop the tunnel"
echo ""

# Start ngrok
ngrok http 8000
