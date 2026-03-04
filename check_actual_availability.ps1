# Check Actual Availability
# This script checks if the bot is actually finding availability or if everything is truly sold out

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Actual Availability Check" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "1. Check recent CheckResult records" -ForegroundColor White
Write-Host "2. Show if any availability was found" -ForegroundColor White
Write-Host "3. Display the actual check details" -ForegroundColor White
Write-Host ""

$checkScript = @"
from monitors.models import MonitorTask, CheckResult
from django.utils import timezone
from datetime import timedelta

print('📊 Checking recent check results...\n')

# Get recent results (last 24 hours)
cutoff = timezone.now() - timedelta(hours=24)
recent_results = CheckResult.objects.filter(
    check_time__gte=cutoff,
    task__site='vatican'
).order_by('-check_time')[:20]

print(f'Found {recent_results.count()} checks in last 24 hours\n')

if recent_results.count() == 0:
    print('⚠️ No recent checks found!')
    print('   This means the bot has not run checks recently.')
    print('   Run: .\force_check_and_verify.ps1 to trigger checks')
else:
    available_count = 0
    sold_out_count = 0
    error_count = 0
    
    for result in recent_results:
        task = result.task
        age = timezone.now() - result.check_time
        minutes_ago = int(age.total_seconds() / 60)
        
        if result.status == 'available':
            available_count += 1
            icon = '✅'
            color = 'GREEN'
        elif result.status == 'sold_out':
            sold_out_count += 1
            icon = '❌'
            color = 'RED'
        else:
            error_count += 1
            icon = '⚠️'
            color = 'YELLOW'
        
        print(f'{icon} Task #{task.id} - {minutes_ago}m ago')
        print(f'   Status: {result.status}')
        print(f'   Visitors: {task.visitors}')
        
        # Show details
        if result.details:
            import json
            details = result.details if isinstance(result.details, dict) else {}
            
            # Check for slots
            slots = details.get('slots', [])
            if slots:
                print(f'   🎉 FOUND {len(slots)} SLOTS!')
                print(f'      First 5: {", ".join(str(s) for s in slots[:5])}')
            else:
                print(f'   No slots found')
            
            # Check for dates
            if 'date' in details:
                print(f'   Date: {details["date"]}')
            
            # Check for ticket info
            if 'ticket_name' in details:
                print(f'   Ticket: {details["ticket_name"]}')
        
        if result.error_message:
            print(f'   Error: {result.error_message}')
        
        print()
    
    print('\n' + '='*60)
    print('SUMMARY')
    print('='*60)
    print(f'✅ Available: {available_count}')
    print(f'❌ Sold Out: {sold_out_count}')
    print(f'⚠️ Errors: {error_count}')
    print()
    
    if available_count > 0:
        print('🎉 The bot IS finding availability!')
        print('   If dashboard shows sold out, the issue is:')
        print('   1. Dashboard not refreshing')
        print('   2. Backend API not accessible from Vercel')
        print('   3. Cloudflare tunnel not working')
    elif sold_out_count > 0:
        print('📊 All recent checks show sold out')
        print('   This could mean:')
        print('   1. Tickets are genuinely sold out')
        print('   2. Bot is checking with wrong parameters (visitor count)')
        print('   3. Bot is not using the new API method')
        print()
        print('   Check logs for visitor count:')
        print('   .\check_logs_windows.ps1')
    else:
        print('⚠️ Only errors found - bot may not be working correctly')

# Check specific Task #19
print('\n' + '='*60)
print('TASK #19 SPECIFIC CHECK (March 16, 1 visitor)')
print('='*60)

try:
    task19 = MonitorTask.objects.get(id=19)
    print(f'Task #19 Configuration:')
    print(f'   Visitors: {task19.visitors}')
    print(f'   Dates: {", ".join(task19.dates[:3])}')
    print(f'   Last Status: {task19.last_status}')
    print(f'   Last Checked: {task19.last_checked}')
    
    # Get recent results for Task #19
    task19_results = CheckResult.objects.filter(
        task=task19,
        check_time__gte=cutoff
    ).order_by('-check_time')[:5]
    
    print(f'\n   Recent checks: {task19_results.count()}')
    for r in task19_results:
        age = timezone.now() - r.check_time
        mins = int(age.total_seconds() / 60)
        print(f'   - {mins}m ago: {r.status}')
        if r.details:
            details = r.details if isinstance(r.details, dict) else {}
            slots = details.get('slots', [])
            if slots:
                print(f'     Found {len(slots)} slots!')
    
    if task19.visitors != 1:
        print(f'\n   ⚠️ WARNING: Task #19 has {task19.visitors} visitors (expected 1)')
        print(f'      This needs to be fixed in the database!')
        
except MonitorTask.DoesNotExist:
    print('❌ Task #19 not found')

"@

$tempFile = [System.IO.Path]::GetTempFileName() + ".py"
$checkScript | Out-File -FilePath $tempFile -Encoding UTF8
Get-Content $tempFile | docker-compose exec -T backend python manage.py shell
Remove-Item $tempFile

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Check Complete" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "If bot IS finding availability but dashboard shows sold out:" -ForegroundColor White
Write-Host "   1. Check backend API: http://localhost:8000/api/tasks/" -ForegroundColor Cyan
Write-Host "   2. Verify Cloudflare tunnel URL in Vercel" -ForegroundColor Cyan
Write-Host "   3. Check browser console for CORS errors" -ForegroundColor Cyan
Write-Host ""
Write-Host "If bot is NOT finding availability:" -ForegroundColor White
Write-Host "   1. Check visitor count in logs: .\check_logs_windows.ps1" -ForegroundColor Cyan
Write-Host "   2. Verify new API method is being used" -ForegroundColor Cyan
Write-Host "   3. Check for errors in worker logs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To force a fresh check:" -ForegroundColor White
Write-Host "   .\force_check_and_verify.ps1" -ForegroundColor Cyan
Write-Host ""
