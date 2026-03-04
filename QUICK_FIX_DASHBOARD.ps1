# Quick Fix for Dashboard Showing Sold Out
# Run this script to diagnose and fix the issue

Write-Host @"
╔════════════════════════════════════════════════════════════╗
║     Dashboard Sold Out - Quick Fix Script                 ║
╚════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host "`nThis script will:" -ForegroundColor Yellow
Write-Host "1. Check if bot is actually finding availability" -ForegroundColor White
Write-Host "2. Force a fresh check with new code" -ForegroundColor White
Write-Host "3. Verify backend and dashboard connection" -ForegroundColor White
Write-Host "4. Give you specific next steps" -ForegroundColor White
Write-Host ""

# Step 1: Quick service check
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "STEP 1: Checking services..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$services = docker-compose ps --services --filter "status=running" 2>&1
if ($services -match "worker_vatican") {
    Write-Host "✅ Vatican worker is running" -ForegroundColor Green
} else {
    Write-Host "❌ Vatican worker is NOT running!" -ForegroundColor Red
    Write-Host "   Starting worker..." -ForegroundColor Yellow
    docker-compose up -d worker_vatican
    Start-Sleep -Seconds 5
}

if ($services -match "backend") {
    Write-Host "✅ Backend is running" -ForegroundColor Green
} else {
    Write-Host "❌ Backend is NOT running!" -ForegroundColor Red
    Write-Host "   Starting backend..." -ForegroundColor Yellow
    docker-compose up -d backend
    Start-Sleep -Seconds 5
}

Write-Host ""

# Step 2: Check recent results
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "STEP 2: Checking recent check results..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$quickCheck = @"
from monitors.models import CheckResult
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(hours=1)
recent = CheckResult.objects.filter(check_time__gte=cutoff, task__site='vatican')

available = recent.filter(status='available').count()
sold_out = recent.filter(status='sold_out').count()
total = recent.count()

print(f'Recent checks (last hour): {total}')
print(f'Available: {available}')
print(f'Sold out: {sold_out}')

if total == 0:
    print('STATUS:NO_CHECKS')
elif available > 0:
    print('STATUS:FOUND_AVAILABILITY')
else:
    print('STATUS:ALL_SOLD_OUT')
"@

$tempFile = [System.IO.Path]::GetTempFileName() + ".py"
$quickCheck | Out-File -FilePath $tempFile -Encoding UTF8
$result = Get-Content $tempFile | docker-compose exec -T backend python manage.py shell 2>&1
Remove-Item $tempFile

Write-Host $result
Write-Host ""

# Determine next action based on result
if ($result -match "STATUS:NO_CHECKS") {
    Write-Host "📊 DIAGNOSIS: No recent checks found" -ForegroundColor Yellow
    Write-Host "   The bot hasn't run checks in the last hour." -ForegroundColor White
    Write-Host "   This is why dashboard shows sold out (old data)." -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 FIX: Forcing fresh check..." -ForegroundColor Green
    
    $forceCheck = @"
from monitors.tasks import orchestrate_all_tasks
result = orchestrate_all_tasks()
print('Triggered: ' + str(result))
"@
    
    $tempFile2 = [System.IO.Path]::GetTempFileName() + ".py"
    $forceCheck | Out-File -FilePath $tempFile2 -Encoding UTF8
    Get-Content $tempFile2 | docker-compose exec -T backend python manage.py shell
    Remove-Item $tempFile2
    
    Write-Host ""
    Write-Host "✅ Check triggered!" -ForegroundColor Green
    Write-Host "   Wait 2-3 minutes, then refresh dashboard" -ForegroundColor White
    Write-Host "   Monitor: docker-compose logs -f worker_vatican" -ForegroundColor Cyan
    
} elseif ($result -match "STATUS:FOUND_AVAILABILITY") {
    Write-Host "🎉 DIAGNOSIS: Bot IS finding availability!" -ForegroundColor Green
    Write-Host "   The bot is working correctly." -ForegroundColor White
    Write-Host "   Problem is dashboard not showing the data." -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 POSSIBLE CAUSES:" -ForegroundColor Yellow
    Write-Host "   1. Dashboard not refreshing (try Ctrl+Shift+R)" -ForegroundColor White
    Write-Host "   2. Backend API not accessible from Vercel" -ForegroundColor White
    Write-Host "   3. Cloudflare tunnel not working" -ForegroundColor White
    Write-Host ""
    Write-Host "🔍 NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "   1. Test backend API:" -ForegroundColor White
    Write-Host "      http://localhost:8000/api/tasks/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   2. Test tunnel URL (if using Cloudflare):" -ForegroundColor White
    Write-Host "      https://your-tunnel-url.trycloudflare.com/api/tasks/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   3. Check Vercel environment variables:" -ForegroundColor White
    Write-Host "      NEXT_PUBLIC_API_URL should point to tunnel URL" -ForegroundColor Gray
    
} elseif ($result -match "STATUS:ALL_SOLD_OUT") {
    Write-Host "📊 DIAGNOSIS: All recent checks show sold out" -ForegroundColor Yellow
    Write-Host "   The bot is running but not finding availability." -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 POSSIBLE CAUSES:" -ForegroundColor Yellow
    Write-Host "   1. Tickets genuinely sold out" -ForegroundColor White
    Write-Host "   2. Wrong visitor count (checking with 2 instead of 1)" -ForegroundColor White
    Write-Host "   3. Wrong dates or ticket types" -ForegroundColor White
    Write-Host ""
    Write-Host "🔍 CHECKING VISITOR COUNT..." -ForegroundColor Cyan
    
    # Check logs for visitor count
    $logs = docker-compose logs --tail=50 worker_vatican 2>&1
    $fromtag1 = ($logs | Select-String -Pattern "fromtag/1/").Count
    $fromtag2 = ($logs | Select-String -Pattern "fromtag/2/").Count
    
    if ($fromtag1 -gt 0) {
        Write-Host "   ✅ Found /fromtag/1/ in logs (correct for 1-visitor tasks)" -ForegroundColor Green
    }
    if ($fromtag2 -gt 0) {
        Write-Host "   ⚠️  Found /fromtag/2/ in logs" -ForegroundColor Yellow
    }
    if ($fromtag1 -eq 0 -and $fromtag2 -eq 0) {
        Write-Host "   ❓ No fromtag patterns found in recent logs" -ForegroundColor Gray
        Write-Host "      Bot may not have run yet with new code" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "🔧 RECOMMENDED ACTIONS:" -ForegroundColor Cyan
    Write-Host "   1. Restart worker with new code:" -ForegroundColor White
    Write-Host "      docker-compose restart worker_vatican" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   2. Check detailed logs:" -ForegroundColor White
    Write-Host "      .\check_logs_windows.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   3. Force fresh check:" -ForegroundColor White
    Write-Host "      .\force_check_and_verify.ps1" -ForegroundColor Gray
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "QUICK FIX COMPLETE" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 For detailed troubleshooting, see:" -ForegroundColor Yellow
Write-Host "   DASHBOARD_SOLD_OUT_TROUBLESHOOTING.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 Available diagnostic scripts:" -ForegroundColor Yellow
Write-Host "   .\check_actual_availability.ps1  - Check if bot finding slots" -ForegroundColor Cyan
Write-Host "   .\force_check_and_verify.ps1     - Force fresh check" -ForegroundColor Cyan
Write-Host "   .\check_logs_windows.ps1         - Check visitor counts" -ForegroundColor Cyan
Write-Host "   .\test_task_19_windows.ps1       - Test specific task" -ForegroundColor Cyan
Write-Host ""
