# Check Dashboard Data and Cloudflare Tunnel

Write-Host "=========================================="
Write-Host "Dashboard Data Check"
Write-Host "=========================================="
Write-Host ""

# 1. Check local backend
Write-Host "1. Checking local backend data..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/" -UseBasicParsing -TimeoutSec 5
    $tasks = $response.Content | ConvertFrom-Json
    
    Write-Host "[OK] Backend is running" -ForegroundColor Green
    Write-Host ""
    Write-Host "Current Tasks:" -ForegroundColor Cyan
    foreach ($task in $tasks) {
        $status_icon = if ($task.last_status -eq "available") { "[OK]" } elseif ($task.last_status -eq "sold_out") { "X" } else { "?" }
        $status_color = if ($task.last_status -eq "available") { "Green" } elseif ($task.last_status -eq "sold_out") { "Red" } else { "Yellow" }
        
        $lastChecked = if ($task.last_checked) {
            $dt = [DateTime]::Parse($task.last_checked)
            $ago = (Get-Date) - $dt
            if ($ago.TotalMinutes -lt 5) {
                "$([int]$ago.TotalMinutes) min ago"
            } elseif ($ago.TotalHours -lt 2) {
                "$([int]$ago.TotalMinutes) min ago"
            } else {
                "$([int]$ago.TotalHours) hours ago"
            }
        } else {
            "Never"
        }
        
        Write-Host "  $status_icon Task #$($task.id) - $($task.dates[0]) - $($task.last_status) - Checked: $lastChecked" -ForegroundColor $status_color
    }
} catch {
    Write-Host "X Backend is not responding" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2. Checking Cloudflare tunnel..."

# Check if cloudflared is running
$cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cloudflared) {
    Write-Host "[OK] Cloudflared is running (PID: $($cloudflared.Id))" -ForegroundColor Green
} else {
    Write-Host "X Cloudflared is NOT running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Start cloudflared with:"
    Write-Host "  cloudflared tunnel --url http://localhost:8000"
    Write-Host ""
}

Write-Host ""
Write-Host "3. Checking Vercel dashboard..."
try {
    $response = Invoke-WebRequest -Uri "https://bot-pl2x.vercel.app/" -UseBasicParsing -TimeoutSec 10
    Write-Host "[OK] Dashboard is accessible" -ForegroundColor Green
    Write-Host "   Status: $($response.StatusCode)"
    Write-Host "   Size: $($response.Content.Length) bytes"
} catch {
    Write-Host "X Dashboard is not accessible" -ForegroundColor Red
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Next Steps"
Write-Host "=========================================="
Write-Host ""

if ($cloudflared) {
    Write-Host "Your Cloudflare tunnel is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To connect your dashboard:"
    Write-Host "  1. Find your Cloudflare URL in the cloudflared terminal"
    Write-Host "  2. Go to Vercel Dashboard -> Settings -> Environment Variables"
    Write-Host "  3. Set: NEXT_PUBLIC_API_URL = https://your-url.trycloudflare.com/api/v1"
    Write-Host "  4. Redeploy your frontend"
    Write-Host ""
    Write-Host "Test your tunnel URL:"
    $tunnelUrl = Read-Host "Enter your Cloudflare tunnel URL (or press Enter to skip)"
    
    if ($tunnelUrl) {
        $tunnelUrl = $tunnelUrl.TrimEnd('/')
        Write-Host ""
        Write-Host "Testing $tunnelUrl/api/v1/tasks/..."
        try {
            $response = Invoke-WebRequest -Uri "$tunnelUrl/api/v1/tasks/" -UseBasicParsing -TimeoutSec 10
            $tasks = $response.Content | ConvertFrom-Json
            Write-Host "[OK] Tunnel is working!" -ForegroundColor Green
            Write-Host "   Found $($tasks.Count) tasks"
            Write-Host ""
            Write-Host "Use this in Vercel:" -ForegroundColor Yellow
            Write-Host "  NEXT_PUBLIC_API_URL=$tunnelUrl/api/v1" -ForegroundColor White
        } catch {
            Write-Host "X Tunnel is not accessible" -ForegroundColor Red
            Write-Host "   Error: $($_.Exception.Message)"
        }
    }
} else {
    Write-Host "Cloudflare tunnel is NOT running!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Start it with:"
    Write-Host "  cloudflared tunnel --url http://localhost:8000"
    Write-Host ""
    Write-Host "Or use ngrok:"
    Write-Host "  ngrok http 8000"
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Current Backend Data (Fresh)"
Write-Host "=========================================="
Write-Host ""

foreach ($task in $tasks) {
    Write-Host "Task #$($task.id) - $($task.dates[0]):" -ForegroundColor Cyan
    Write-Host "  Status: $($task.last_status)"
    Write-Host "  Language: $($task.language)"
    Write-Host "  Ticket Type: $($task.ticket_type)"
    Write-Host "  Last Checked: $($task.last_checked)"
    Write-Host ""
}
