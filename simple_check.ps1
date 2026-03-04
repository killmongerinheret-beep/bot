# Simple Dashboard Check Script
# This is a simplified version that's easier to run

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Vatican Bot - Simple Dashboard Check                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check services
Write-Host "Step 1: Checking Docker services..." -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# Step 2: Restart Vatican worker
Write-Host "Step 2: Restarting Vatican worker with new code..." -ForegroundColor Yellow
docker-compose restart worker_vatican
Write-Host "✅ Worker restarted" -ForegroundColor Green
Write-Host ""

# Step 3: Wait a bit
Write-Host "Step 3: Waiting 5 seconds for worker to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host "✅ Ready" -ForegroundColor Green
Write-Host ""

# Step 4: Trigger orchestration using docker-compose exec with inline Python
Write-Host "Step 4: Triggering fresh check..." -ForegroundColor Yellow
docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; print('Result:', orchestrate_all_tasks())"
Write-Host ""

# Step 5: Show recent logs
Write-Host "Step 5: Recent worker logs (last 20 lines)..." -ForegroundColor Yellow
docker-compose logs --tail=20 worker_vatican
Write-Host ""

# Step 6: Instructions
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Next Steps                                             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Wait 2-3 minutes for checks to complete" -ForegroundColor White
Write-Host ""
Write-Host "2. Check worker logs for visitor counts:" -ForegroundColor White
Write-Host "   docker-compose logs -f worker_vatican" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Look for:" -ForegroundColor White
Write-Host "   ✅ /fromtag/1/... (for 1-visitor tasks)" -ForegroundColor Green
Write-Host "   ✅ visitorNum=1 (in API calls)" -ForegroundColor Green
Write-Host "   ✅ Smart Group: .../1v" -ForegroundColor Green
Write-Host ""
Write-Host "3. Test backend API in browser:" -ForegroundColor White
Write-Host "   http://localhost:8000/api/tasks/" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Refresh Vercel dashboard:" -ForegroundColor White
Write-Host "   https://bot-pl2x.vercel.app/" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. If still showing sold out, check:" -ForegroundColor White
Write-Host "   - Is Cloudflare tunnel running?" -ForegroundColor Gray
Write-Host "   - Is tunnel URL correct in Vercel?" -ForegroundColor Gray
Write-Host "   - Does tunnel URL work: https://your-tunnel.trycloudflare.com/api/tasks/" -ForegroundColor Gray
Write-Host ""

Write-Host "Would you like to see live logs now? (Y/N): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`nShowing live logs (Press Ctrl+C to stop)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    docker-compose logs -f worker_vatican
}
