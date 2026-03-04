# Quick Vatican Bot Health Check
# ================================
# Run this to verify bot is working correctly

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VATICAN BOT HEALTH CHECK" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check if worker is running
Write-Host "[1/5] Checking worker status..." -ForegroundColor Yellow
$workerStatus = docker-compose ps worker_vatican 2>&1
if ($workerStatus -match "Up") {
    Write-Host "  ✅ Worker is RUNNING" -ForegroundColor Green
} else {
    Write-Host "  ❌ Worker is DOWN" -ForegroundColor Red
    Write-Host "  Fix: docker-compose restart worker_vatican" -ForegroundColor Yellow
    exit 1
}

# 2. Check recent logs for errors
Write-Host "`n[2/5] Checking for recent errors..." -ForegroundColor Yellow
$recentLogs = docker-compose logs --tail=50 worker_vatican 2>&1 | Select-String -Pattern "ERROR|CRITICAL|Failed" -CaseSensitive:$false
if ($recentLogs) {
    Write-Host "  ⚠️  Found errors in logs:" -ForegroundColor Yellow
    $recentLogs | Select-Object -First 3 | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
} else {
    Write-Host "  ✅ No recent errors" -ForegroundColor Green
}

# 3. Check for successful checks
Write-Host "`n[3/5] Checking for successful checks..." -ForegroundColor Yellow
$successLogs = docker-compose logs --tail=100 worker_vatican 2>&1 | Select-String -Pattern "Found \d+ available slots|Keyword Match|Exact Match"
if ($successLogs) {
    Write-Host "  ✅ Bot is finding tickets:" -ForegroundColor Green
    $successLogs | Select-Object -First 3 | ForEach-Object { 
        $line = $_ -replace '.*worker_vatican-1  \| ', ''
        Write-Host "    $line" -ForegroundColor Green 
    }
} else {
    Write-Host "  ⚠️  No successful checks found recently" -ForegroundColor Yellow
}

# 4. Check for name matching issues
Write-Host "`n[4/5] Checking for name matching issues..." -ForegroundColor Yellow
$nameIssues = docker-compose logs --tail=100 worker_vatican 2>&1 | Select-String -Pattern "No name match"
if ($nameIssues) {
    Write-Host "  ⚠️  Name matching issues detected:" -ForegroundColor Yellow
    $nameIssues | Select-Object -First 2 | ForEach-Object { 
        $line = $_ -replace '.*worker_vatican-1  \| ', ''
        Write-Host "    $line" -ForegroundColor Red 
    }
    Write-Host "`n  💡 Fix: Run fix_vatican_ticket_names.py" -ForegroundColor Cyan
} else {
    Write-Host "  ✅ Name matching working correctly" -ForegroundColor Green
}

# 5. Check for API errors
Write-Host "`n[5/5] Checking for API errors..." -ForegroundColor Yellow
$apiErrors = docker-compose logs --tail=100 worker_vatican 2>&1 | Select-String -Pattern "Status 500|API call failed"
if ($apiErrors) {
    Write-Host "  ⚠️  API errors detected:" -ForegroundColor Yellow
    $apiErrors | Select-Object -First 2 | ForEach-Object { 
        $line = $_ -replace '.*worker_vatican-1  \| ', ''
        Write-Host "    $line" -ForegroundColor Red 
    }
} else {
    Write-Host "  ✅ No API errors" -ForegroundColor Green
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$issues = 0
if ($workerStatus -notmatch "Up") { $issues++ }
if ($nameIssues) { $issues++ }
if ($apiErrors) { $issues++ }

if ($issues -eq 0) {
    Write-Host "`n✅ Vatican bot is HEALTHY and working correctly!" -ForegroundColor Green
    Write-Host "`nMonitor live: docker-compose logs -f worker_vatican" -ForegroundColor Cyan
} elseif ($issues -eq 1) {
    Write-Host "`n⚠️  Vatican bot has MINOR issues (see above)" -ForegroundColor Yellow
    Write-Host "`nRecommended action:" -ForegroundColor Cyan
    Write-Host "  1. docker-compose restart worker_vatican" -ForegroundColor White
    Write-Host "  2. Run fix_vatican_ticket_names.py if name issues persist" -ForegroundColor White
} else {
    Write-Host "`n❌ Vatican bot has MULTIPLE issues (see above)" -ForegroundColor Red
    Write-Host "`nRequired actions:" -ForegroundColor Cyan
    Write-Host "  1. docker-compose restart worker_vatican" -ForegroundColor White
    Write-Host "  2. docker cp fix_vatican_ticket_names.py travelagenntbot-backend-1:/app/" -ForegroundColor White
    Write-Host "  3. docker-compose exec backend python /app/fix_vatican_ticket_names.py" -ForegroundColor White
    Write-Host "  4. Check VATICAN_BOT_STATUS_REPORT.md for details" -ForegroundColor White
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
