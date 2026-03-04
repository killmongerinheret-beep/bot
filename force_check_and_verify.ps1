# Force Check and Verify Dashboard Data
# This script forces a fresh check and verifies the backend/dashboard connection

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Force Check and Dashboard Verification" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if services are running
Write-Host "Step 1: Checking services..." -ForegroundColor Yellow
$services = docker-compose ps --services --filter "status=running"
Write-Host "Running services: $($services -join ', ')" -ForegroundColor Green
Write-Host ""

# Step 2: Check current task statuses
Write-Host "Step 2: Checking current task statuses..." -ForegroundColor Yellow

$checkScript = @"
from monitors.models import MonitorTask
from django.utils import timezone

tasks = MonitorTask.objects.filter(is_active=True, site='vatican').order_by('id')
print(f'\n📊 Found {tasks.count()} active Vatican tasks\n')

for task in tasks:
    age = 'Never'
    if task.last_checked:
        delta = timezone.now() - task.last_checked
        minutes = int(delta.total_seconds() / 60)
        if minutes < 60:
            age = f'{minutes}m ago'
        else:
            hours = int(minutes / 60)
            age = f'{hours}h ago'
    
    status_icon = '❌' if task.last_status == 'sold_out' else '✅' if task.last_status == 'available' else '❓'
    
    print(f'{status_icon} Task #{task.id}: {task.area_name}')
    print(f'   Visitors: {task.visitors}')
    print(f'   Status: {task.last_status or "unknown"}')
    print(f'   Last Checked: {age}')
    print(f'   Dates: {", ".join(task.dates[:2])}{"..." if len(task.dates) > 2 else ""}')
    print()
"@

$tempFile = [System.IO.Path]::GetTempFileName() + ".py"
$checkScript | Out-File -FilePath $tempFile -Encoding UTF8
Get-Content $tempFile | docker-compose exec -T backend python manage.py shell
Remove-Item $tempFile

Write-Host ""

# Step 3: Force orchestration
Write-Host "Step 3: Forcing fresh orchestration..." -ForegroundColor Yellow
Write-Host "This will trigger checks for all active tasks." -ForegroundColor Gray
Write-Host ""

