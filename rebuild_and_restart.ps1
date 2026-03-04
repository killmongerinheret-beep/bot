# Rebuild and Restart Worker
# This ensures the worker loads the new code

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Rebuild and Restart Worker                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "The worker is still running old code." -ForegroundColor Yellow
Write-Host "We need to rebuild the container to load the fixes." -ForegroundColor White
Write-Host ""

Write-Host "Step 1: Stopping worker..." -ForegroundColor Yellow
docker-compose stop worker_vatican
Write-Host "✅ Worker stopped" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Rebuilding worker container..." -ForegroundColor Yellow
Write-Host "(This may take 1-2 minutes)" -ForegroundColor Gray
docker-compose build worker_vatican
Write-Host "✅ Worker rebuilt" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Starting worker with new code..." -ForegroundColor Yellow
docker-compose up -d worker_vatican
Write-Host "✅ Worker started" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Waiting for worker to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
Write-Host "✅ Worker should be ready" -ForegroundColor Green
Write-Host ""

Write-Host "Step 5: Checking if error is gone..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
$logs = docker-compose logs --tail=50 worker_vatican 2>&1 | Out-String

if ($logs -match "Missing visit_date or visitors") {
    Write-Host "❌ Error still present!" -ForegroundColor Red
    Write-Host "   The code changes may not have been saved." -ForegroundColor Yellow
    Write-Host "   Check: backend/monitors/tasks.py line 251-257" -ForegroundColor Cyan
} else {
    Write-Host "✅ Error is gone!" -ForegroundColor Green
    Write-Host "   Worker is now running with the fix." -ForegroundColor White
}

Write-Host ""

Write-Host "Step 6: Triggering fresh check..." -ForegroundColor Yellow
docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; print('Result:', orchestrate_all_tasks())"
Write-Host ""

Write-Host "Step 7: Monitoring logs for 10 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
docker-compose logs --tail=30 worker_vatican
Write-Host ""

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Rebuild Complete                                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next: Run verification again" -ForegroundColor Yellow
Write-Host ".\complete_verification.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "Or view live logs:" -ForegroundColor Yellow
Write-Host "docker-compose logs -f worker_vatican" -ForegroundColor Cyan
Write-Host ""
