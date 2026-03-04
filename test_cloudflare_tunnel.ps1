# Test Cloudflare Tunnel Connection

Write-Host "=========================================="
Write-Host "Testing Cloudflare Tunnel"
Write-Host "=========================================="
Write-Host ""

# Check if cloudflared is running
$cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cloudflared) {
    Write-Host "[OK] Cloudflared is running (PID: $($cloudflared.Id))" -ForegroundColor Green
} else {
    Write-Host "X Cloudflared is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Start cloudflared with:"
    Write-Host "  cloudflared tunnel --url http://localhost:8000"
    Write-Host ""
    exit 1
}

Write-Host ""

# Test local backend first
Write-Host "1. Testing local backend..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/" -UseBasicParsing -TimeoutSec 5
    $tasks = $response.Content | ConvertFrom-Json
    Write-Host "[OK] Local backend is working" -ForegroundColor Green
    Write-Host "   Found $($tasks.Count) tasks" -ForegroundColor Cyan
    
    foreach ($task in $tasks) {
        $status_icon = if ($task.last_status -eq "available") { "[OK]" } else { "X" }
        $status_color = if ($task.last_status -eq "available") { "Green" } else { "Red" }
        $slots = if ($task.latest_check.details.slots) { $task.latest_check.details.slots.Count } else { 0 }
        Write-Host "   $status_icon Task #$($task.id) - $($task.dates[0]) - $($task.last_status) - $slots slots" -ForegroundColor $status_color
    }
} catch {
    Write-Host "X Local backend is not responding" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Ask for Cloudflare tunnel URL
Write-Host "2. Enter your Cloudflare tunnel URL"
Write-Host "   (The URL shown when you ran: cloudflared tunnel --url http://localhost:8000)"
Write-Host ""
$tunnelUrl = Read-Host "Cloudflare URL (e.g., https://xyz.trycloudflare.com)"

if (-not $tunnelUrl) {
    Write-Host "X No URL provided" -ForegroundColor Red
    exit 1
}

# Remove trailing slash
$tunnelUrl = $tunnelUrl.TrimEnd('/')

Write-Host ""
Write-Host "3. Testing Cloudflare tunnel..."
Write-Host "   URL: $tunnelUrl/api/v1/tasks/"
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "$tunnelUrl/api/v1/tasks/" -UseBasicParsing -TimeoutSec 10
    $tasks = $response.Content | ConvertFrom-Json
    
    Write-Host "[OK] Cloudflare tunnel is working!" -ForegroundColor Green
    Write-Host "   Found $($tasks.Count) tasks" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($task in $tasks) {
        $status_icon = if ($task.last_status -eq "available") { "[OK]" } else { "X" }
        $status_color = if ($task.last_status -eq "available") { "Green" } else { "Red" }
        $slots = if ($task.latest_check.details.slots) { $task.latest_check.details.slots.Count } else { 0 }
        Write-Host "   $status_icon Task #$($task.id) - $($task.dates[0]) - $($task.last_status) - $slots slots" -ForegroundColor $status_color
    }
    
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "SUCCESS!"
    Write-Host "=========================================="
    Write-Host ""
    Write-Host "Your Cloudflare tunnel is working correctly!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Vercel Configuration:" -ForegroundColor Cyan
    Write-Host "  1. Go to Vercel Dashboard"
    Write-Host "  2. Select your project"
    Write-Host "  3. Settings -> Environment Variables"
    Write-Host "  4. Set: NEXT_PUBLIC_API_URL = $tunnelUrl/api/v1"
    Write-Host "  5. Redeploy your frontend"
    Write-Host ""
    Write-Host "If dashboard still shows 'sold out':" -ForegroundColor Yellow
    Write-Host "  - Clear browser cache (Ctrl+Shift+Delete)"
    Write-Host "  - Hard refresh (Ctrl+F5)"
    Write-Host "  - Check browser console (F12) for errors"
    Write-Host "  - Verify NEXT_PUBLIC_API_URL is set correctly"
    Write-Host ""
    
} catch {
    Write-Host "X Cloudflare tunnel is not accessible" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "Troubleshooting:"
    Write-Host "  1. Make sure cloudflared is running"
    Write-Host "  2. Check the URL is correct (should start with https://)"
    Write-Host "  3. Try accessing the URL in your browser"
    Write-Host "  4. Check if there are any firewall issues"
    Write-Host ""
    exit 1
}

Write-Host "=========================================="
Write-Host "Testing Complete"
Write-Host "=========================================="
