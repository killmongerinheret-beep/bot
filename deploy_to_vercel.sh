#!/bin/bash

# Deploy Frontend to Vercel
# This script prepares and pushes the frontend to GitHub for Vercel deployment

set -e  # Exit on error

echo "========================================="
echo "HYDRA Monitor - Vercel Deployment"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found"
    echo "Please run this script from the project root"
    exit 1
fi

# Navigate to frontend
cd frontend

echo "📦 Step 1: Installing dependencies..."
npm install

echo ""
echo "🔨 Step 2: Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed! Please fix errors and try again."
    exit 1
fi

echo ""
echo "✅ Build successful!"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "🔧 Step 3: Initializing git repository..."
    git init
    git branch -M main
else
    echo "✅ Git repository already initialized"
fi

# Check if remote exists
if ! git remote | grep -q "origin"; then
    echo "🔗 Step 4: Adding GitHub remote..."
    git remote add origin https://github.com/killmongerinheret-beep/bot-front.git
else
    echo "✅ GitHub remote already configured"
fi

echo ""
echo "📝 Step 5: Committing changes..."
git add .
git commit -m "Deploy to Vercel - $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"

echo ""
echo "🚀 Step 6: Pushing to GitHub..."
git push -u origin main --force

echo ""
echo "========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Go to https://vercel.com"
echo "2. Import project: killmongerinheret-beep/bot-front"
echo "3. Add environment variable:"
echo "   NEXT_PUBLIC_API_URL=http://151.25.69.162:8000/api/v1"
echo "4. Deploy!"
echo ""
echo "Your frontend will be live at:"
echo "https://bot-front-xxx.vercel.app"
echo ""
echo "========================================="
