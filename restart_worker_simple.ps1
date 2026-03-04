# Simple Worker Restart
# Restarts the worker to load new code from mounted volume

Write-Host "Restarting Vatican worker to load new code..." -ForegroundColor Yellow
Write-Host ""

# Stop worker
Write-Host "1. Stopping worker..." -ForegroundColor Gray
docker-compose stop worker_vatican

# Start worker
Write-Host "2. Starting worker..." -ForegroundColor Gray
docker-compose start worker_vatican

Write-Host ""
Write-Host "✅ Worker restarted" -ForegroundColor Green
Write-Host ""

Write-Host "Waiting 10 seconds for worker to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Checking recent logs..." -ForegroundColor Yellow
docker-compose logs --tail=20 worker_vatican

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$logs = docker-compose logs --tail=50 worker_vatican 2>&1 | Out-String

if ($logs -match "Missing visit_date or visitors") {
    Write-Host "❌ Still seeing 'Missing parameters' error" -ForegroundColor Red
    Write-Host ""
    Write-Host "This means Python is caching the old code." -ForegroundColor Yellow
    Write-Host "Solution: Force rebuild the container" -ForegroundColor White
    Write-Host ""
    Write-Host "Run: docker-compose up -d --build worker_vatican" -ForegroundColor Cyan
} else {
    Write-Host "✅ No 'Missing parameters' error!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Triggering fresh check..." -ForegroundColor Yellow
    docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; orchestrate_all_tasks()"
    
    Write-Host ""
    Write-Host "✅ Check triggered" -ForegroundColor Green
    Write-Host ""
    Write-Host "Monitor logs: docker-compose logs -f worker_vatican" -ForegroundColor Cyan
    Write-Host "Run verification: .\complete_verification.ps1" -ForegroundColor Cyan
}

Write-Host ""
