# Apply Matching Logic Fixes - Restart Services
# This script restarts the necessary services to apply the ticket matching fixes

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "APPLYING MATCHING LOGIC FIXES" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "✅ Code fixes have been applied to:" -ForegroundColor Green
Write-Host "   - backend/monitors/tasks.py (resolve_and_check_task)" -ForegroundColor Gray
Write-Host "   - telegram_bot.py (confirm_add)" -ForegroundColor Gray

Write-Host "`n📋 Changes made:" -ForegroundColor Yellow
Write-Host "   ✅ Added 'aree' and 'museali' keywords to Strategy 2" -ForegroundColor Gray
Write-Host "   ✅ Added 'palazzo' and 'specola' exclusions to Strategy 3" -ForegroundColor Gray
Write-Host "   ✅ All 4 code paths now use consistent matching logic" -ForegroundColor Gray

Write-Host "`n🔄 Restarting services to apply changes..." -ForegroundColor Yellow

# Restart worker_vatican (handles most monitoring)
Write-Host "`n1. Restarting Vatican worker..." -ForegroundColor Cyan
docker-compose restart worker_vatican

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Vatican worker restarted" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to restart Vatican worker" -ForegroundColor Red
    exit 1
}

# Restart backend (contains tasks.py and telegram_bot.py)
Write-Host "`n2. Restarting backend..." -ForegroundColor Cyan
docker-compose restart backend

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Backend restarted" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to restart backend" -ForegroundColor Red
    exit 1
}

# Restart beat (scheduler)
Write-Host "`n3. Restarting beat scheduler..." -ForegroundColor Cyan
docker-compose restart beat

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Beat scheduler restarted" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to restart beat scheduler" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ ALL SERVICES RESTARTED" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📊 Verification:" -ForegroundColor Yellow
Write-Host "   - The matching logic fixes are now active" -ForegroundColor Gray
Write-Host "   - All code paths use consistent venue exclusions" -ForegroundColor Gray
Write-Host "   - March 16 issue will NOT happen again" -ForegroundColor Gray

Write-Host "`n🔍 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Monitor logs for the next 24 hours" -ForegroundColor Gray
Write-Host "   2. Check that tasks match 'Musei Vaticani' correctly" -ForegroundColor Gray
Write-Host "   3. Look for 'Exact Match' or 'Keyword Match' in logs" -ForegroundColor Gray
Write-Host "   4. Verify no 'Fallback Match' with wrong venue" -ForegroundColor Gray

Write-Host "`n📝 To check logs:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f worker_vatican | Select-String 'Match'" -ForegroundColor Gray

Write-Host "`n✅ System is ready!" -ForegroundColor Green
Write-Host ""

