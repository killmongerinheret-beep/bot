# Complete Bot and Dashboard Verification
# This script checks everything and verifies the dashboard is working

Write-Host @"
╔════════════════════════════════════════════════════════════╗
║     Complete Vatican Bot & Dashboard Verification         ║
╚════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host ""

# Step 1: Check Services
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "STEP 1: Checking Docker Services" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$services = docker-compose ps --format "table {{.Service}}\t{{.Status}}" 2>&1

if ($services -match "worker_vatican.*Up") {
    Write-Host "✅ Vatican worker is running" -ForegroundColor Green
} else {
    Write-Host "❌ Vatican worker is NOT running" -ForegroundColor Red
}

if ($services -match "backend.*Up") {
    Write-Host "✅ Backend is running" -ForegroundColor Green
} else {
    Write-Host "❌ Backend is NOT running" -ForegroundColor Red
}

Write-Host ""

# Step 2: Check Recent Bot Activity
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "STEP 2: Checking Recent Bot Activity" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$checkActivity = @"
from monitors.models import MonitorTask, CheckResult
from django.utils import timezone
from datetime import timedelta
import json

# Get recent checks (last hour)
cutoff = timezone.now() - timedelta(hours=1)
recent = CheckResult.objects.filter(check_time__gte=cutoff, task__site='vatican')

total = recent.count()
available = recent.filter(status='available').count()
sold_out = recent.filter(status='sold_out').count()
errors = recent.filter(status='error').count()

print(f'RECENT_CHECKS:{total}')
print(f'AVAILABLE:{available}')
print(f'SOLD_OUT:{sold_out}')
print(f'ERRORS:{errors}')

# Check Task #19 specifically
try:
    task19 = MonitorTask.objects.get(id=19)
    print(f'TASK19_VISITORS:{task19.visitors}')
    print(f'TASK19_STATUS:{task19.last_status}')
    
    age = 'never'
    if task19.last_checked:
        delta = timezone.now() - task19.last_checked
        mins = int(delta.total_seconds() / 60)
        age = f'{mins}m'
    print(f'TASK19_AGE:{age}')
    
    # Get latest result
    latest = CheckResult.objects.filter(task=task19).order_by('-check_time').first()
    if latest and latest.details:
        details = latest.details if isinstance(latest.details, dict) else {}
        slots = details.get('slots', [])
        print(f'TASK19_SLOTS:{len(slots)}')
except:
    print('TASK19_ERROR:not_found')
"@

$tempFile = [System.IO.Path]::GetTempFileName() + ".py"
$checkActivity | Out-File -FilePath $tempFile -Encoding UTF8
$activityResult = Get-Content $tempFile | docker-compose exec -T backend python manage.py shell 2>&1 | Out-String
Remove-Item $tempFile

# Parse results
$recentChecks = if ($activityResult -match "RECENT_CHECKS:(\d+)") { $matches[1] } else { "0" }
$availableCount = if ($activityResult -match "AVAILABLE:(\d+)") { $matches[1] } else { "0" }
$soldOutCount = if ($activityResult -match "SOLD_OUT:(\d+)") { $matches[1] } else { "0" }
$task19Visitors = if ($activityResult -match "TASK19_VISITORS:(\d+)") { $matches[1] } else { "?" }
$task19Status = if ($activityResult -match "TASK19_STATUS:(\w+)") { $matches[1] } else { "unknown" }
$task19Age = if ($activityResult -match "TASK19_AGE:(\S+)") { $matches[1] } else { "never" }
$task19Slots = if ($activityResult -match "TASK19_SLOTS:(\d+)") { $matches[1] } else { "0" }

Write-Host "Recent Activity (last hour):" -ForegroundColor Yellow
Write-Host "  Total checks: $recentChecks" -ForegroundColor White
Write-Host "  Available: $availableCount" -ForegroundColor $(if ([int]$availableCount -gt 0) { "Green" } else { "Gray" })
Write-Host "  Sold out: $soldOutCount" -ForegroundColor Gray
Write-Host ""

Write-Host "Task #19 (March 16, 1 visitor):" -ForegroundColor Yellow
Write-Host "  Configured visitors: $task19Visitors" -ForegroundColor $(if ($task19Visitors -eq "1") { "Green" } else { "Red" })
Write-Host "  Current status: $task19Status" -ForegroundColor $(if ($task19Status -eq "available") { "Green" } elseif ($task19Status -eq "sold_out") { "Red" } else { "Gray" })
Write-Host "  Last checked: $task19Age ago" -ForegroundColor Gray
Write-Host "  Slots found: $task19Slots" -ForegroundColor $(if ([int]$task19Slots -gt 0) { "Green" } else { "Gray" })
Write-Host ""

