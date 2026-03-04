# Deploy Frontend to Vercel
Write-Host "🚀 Deploying Frontend to Vercel..." -ForegroundColor Cyan
Write-Host ""

# Change to frontend directory
Set-Location frontend

# Check if .vercel directory exists (project is linked)
if (Test-Path ".vercel") {
    Write-Host "✅ Vercel project already linked" -ForegroundColor Green
} else {
    Write-Host "⚠️  Vercel project not linked. Please run 'vercel link' first" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or deploy with:" -ForegroundColor Yellow
    Write-Host "  vercel --prod" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "📦 Building frontend..." -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Cyan
vercel --prod

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Your site is live at: https://bot-pl2x.vercel.app/" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

# Return to root directory
Set-Location ..
