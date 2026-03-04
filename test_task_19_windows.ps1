# Windows PowerShell Script to Test Task #19
# This script checks Task #19 configuration and triggers a test

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Task #19 Verification Script" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Task #19 configuration
Write-Host "Step 1: Checking Task #19 configuration..." -ForegroundColor Yellow

$pythonScript = @"
from monitors.models import MonitorTask
try:
    task = MonitorTask.objects.get(id=19)
    print(f'✅ Task #19 Found')
    print(f'   Area: {task.area_name}')
    print(f'   Visitors: {task.visitors}')
    print(f'   Dates: {", ".join(task.dates[:3])}{"..." if len(task.dates) > 3 else ""}')
    print(f'   Language: {task.language or "None (Standard)"}')
    print(f'   Ticket Type: {"Standard" if task.ticket_type == 0 else "Guided"}')
    print(f'   Ticket ID: {task.ticket_id}')
    print(f'   Last Checked: {task.last_checked}')
    print(f'   Last Status: {task.last_status}')
    
    # Check for March 16
    if '16/03/2026' in task.dates or '2026-03-16' in task.dates:
        print(f'   ⚠️ Contains March 16 - Should show availability for {task.visitors} visitor(s)')
    
    # Verify visitor count
    if task.visitors == 1:
        print(f'   ✅ Visitor count is correct (1)')
    else:
        print(f'   ⚠️ Visitor count is {task.visitors} (expected 1)')
        
except MonitorTask.DoesNotExist:
    print('❌ Task #19 not found')
except Exception as e:
    print(f'❌ Error: {e}')
"@

# Save to temp file
$tempFile = [System.IO.Path]::GetTempFileName() + ".py"
$pythonScript | Out-File -FilePath $tempFile -Encoding UTF8

# Execute in Django shell
Get-Content $tempFile | docker-compose exec -T backend python manage.py shell

# Clean up
Remove-Item $tempFile

Write-Host ""

# Step 2: Ask if user wants to trigger a check
Write-Host "Step 2: Trigger a test check for Task #19?" -ForegroundColor Yellow
Write-Host "This will run orchestrate_all_tasks() which will check all active tasks." -ForegroundColor Gray
Write-Host "Would you like to proceed? (Y/N): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`nTriggering orchestration..." -ForegroundColor Yellow
    
    $triggerScript = @"
from monitors.tasks import orchestrate_all_tasks
try:
    result = orchestrate_all_tasks()
    print(f'✅ Orchestration triggered: {result}')
except Exception as e:
    print(f'❌ Error: {e}')
"@
    
    $tempFile2 = [System.IO.Path]::GetTempFileName() + ".py"
    $triggerScript | Out-File -FilePath $tempFile2 -Encoding UTF8
    
    Get-Content $tempFile2 | docker-compose exec -T backend python manage.py shell
    
    Remove-Item $tempFile2
    
    Write-Host "`n✅ Check triggered! Monitor logs with:" -ForegroundColor Green
    Write-Host "   .\check_logs_windows.ps1" -ForegroundColor Cyan
    Write-Host "   or" -ForegroundColor Gray
    Write-Host "   docker-compose logs -f worker_vatican" -ForegroundColor Cyan
    
    Write-Host "`nWould you like to see live logs now? (Y/N): " -NoNewline -ForegroundColor Yellow
    $logsResponse = Read-Host
    
    if ($logsResponse -eq "Y" -or $logsResponse -eq "y") {
        Write-Host "`nShowing live logs (Press Ctrl+C to stop)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        docker-compose logs -f worker_vatican
    }
} else {
    Write-Host "`nSkipped orchestration trigger" -ForegroundColor Gray
}

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Verification Complete" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
