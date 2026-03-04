# Vatican Bot - Frontend Deployment Script
# This script helps deploy the frontend to Vercel

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "VATICAN BOT - FRONTEND DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "frontend")) {
    Write-Host "❌ Error: frontend directory not found" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Frontend directory found`n" -ForegroundColor Green

# Step 1: Check if build was successful
Write-Host "Step 1: Checking build status..." -ForegroundColor Yellow
if (Test-Path "frontend/.next") {
    Write-Host "✅ Build directory exists (.next)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Build directory not found. Running build..." -ForegroundColor Yellow
    Set-Location frontend
    npm run build
    Set-Location ..
}

# Step 2: Show deployment options
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT OPTIONS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Choose your deployment method:`n" -ForegroundColor White

Write-Host "1. Vercel CLI (Recommended)" -ForegroundColor Green
Write-Host "   - Fast and direct deployment" -ForegroundColor Gray
Write-Host "   - Requires Vercel CLI installed" -ForegroundColor Gray
Write-Host "   - Command: vercel --prod`n" -ForegroundColor Gray

Write-Host "2. Git Push (Auto-Deploy)" -ForegroundColor Green
Write-Host "   - Automatic deployment via Git" -ForegroundColor Gray
Write-Host "   - Requires Vercel connected to Git repo" -ForegroundColor Gray
Write-Host "   - Command: git push origin main`n" -ForegroundColor Gray

Write-Host "3. Vercel Dashboard" -ForegroundColor Green
Write-Host "   - Manual deployment via web interface" -ForegroundColor Gray
Write-Host "   - Go to: https://vercel.com/dashboard" -ForegroundColor Gray
Write-Host "   - Click 'Redeploy' button`n" -ForegroundColor Gray

Write-Host "4. Test Backend Connection" -ForegroundColor Green
Write-Host "   - Test if backend is accessible" -ForegroundColor Gray
Write-Host "   - Verify API endpoints`n" -ForegroundColor Gray

Write-Host "5. Exit`n" -ForegroundColor Red

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`n📦 Deploying via Vercel CLI..." -ForegroundColor Yellow
        
        # Check if Vercel CLI is installed
        $vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue
        
        if (-not $vercelInstalled) {
            Write-Host "❌ Vercel CLI not found" -ForegroundColor Red
            Write-Host "`nInstalling Vercel CLI..." -ForegroundColor Yellow
            npm install -g vercel
        }
        
        Write-Host "`n🚀 Starting deployment..." -ForegroundColor Green
        Set-Location frontend
        vercel --prod
        Set-Location ..
        
        Write-Host "`n✅ Deployment initiated!" -ForegroundColor Green
        Write-Host "Check the URL provided by Vercel to verify deployment" -ForegroundColor Yellow
    }
    
    "2" {
        Write-Host "`n📦 Deploying via Git Push..." -ForegroundColor Yellow
        
        # Check if there are uncommitted changes
        $status = git status --porcelain
        
        if ($status) {
            Write-Host "`n📝 Uncommitted changes found. Committing..." -ForegroundColor Yellow
            git add frontend/src/components/TaskModal.tsx
            git commit -m "fix: Remove hardcoded ENG language default for standard tickets"
        } else {
            Write-Host "✅ No uncommitted changes" -ForegroundColor Green
        }
        
        Write-Host "`n🚀 Pushing to Git..." -ForegroundColor Green
        git push origin main
        
        Write-Host "`n✅ Pushed to Git!" -ForegroundColor Green
        Write-Host "Vercel will auto-deploy if connected to your Git repository" -ForegroundColor Yellow
        Write-Host "Check Vercel dashboard for deployment status" -ForegroundColor Yellow
    }
    
    "3" {
        Write-Host "`n🌐 Opening Vercel Dashboard..." -ForegroundColor Yellow
        Start-Process "https://vercel.com/dashboard"
        
        Write-Host "`n📋 Manual Deployment Steps:" -ForegroundColor Cyan
        Write-Host "1. Select your project" -ForegroundColor White
        Write-Host "2. Go to 'Deployments' tab" -ForegroundColor White
        Write-Host "3. Click 'Redeploy' button" -ForegroundColor White
        Write-Host "4. Wait for build to complete" -ForegroundColor White
        Write-Host "5. Test the deployment" -ForegroundColor White
    }
    
    "4" {
        Write-Host "`n🔍 Testing Backend Connection..." -ForegroundColor Yellow
        
        # Check if backend is running
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health/" -Method GET -TimeoutSec 5 -ErrorAction Stop
            Write-Host "✅ Backend is running!" -ForegroundColor Green
            Write-Host "Status: $($response.StatusCode)" -ForegroundColor Gray
        } catch {
            Write-Host "❌ Backend not accessible" -ForegroundColor Red
            Write-Host "Make sure backend is running: docker-compose up -d backend" -ForegroundColor Yellow
        }
        
        # Check if worker is running
        Write-Host "`n🔍 Checking worker status..." -ForegroundColor Yellow
        docker-compose ps worker_vatican
    }
    
    "5" {
        Write-Host "`nExiting..." -ForegroundColor Gray
        exit 0
    }
    
    default {
        Write-Host "`n❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

# Post-deployment instructions
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "POST-DEPLOYMENT TESTING" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "After deployment, test the following:`n" -ForegroundColor White

Write-Host "1. Create Standard Ticket Monitor:" -ForegroundColor Yellow
Write-Host "   - Open dashboard" -ForegroundColor Gray
Write-Host "   - Click 'New Monitor'" -ForegroundColor Gray
Write-Host "   - Select 'Vatican Museums' > 'Standard Entry'" -ForegroundColor Gray
Write-Host "   - Language field should NOT be visible" -ForegroundColor Gray
Write-Host "   - Submit and verify language=null in database`n" -ForegroundColor Gray

Write-Host "2. Create Guided Tour Monitor:" -ForegroundColor Yellow
Write-Host "   - Click 'New Monitor'" -ForegroundColor Gray
Write-Host "   - Select 'Vatican Museums' > 'Guided Tours'" -ForegroundColor Gray
Write-Host "   - Language field SHOULD be visible" -ForegroundColor Gray
Write-Host "   - Select language and submit`n" -ForegroundColor Gray

Write-Host "3. Verify Database:" -ForegroundColor Yellow
Write-Host "   Run: python test_new_monitor_creation.py`n" -ForegroundColor Gray

Write-Host "4. Check Bot Logs:" -ForegroundColor Yellow
Write-Host "   Run: docker-compose logs worker_vatican | Select-String 'Lang:'`n" -ForegroundColor Gray

Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📚 For detailed instructions, see:" -ForegroundColor Cyan
Write-Host "   - VERCEL_DEPLOYMENT_GUIDE.md" -ForegroundColor White
Write-Host "   - COMPLETE_FIX_SUMMARY.md`n" -ForegroundColor White
