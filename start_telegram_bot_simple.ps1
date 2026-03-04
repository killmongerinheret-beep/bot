# Start Telegram Bot - Simple Version
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TELEGRAM BOT - STARTING" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check if backend is running
Write-Host "1. Checking backend..." -ForegroundColor Yellow
$backendRunning = docker-compose ps backend 2>&1 | Select-String "Up"

if (-not $backendRunning) {
    Write-Host "   ❌ Backend not running!" -ForegroundColor Red
    Write-Host "   Starting backend..." -ForegroundColor Yellow
    docker-compose up -d backend
    Start-Sleep -Seconds 5
    Write-Host "   ✅ Backend started" -ForegroundColor Green
} else {
    Write-Host "   ✅ Backend is running" -ForegroundColor Green
}

# 2. Check token
Write-Host "`n2. Checking Telegram token..." -ForegroundColor Yellow
$envFile = ".env"
$tokenExists = $false

if (Test-Path $envFile) {
    $content = Get-Content $envFile
    if ($content -match "TELEGRAM_BOT_TOKEN=(.+)") {
        $tokenExists = $true
        Write-Host "   ✅ Token found" -ForegroundColor Green
    }
}

if (-not $tokenExists) {
    Write-Host "   ❌ TELEGRAM_BOT_TOKEN not found in .env" -ForegroundColor Red
    Write-Host "   Please add your token to .env file" -ForegroundColor Red
    exit 1
}

# 3. Copy bot file to backend
Write-Host "`n3. Copying bot file..." -ForegroundColor Yellow
if (Test-Path "telegram_bot.py") {
    docker cp telegram_bot.py travelagenntbot-backend-1:/app/telegram_bot.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Bot file copied" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to copy bot file" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ❌ telegram_bot.py not found!" -ForegroundColor Red
    exit 1
}

# 4. Copy calendar file too
Write-Host "`n4. Copying calendar file..." -ForegroundColor Yellow
if (Test-Path "telegram_bot_calendar.py") {
    docker cp telegram_bot_calendar.py travelagenntbot-backend-1:/app/telegram_bot_calendar.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Calendar file copied" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Calendar file copy failed (not critical)" -ForegroundColor Yellow
    }
}

# 5. Install dependencies
Write-Host "`n5. Installing dependencies..." -ForegroundColor Yellow
docker-compose exec -T backend pip install python-telegram-bot==20.7 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Dependencies may already be installed" -ForegroundColor Yellow
}

# 6. Start the bot
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "STARTING BOT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📱 Bot is starting..." -ForegroundColor Yellow
Write-Host "📤 Open Telegram and send /start to your bot`n" -ForegroundColor Cyan
Write-Host "⚠️  Press Ctrl+C to stop the bot`n" -ForegroundColor Yellow

# Start the bot
docker-compose exec backend python /app/telegram_bot.py
