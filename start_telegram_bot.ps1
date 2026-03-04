# Quick Start Telegram Bot (Token Already Configured)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TELEGRAM BOT - QUICK START" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Verify token exists
Write-Host "1. Checking configuration..." -ForegroundColor Yellow

$envFile = ".env"
$tokenExists = $false

if (Test-Path $envFile) {
    $content = Get-Content $envFile
    if ($content -match "TELEGRAM_BOT_TOKEN=(.+)") {
        $tokenExists = $true
        $tokenPreview = $matches[1].Substring(0, [Math]::Min(20, $matches[1].Length)) + "..."
        Write-Host "   ✅ Token found: $tokenPreview" -ForegroundColor Green
    }
}

if (-not $tokenExists) {
    Write-Host "   ❌ TELEGRAM_BOT_TOKEN not found in .env" -ForegroundColor Red
    Write-Host "   Please add your token to .env file" -ForegroundColor Red
    exit 1
}

# 2. Check if dependency is installed
Write-Host "`n2. Checking dependencies..." -ForegroundColor Yellow

$checkInstalled = docker-compose exec -T backend pip list 2>&1 | Select-String "python-telegram-bot"

if (-not $checkInstalled) {
    Write-Host "   ⚠️  python-telegram-bot not installed" -ForegroundColor Yellow
    Write-Host "   Installing now..." -ForegroundColor Yellow
    
    docker-compose exec -T backend pip install python-telegram-bot==20.7 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Installed python-telegram-bot" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to install. Try manually:" -ForegroundColor Red
        Write-Host "   docker-compose exec backend pip install python-telegram-bot==20.7" -ForegroundColor Gray
        exit 1
    }
} else {
    Write-Host "   ✅ python-telegram-bot already installed" -ForegroundColor Green
}

# 3. Verify chat ID is linked
Write-Host "`n3. Checking agency configuration..." -ForegroundColor Yellow

$checkAgency = docker-compose exec -T backend python -c @"
import django, os, sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from monitors.models import Agency
agency = Agency.objects.filter(telegram_chat_id__isnull=False).first()
if agency:
    print(f'FOUND:{agency.name}:{agency.telegram_chat_id}')
else:
    print('NONE')
"@ 2>&1

if ($checkAgency -match "FOUND:(.+):(.+)") {
    $agencyName = $matches[1]
    $chatId = $matches[2]
    Write-Host "   ✅ Agency linked: $agencyName" -ForegroundColor Green
    Write-Host "   ✅ Chat ID: $chatId" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  No agency has telegram_chat_id set" -ForegroundColor Yellow
    Write-Host "   You'll need to link your chat ID after starting the bot" -ForegroundColor Yellow
}

# 4. Copy bot file to backend
Write-Host "`n4. Preparing bot file..." -ForegroundColor Yellow

if (Test-Path "telegram_bot.py") {
    Copy-Item telegram_bot.py backend/telegram_bot.py -Force
    Write-Host "   ✅ Bot file ready" -ForegroundColor Green
} else {
    Write-Host "   ❌ telegram_bot.py not found!" -ForegroundColor Red
    exit 1
}

# 5. Start the bot
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "STARTING TELEGRAM BOT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Bot is starting..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

Write-Host "📱 Open Telegram and search for your bot" -ForegroundColor Cyan
Write-Host "📤 Send /start to begin`n" -ForegroundColor Cyan

# Start the bot
docker-compose exec backend python /app/telegram_bot.py