$orchestrateScript = @"
from monitors.tasks import orchestrate_all_tasks
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print('🚀 Triggering orchestrate_all_tasks()...')
try:
    result = orchestrate_all_tasks()
    print(f'✅ Result: {result}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"@

$tempFile2 = [System.IO.Path]::GetTempFileName() + ".py"
$orchestrateScript | Out-File -FilePath $tempFile2 -Encoding UTF8
Get-Content $tempFile2 | docker-compose exec -T backend python manage.py shell
Remove-Item $tempFile2

Write-Host ""
Write-Host "✅ Orchestration triggered!" -ForegroundColor Green
Write-Host ""

# Step 4: Wait and show worker logs
Write-Host "Step 4: Monitoring worker activity..." -ForegroundColor Yellow
Write-Host "Waiting 10 seconds for workers to process tasks..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Write-Host "`nRecent worker logs:" -ForegroundColor Yellow
docker-compose logs --tail=30 worker_vatican

Write-Host ""

# Step 5: Check backend API
Write-Host "Step 5: Testing backend API..." -ForegroundColor Yellow

$apiScript = @"
import requests
import json

try:
    # Test if backend is accessible
    response = requests.get('http://localhost:8000/api/tasks/', timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Backend API is accessible')
        print(f'   Found {len(data)} tasks in API response')
        
        # Show first few tasks
        for task in data[:3]:
            print(f'\n   Task #{task.get("id")}:')
            print(f'      Status: {task.get("last_status", "unknown")}')
            print(f'      Last Checked: {task.get("last_checked", "never")}')
            if task.get('latest_check'):
                check = task['latest_check']
                print(f'      Latest Check Status: {check.get("status")}')
                if check.get('details'):
                    details = check['details']
                    if isinstance(details, dict):
                        slots = details.get('slots', [])
                        print(f'      Slots Found: {len(slots)}')
    else:
        print(f'⚠️ Backend returned status {response.status_code}')
        
except requests.exceptions.ConnectionError:
    print('❌ Cannot connect to backend at http://localhost:8000')
    print('   Is the backend service running?')
    print('   Check with: docker-compose ps backend')
except Exception as e:
    print(f'❌ Error: {e}')
"@

$tempFile3 = [System.IO.Path]::GetTempFileName() + ".py"
$apiScript | Out-File -FilePath $tempFile3 -Encoding UTF8
Get-Content $tempFile3 | docker-compose exec -T backend python manage.py shell
Remove-Item $tempFile3

Write-Host ""

# Step 6: Check Cloudflare tunnel
Write-Host "Step 6: Checking Cloudflare tunnel..." -ForegroundColor Yellow

$tunnelScript = @"
import os
import subprocess
import json

# Check if cloudflared is running
try:
    result = subprocess.run(['docker-compose', 'ps', '--format', 'json'], 
                          capture_output=True, text=True, timeout=5)
    
    if result.returncode == 0:
        services = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    services.append(json.loads(line))
                except:
                    pass
        
        tunnel_running = any('cloudflare' in s.get('Service', '').lower() or 
                           'tunnel' in s.get('Service', '').lower() 
                           for s in services)
        
        if tunnel_running:
            print('✅ Cloudflare tunnel appears to be running')
        else:
            print('⚠️ Cloudflare tunnel not detected in docker-compose')
            print('   The tunnel might be running separately')
    
    # Check environment for tunnel URL
    tunnel_url = os.getenv('CLOUDFLARE_TUNNEL_URL')
    if tunnel_url:
        print(f'   Tunnel URL from env: {tunnel_url}')
    else:
        print('   No CLOUDFLARE_TUNNEL_URL in environment')
        
except Exception as e:
    print(f'⚠️ Could not check tunnel status: {e}')

print('\n📝 Note: If using Cloudflare tunnel, make sure:')
print('   1. Tunnel is running and pointing to backend:8000')
print('   2. Vercel dashboard is configured with tunnel URL')
print('   3. CORS is enabled in Django settings')
"@

$tempFile4 = [System.IO.Path]::GetTempFileName() + ".py"
$tunnelScript | Out-File -FilePath $tempFile4 -Encoding UTF8
Get-Content $tempFile4 | docker-compose exec -T backend python manage.py shell
Remove-Item $tempFile4

Write-Host ""

# Step 7: Summary and next steps
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Verification Complete" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Wait 2-3 minutes for checks to complete" -ForegroundColor White
Write-Host "   Tasks run every 60-120 seconds based on check_interval" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Monitor worker logs:" -ForegroundColor White
Write-Host "   docker-compose logs -f worker_vatican" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Check for these patterns:" -ForegroundColor White
Write-Host "   ✅ 'Smart Group: .../1v' (grouping by visitor count)" -ForegroundColor Green
Write-Host "   ✅ '/fromtag/1/...' (correct visitor count in deep links)" -ForegroundColor Green
Write-Host "   ✅ 'visitorNum=1' (correct visitor count in API calls)" -ForegroundColor Green
Write-Host "   ✅ 'Found X slots' (availability detected)" -ForegroundColor Green
Write-Host ""
Write-Host "4. Refresh Vercel dashboard:" -ForegroundColor White
Write-Host "   https://bot-pl2x.vercel.app/" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. If still showing sold out:" -ForegroundColor White
Write-Host "   a) Check backend API: http://localhost:8000/api/tasks/" -ForegroundColor Cyan
Write-Host "   b) Verify Cloudflare tunnel is running" -ForegroundColor Cyan
Write-Host "   c) Check CORS settings in Django" -ForegroundColor Cyan
Write-Host "   d) Run: .\check_logs_windows.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "Would you like to see live worker logs now? (Y/N): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`nShowing live logs (Press Ctrl+C to stop)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    docker-compose logs -f worker_vatican
}
