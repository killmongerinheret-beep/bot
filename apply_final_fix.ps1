# Apply Final Fix - Missing visit_date and visitors parameters
# This fixes the "❌ Missing visit_date or visitors" error

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Applying Final Fix - Missing Parameters               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Issue Found:" -ForegroundColor Yellow
Write-Host "  ❌ Missing visit_date or visitors - cannot check via API" -ForegroundColor Red
Write-Host ""
Write-Host "Root Cause:" -ForegroundColor Yellow
Write-Host "  check_via_click() was called without visit_date and visitors parameters" -ForegroundColor White
Write-Host ""
Write-Host "Fix Applied:" -ForegroundColor Yellow
Write-Host "  ✅ Added visit_date=date parameter" -ForegroundColor Green
Write-Host "  ✅ Added visitors=visitors parameter" -ForegroundColor Green
Write-Host ""

Write-Host "Step 1: Restarting Vatican worker with fix..." -ForegroundColor Yellow
docker-compose restart worker_vatican

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Worker restarted successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to restart worker" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Waiting for worker to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host "✅ Worker should be ready" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Triggering fresh check..." -ForegroundColor Yellow
docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; print('Result:', orchestrate_all_tasks())"
Write-Host ""

Write-Host "Step 4: Waiting for checks to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host ""

Write-Host "Step 5: Checking recent logs..." -ForegroundColor Yellow
Write-Host ""
docker-compose logs --tail=30 worker_vatican
Write-Host ""

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Fix Applied Successfully                               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "What to Look For:" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ GOOD SIGNS:" -ForegroundColor Green
Write-Host "   • No more 'Missing visit_date or visitors' errors" -ForegroundColor White
Write-Host "   • See '/fromtag/1/...' for 1-visitor tasks" -ForegroundColor White
Write-Host "   • See 'visitorNum=1' in API calls" -ForegroundColor White
Write-Host "   • See 'Smart Group: .../1v'" -ForegroundColor White
Write-Host "   • See 'Found X slots' or availability messages" -ForegroundColor White
Write-Host ""

Write-Host "❌ BAD SIGNS:" -ForegroundColor Red
Write-Host "   • Still seeing 'Missing visit_date or visitors'" -ForegroundColor White
Write-Host "   • Python errors or stack traces" -ForegroundColor White
Write-Host "   • Worker keeps restarting" -ForegroundColor White
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Monitor logs for 2-3 minutes:" -ForegroundColor White
Write-Host "   docker-compose logs -f worker_vatican" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Run log analysis:" -ForegroundColor White
Write-Host "   .\analyze_logs.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Test backend API:" -ForegroundColor White
Write-Host "   http://localhost:8000/api/tasks/" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Refresh Vercel dashboard:" -ForegroundColor White
Write-Host "   https://bot-pl2x.vercel.app/" -ForegroundColor Cyan
Write-Host ""

Write-Host "Would you like to see live logs now? (Y/N): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`nShowing live logs (Press Ctrl+C to stop)..." -ForegroundColor Yellow
    Write-Host "Look for the patterns mentioned above!" -ForegroundColor Gray
    Write-Host ""
    Start-Sleep -Seconds 2
    docker-compose logs -f worker_vatican
}
