# Force Reload Code
# This forces Python to reload the code by clearing cache and restarting

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Force Code Reload                                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Clearing Python cache..." -ForegroundColor Yellow
docker-compose exec -T worker_vatican find /app -type d -name __pycache__ -exec rm -rf {} + 2>$null
docker-compose exec -T worker_vatican find /app -type f -name "*.pyc" -delete 2>$null
Write-Host "✅ Cache cleared" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Restarting worker..." -ForegroundColor Yellow
docker-compose restart worker_vatican
Write-Host "✅ Worker restarted" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Waiting for worker to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
Write-Host "✅ Ready" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Checking for errors..." -ForegroundColor Yellow
$logs = docker-compose logs --tail=30 worker_vatican 2>&1 | Out-String

Write-Host $logs
Write-Host ""

if ($logs -match "Missing visit_date or visitors") {
    Write-Host "❌ STILL SEEING ERROR!" -ForegroundColor Red
    Write-Host ""
    Write-Host "The issue persists. Let's check if the file is actually mounted:" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Checking file in container..." -ForegroundColor Gray
    docker-compose exec -T worker_vatican grep -A 5 "check_via_click" /app/backend/monitors/tasks.py | Select-String -Pattern "visit_date|visitors"
    
    Write-Host ""
    Write-Host "If you don't see 'visit_date=date' and 'visitors=visitors' above," -ForegroundColor Yellow
    Write-Host "the file changes are not in the container." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Solution: Rebuild container" -ForegroundColor White
    Write-Host "docker-compose up -d --build --force-recreate worker_vatican" -ForegroundColor Cyan
    
} else {
    Write-Host "✅ SUCCESS! No more 'Missing parameters' error!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Step 5: Triggering fresh check..." -ForegroundColor Yellow
    docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; print('Triggered:', orchestrate_all_tasks())"
    Write-Host ""
    
    Write-Host "✅ All done!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Wait 2-3 minutes for checks to complete" -ForegroundColor White
    Write-Host "2. Run: .\complete_verification.ps1" -ForegroundColor Cyan
    Write-Host "3. Check dashboard: https://bot-pl2x.vercel.app/" -ForegroundColor Cyan
}

Write-Host ""
