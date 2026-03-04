# PowerShell script to get backend URL for Vercel

Write-Host "=========================================="
Write-Host "Backend URL for Vercel Dashboard"
Write-Host "=========================================="
Write-Host ""

# Test if backend is running
Write-Host "Testing backend..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/" -UseBasicParsing -TimeoutSec 5
    Write-Host "[OK] Backend is running on port 8000" -ForegroundColor Green
    Write-Host ""
    
    # Parse response
    $tasks = $response.Content | ConvertFrom-Json
    Write-Host "Found $($tasks.Count) tasks:" -ForegroundColor Cyan
    foreach ($task in $tasks) {
        $status_icon = if ($task.last_status -eq "available") { "[OK]" } else { "X" }
        $status_color = if ($task.last_status -eq "available") { "Green" } else { "Red" }
        Write-Host "  $status_icon Task #$($task.id) - $($task.area_name) - $($task.dates[0]) - $($task.last_status)" -ForegroundColor $status_color
    }
    Write-Host ""
    
} catch {
    Write-Host "X Backend is not running on port 8000" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start your backend first:"
    Write-Host "  docker-compose up -d"
    Write-Host ""
    exit 1
}

# Show options
Write-Host "=========================================="
Write-Host "Your backend is LOCAL (localhost:8000)"
Write-Host "=========================================="
Write-Host ""
Write-Host "Vercel CANNOT access localhost!" -ForegroundColor Yellow
Write-Host "You need to expose your backend publicly." -ForegroundColor Yellow
Write-Host ""

Write-Host "OPTION 1: Use ngrok (Fastest)" -ForegroundColor Cyan
Write-Host "  1. Download: https://ngrok.com/download"
Write-Host "  2. Run: ngrok http 8000"
Write-Host "  3. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)"
Write-Host "  4. In Vercel: NEXT_PUBLIC_API_URL=https://abc123.ngrok.io/api/v1"
Write-Host ""

Write-Host "OPTION 2: Use Cloudflare Tunnel (Free)" -ForegroundColor Cyan
Write-Host "  1. Download: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
Write-Host "  2. Run: cloudflared tunnel --url http://localhost:8000"
Write-Host "  3. Copy the URL (e.g., https://xyz.trycloudflare.com)"
Write-Host "  4. In Vercel: NEXT_PUBLIC_API_URL=https://xyz.trycloudflare.com/api/v1"
Write-Host ""

Write-Host "OPTION 3: Deploy to Production (Recommended)" -ForegroundColor Cyan
Write-Host "  - Railway: railway up"
Write-Host "  - Render: Connect GitHub repo"
Write-Host "  - DigitalOcean/AWS: Deploy Docker container"
Write-Host "  - In Vercel: NEXT_PUBLIC_API_URL=https://your-backend.com/api/v1"
Write-Host ""

Write-Host "=========================================="
Write-Host "Quick Start with ngrok:"
Write-Host "=========================================="
Write-Host ""

# Check if ngrok is installed
$ngrokInstalled = Get-Command ngrok -ErrorAction SilentlyContinue
if ($ngrokInstalled) {
    Write-Host "[OK] ngrok is installed" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run this command to start ngrok:" -ForegroundColor Yellow
    Write-Host "  ngrok http 8000" -ForegroundColor White
    Write-Host ""
    
    $startNgrok = Read-Host "Start ngrok now? (y/n)"
    if ($startNgrok -eq "y" -or $startNgrok -eq "Y") {
        Write-Host ""
        Write-Host "Starting ngrok..." -ForegroundColor Green
        Write-Host "Copy the HTTPS URL and use it in Vercel!" -ForegroundColor Yellow
        Write-Host ""
        ngrok http 8000
    }
} else {
    Write-Host "X ngrok is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install ngrok:"
    Write-Host "  1. Go to: https://ngrok.com/download"
    Write-Host "  2. Download for Windows"
    Write-Host "  3. Extract and add to PATH"
    Write-Host "  4. Run: ngrok http 8000"
    Write-Host ""
}

Write-Host "=========================================="
Write-Host "Full guide: VERCEL_DASHBOARD_SETUP.md"
Write-Host "=========================================="
