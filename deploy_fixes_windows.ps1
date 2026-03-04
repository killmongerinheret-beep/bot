# Windows PowerShell Deployment Script for Visitor Count Fix
# Run this script to deploy the fixes

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Vatican Bot - Visitor Count Fix Deployment" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if Docker is running
Write-Host "Step 1: Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Step 2: Show current services
Write-Host "`nStep 2: Current services..." -ForegroundColor Yellow
docker-compose ps

# Step 3: Restart Vatican worker
Write-Host "`nStep 3: Restarting Vatican worker..." -ForegroundColor Yellow
docker-compose restart worker_vatican

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Vatican worker restarted successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to restart Vatican worker" -ForegroundColor Red
    exit 1
}

# Step 4: Wait for worker to be ready
Write-Host "`nStep 4: Waiting for worker to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host "✅ Worker should be ready now" -ForegroundColor Green

# Step 5: Show recent logs
Write-Host "`nStep 5: Recent logs (last 20 lines)..." -ForegroundColor Yellow
docker-compose logs --tail=20 worker_vatican

# Step 6: Instructions for monitoring
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Monitor logs for visitor counts:" -ForegroundColor White
Write-Host "   docker-compose logs -f worker_vatican" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Look for these patterns in logs:" -ForegroundColor White
Write-Host "   ✅ /fromtag/1/... (for 1-visitor tasks)" -ForegroundColor Green
Write-Host "   ✅ visitorNum=1 (in API calls)" -ForegroundColor Green
Write-Host "   ✅ Smart Group: .../1v → (grouping by visitor count)" -ForegroundColor Green
Write-Host ""
Write-Host "3. Trigger a test check:" -ForegroundColor White
Write-Host "   docker-compose exec backend python manage.py shell" -ForegroundColor Cyan
Write-Host "   Then run: from monitors.tasks import orchestrate_all_tasks; orchestrate_all_tasks()" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Check Task #19 configuration:" -ForegroundColor White
Write-Host "   docker-compose exec backend python manage.py shell" -ForegroundColor Cyan
Write-Host "   Then run: from monitors.models import MonitorTask; task = MonitorTask.objects.get(id=19); print(f'Visitors: {task.visitors}')" -ForegroundColor Cyan
Write-Host ""

# Optional: Ask if user wants to see live logs
Write-Host "Would you like to see live logs now? (Y/N): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`nShowing live logs (Press Ctrl+C to stop)..." -ForegroundColor Yellow
    docker-compose logs -f worker_vatican
}