# Step 3: Analyze Logs
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "STEP 3: Analyzing Worker Logs" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$logs = docker-compose logs --tail=100 worker_vatican 2>&1 | Out-String

# Check for fix indicators
$hasFromtag1 = $logs -match "fromtag/1/"
$hasVisitorNum1 = $logs -match "visitorNum=1"
$hasSmartGroup = $logs -match "Smart Group:.*?/1v"
$hasMissingParams = $logs -match "Missing visit_date or visitors"
$hasErrors = $logs -match "ERROR|Error"

Write-Host "Fix Verification:" -ForegroundColor Yellow
if ($hasFromtag1) {
    Write-Host "  ✅ Found /fromtag/1/ (correct for 1-visitor tasks)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  No /fromtag/1/ found in recent logs" -ForegroundColor Yellow
}

if ($hasVisitorNum1) {
    Write-Host "  ✅ Found visitorNum=1 in API calls" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  No visitorNum=1 found in recent logs" -ForegroundColor Yellow
}

if ($hasSmartGroup) {
    Write-Host "  ✅ Found Smart Group with /1v (grouping by visitor count)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  No Smart Group patterns found" -ForegroundColor Yellow
}

if ($hasMissingParams) {
    Write-Host "  ❌ Still seeing 'Missing visit_date or visitors' error!" -ForegroundColor Red
    Write-Host "     Worker needs restart: docker-compose restart worker_vatican" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ No 'Missing parameters' errors" -ForegroundColor Green
}

if ($hasErrors) {
    Write-Host "  ⚠️  Errors detected in logs" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ No errors in recent logs" -ForegroundColor Green
}

Write-Host ""

# Step 4: Test Backend API
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "STEP 4: Testing Backend API" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$testApi = @"
import requests
import json

