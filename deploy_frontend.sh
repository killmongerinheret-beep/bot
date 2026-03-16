#!/bin/bash

echo "🚀 Deploying Multi-Tenant Dashboard to hydrasnipe.it"
echo "=================================================="

# Step 1: Build frontend for production
echo "📦 Building frontend for production..."
cd frontend

# Install dependencies
echo "Installing dependencies..."
npm install

# Build for production
echo "Building static files..."
npm run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Frontend build successful!"
    echo ""
    echo "📁 Static files ready in: frontend/out/"
    echo ""
    echo "🎯 NEXT STEPS:"
    echo "1. Upload all files from 'frontend/out/' folder to hydrasnipe.it"
    echo "2. Replace existing files in your web server directory"
    echo "3. Test: https://hydrasnipe.it/"
    echo ""
    echo "📋 Files to upload:"
    ls -la out/
    echo ""
    echo "🔧 Backend is already configured for hydrasnipe.it"
    echo "✅ CORS settings updated"
    echo "✅ Port 8000 exposed publicly"
    echo ""
    echo "🧪 Test backend access:"
    echo "curl http://151.25.69.162:8000/api/v1/agencies/"
else
    echo "❌ Frontend build failed!"
    exit 1
fi