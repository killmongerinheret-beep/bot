# Vatican Bot Status Verification Script
# Run this to check if the bot is working correctly

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "VATICAN BOT STATUS VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if containers are running
Write-Host "1. Checking Docker containers..." -ForegroundColor Yellow
docker-compose ps | Select-String -Pattern "worker_vatican|backend|redis"

# Check current task status
Write-Host "`n2. Checking current task status..." -ForegroundColor Yellow
docker-compose exec -T backend python /app/check_current_tasks.py 2>&1 | Select-Object -Last 50

# Check recent worker logs
Write-Host "`n3. Checking recent worker activity..." -ForegroundColor Yellow
docker-compose logs worker_vatican --tail=20 2>&1 | Select-String -Pattern "Available:|Sold Out:|SMART CHECK|GOD-TIER"

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION COMPLETE" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "✅ If you see 'Available: X, Sold Out: Y' in the logs, the bot is working!" -ForegroundColor Green
Write-Host "✅ Check the frontend dashboard to see real-time status" -ForegroundColor Green
Write-Host "`nTo monitor live:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f worker_vatican`n" -ForegroundColor White