try:
    response = requests.get('http://localhost:8000/api/tasks/', timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print(f'API_STATUS:success')
        print(f'API_TASKS:{len(data)}')
        
        # Find Task #19
        task19_data = next((t for t in data if t.get('id') == 19), None)
        if task19_data:
            print(f'API_TASK19_STATUS:{task19_data.get("last_status", "unknown")}')
            latest = task19_data.get('latest_check', {})
            if latest:
                details = latest.get('details', {})
                slots = details.get('slots', [])
                print(f'API_TASK19_SLOTS:{len(slots)}')
    else:
        print(f'API_STATUS:error_{response.status_code}')
        
except requests.exceptions.ConnectionError:
    print('API_STATUS:connection_error')
except Exception as e:
    print(f'API_STATUS:error')
"@

$tempFile2 = [System.IO.Path]::GetTempFileName() + ".py"
$testApi | Out-File -FilePath $tempFile2 -Encoding UTF8
$apiResult = Get-Content $tempFile2 | docker-compose exec -T backend python manage.py shell 2>&1 | Out-String
Remove-Item $tempFile2

$apiStatus = if ($apiResult -match "API_STATUS:(\w+)") { $matches[1] } else { "unknown" }
$apiTasks = if ($apiResult -match "API_TASKS:(\d+)") { $matches[1] } else { "0" }
$apiTask19Status = if ($apiResult -match "API_TASK19_STATUS:(\w+)") { $matches[1] } else { "unknown" }
$apiTask19Slots = if ($apiResult -match "API_TASK19_SLOTS:(\d+)") { $matches[1] } else { "0" }

Write-Host "Backend API Test:" -ForegroundColor Yellow
Write-Host "  URL: http://localhost:8000/api/tasks/" -ForegroundColor Gray
Write-Host "  Status: $apiStatus" -ForegroundColor $(if ($apiStatus -eq "success") { "Green" } else { "Red" })

if ($apiStatus -eq "success") {
    Write-Host "  Tasks returned: $apiTasks" -ForegroundColor White
    Write-Host "  Task #19 status: $apiTask19Status" -ForegroundColor $(if ($apiTask19Status -eq "available") { "Green" } else { "Gray" })
    Write-Host "  Task #19 slots: $apiTask19Slots" -ForegroundColor $(if ([int]$apiTask19Slots -gt 0) { "Green" } else { "Gray" })
}

Write-Host ""

# Step 5: Summary and Diagnosis
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "SUMMARY & DIAGNOSIS" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$fixWorking = $hasFromtag1 -or $hasSmartGroup
$botFindingSlots = [int]$availableCount -gt 0 -or [int]$task19Slots -gt 0
$apiWorking = $apiStatus -eq "success"
$hasCriticalErrors = $hasMissingParams

if ($hasCriticalErrors) {
    Write-Host "❌ CRITICAL: Missing parameters error still present!" -ForegroundColor Red
    Write-Host "   Action: Restart worker immediately" -ForegroundColor Yellow
    Write-Host "   Command: docker-compose restart worker_vatican" -ForegroundColor Cyan
    
} elseif ($fixWorking -and $botFindingSlots -and $apiWorking) {
    Write-Host "🎉 SUCCESS: Everything is working!" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Visitor count fix is working" -ForegroundColor Green
    Write-Host "✅ Bot is finding availability" -ForegroundColor Green
    Write-Host "✅ Backend API is accessible" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dashboard Status:" -ForegroundColor Yellow
    Write-Host "  If Vercel dashboard still shows 'sold out':" -ForegroundColor White
    Write-Host "  1. Hard refresh: Ctrl+Shift+R" -ForegroundColor Gray
    Write-Host "  2. Check Cloudflare tunnel is running" -ForegroundColor Gray
    Write-Host "  3. Verify tunnel URL in Vercel env vars" -ForegroundColor Gray
    
} elseif ($fixWorking -and -not $botFindingSlots) {
    Write-Host "⚠️  Fix is working but no availability found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "✅ Visitor count fix is working" -ForegroundColor Green
    Write-Host "❌ No availability detected yet" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible reasons:" -ForegroundColor White
    Write-Host "  1. Tickets genuinely sold out" -ForegroundColor Gray
    Write-Host "  2. Bot hasn't completed checks yet (wait 2-3 min)" -ForegroundColor Gray
    Write-Host "  3. Checks failing for other reasons" -ForegroundColor Gray
    
} else {
    Write-Host "⚠️  Fix not fully applied or bot not running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Action needed:" -ForegroundColor White
    Write-Host "  1. Restart worker: docker-compose restart worker_vatican" -ForegroundColor Cyan
    Write-Host "  2. Wait 30 seconds" -ForegroundColor Gray
    Write-Host "  3. Run this script again" -ForegroundColor Gray
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "NEXT STEPS" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

Write-Host "1. Test backend API in browser:" -ForegroundColor White
Write-Host "   http://localhost:8000/api/tasks/" -ForegroundColor Cyan
Write-Host ""

Write-Host "2. Check Vercel dashboard:" -ForegroundColor White
Write-Host "   https://bot-pl2x.vercel.app/" -ForegroundColor Cyan
Write-Host "   (Hard refresh: Ctrl+Shift+R)" -ForegroundColor Gray
Write-Host ""

Write-Host "3. If dashboard still shows sold out:" -ForegroundColor White
Write-Host "   • Check Cloudflare tunnel is running" -ForegroundColor Gray
Write-Host "   • Test tunnel URL: https://your-tunnel.trycloudflare.com/api/tasks/" -ForegroundColor Gray
Write-Host "   • Verify NEXT_PUBLIC_API_URL in Vercel settings" -ForegroundColor Gray
Write-Host ""

Write-Host "4. View live logs:" -ForegroundColor White
Write-Host "   docker-compose logs -f worker_vatican" -ForegroundColor Cyan
Write-Host ""

Write-Host "Would you like to:" -ForegroundColor Yellow
Write-Host "  1. View live logs" -ForegroundColor White
Write-Host "  2. Restart worker and re-check" -ForegroundColor White
Write-Host "  3. Exit" -ForegroundColor White
Write-Host ""
Write-Host "Enter choice (1/2/3): " -NoNewline -ForegroundColor Yellow
$choice = Read-Host

switch ($choice) {
    "1" {
        Write-Host "`nShowing live logs (Press Ctrl+C to stop)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 1
        docker-compose logs -f worker_vatican
    }
    "2" {
        Write-Host "`nRestarting worker..." -ForegroundColor Yellow
        docker-compose restart worker_vatican
        Write-Host "✅ Worker restarted" -ForegroundColor Green
        Write-Host "Waiting 10 seconds..." -ForegroundColor Gray
        Start-Sleep -Seconds 10
        Write-Host "`nRe-running verification..." -ForegroundColor Yellow
        & $PSCommandPath
    }
    default {
        Write-Host "`nExiting..." -ForegroundColor Gray
    }
}
