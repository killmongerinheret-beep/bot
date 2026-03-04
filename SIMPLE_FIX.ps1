# SIMPLE FIX - Just restart the worker
# The code is already in the container via volume mount

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Simple Fix - Restart Worker                           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "The code changes are already in the container (volume mount)." -ForegroundColor White
Write-Host "We just need to restart the worker to reload the code." -ForegroundColor White
Write-Host ""

# Method 1: Restart (keeps container, reloads code)
Write-Host "Restarting worker..." -ForegroundColor Yellow
docker-compose restart worker_vatican

Write-Host "✅ Worker restarted" -ForegroundColor Green
Write-Host ""

Write-Host "Waiting 15 seconds for worker to fully initialize..." -ForegroundColor Yellow
for ($i = 15; $i -gt 0; $i--) {
    Write-Host "  $i..." -NoNewline -ForegroundColor Gray
    Start-Sleep -Seconds 1
    if ($i % 5 -eq 0) { Write-Host "" }
}
Write-Host ""
Write-Host ""

Write-Host "Checking logs..." -ForegroundColor Yellow
Write-Host ""
$recentLogs = docker-compose logs --tail=20 worker_vatican 2>&1 | Out-String
Write-Host $recentLogs

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Check for the error
if ($recentLogs -match "Missing visit_date or visitors") {
    Write-Host "❌ Error still present" -ForegroundColor Red
    Write-Host ""
    Write-Host "Python is caching the old code. Let's force a clean restart:" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "1. Stopping worker..." -ForegroundColor Gray
    docker-compose stop worker_vatican
    
    Write-Host "2. Removing container..." -ForegroundColor Gray
    docker-compose rm -f worker_vatican
    
    Write-Host "3. Starting fresh..." -ForegroundColor Gray
    docker-compose up -d worker_vatican
    
    Write-Host ""
    Write-Host "✅ Worker recreated" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting 15 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    Write-Host ""
    Write-Host "Checking again..." -ForegroundColor Yellow
    $newLogs = docker-compose logs --tail=20 worker_vatican 2>&1 | Out-String
    Write-Host $newLogs
    
    if ($newLogs -match "Missing visit_date or visitors") {
        Write-Host ""
        Write-Host "❌ Still seeing error after recreate" -ForegroundColor Red
        Write-Host ""
        Write-Host "Let's check what's actually in the file:" -ForegroundColor Yellow
        Write-Host ""
        docker-compose exec -T worker_vatican cat /app/backend/monitors/tasks.py | Select-String -Context 2 "check_via_click"
        Write-Host ""
        Write-Host "If you don't see 'visit_date=date' and 'visitors=visitors'," -ForegroundColor Yellow
        Write-Host "the file might not be saved correctly." -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "✅ SUCCESS! Error is gone!" -ForegroundColor Green
    }
    
} else {
    Write-Host "✅ SUCCESS! No 'Missing parameters' error!" -ForegroundColor Green
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

Write-Host "Triggering fresh check..." -ForegroundColor Yellow
docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; result = orchestrate_all_tasks(); print('Result:', result)"

Write-Host ""
Write-Host "Check triggered!" -ForegroundColor Green
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 minutes for checks to complete" -ForegroundColor White
Write-Host "2. Run: .\complete_verification.ps1" -ForegroundColor Cyan
Write-Host "3. Or view live logs: docker-compose logs -f worker_vatican" -ForegroundColor Cyan
Write-Host ""
