# Telegram Bot Quick Setup Script

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TELEGRAM BOT SETUP" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if token exists in .env
$envFile = ".env"
$tokenExists = $false

if (Test-Path $envFile) {
    $content = Get-Content $envFile
    if ($content -match "TELEGRAM_BOT_TOKEN=") {
        $tokenExists = $true
        Write-Host "✅ TELEGRAM_BOT_TOKEN found in .env" -ForegroundColor Green
    }
}

if (-not $tokenExists) {
    Write-Host "⚠️  TELEGRAM_BOT_TOKEN not found in .env" -ForegroundColor Yellow
    Write-Host "`nSteps to get your bot token:" -ForegroundColor Yellow
    Write-Host "  1. Open Telegram and search for @BotFather" -ForegroundColor White
    Write-Host "  2. Send: /newbot" -ForegroundColor White
    Write-Host "  3. Follow instructions to create bot" -ForegroundColor White
    Write-Host "  4. Copy the token BotFather gives you" -ForegroundColor White
    Write-Host "  5. Add to .env file:" -ForegroundColor White
    Write-Host "     TELEGRAM_BOT_TOKEN=your_token_here`n" -ForegroundColor Gray
    
    $addNow = Read-Host "Do you have a token to add now? (y/n)"
    
    if ($addNow -eq 'y') {
        $token = Read-Host "Enter your bot token"
        Add-Content -Path $envFile -Value "`nTELEGRAM_BOT_TOKEN=$token"
        Write-Host "✅ Token added to .env" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Please add TELEGRAM_BOT_TOKEN to .env and run this script again." -ForegroundColor Red
        exit 1
    }
}

# Check if python-telegram-bot is installed
Write-Host "`nChecking dependencies..." -ForegroundColor Yellow

$installed = docker-compose exec -T backend pip list 2>&1 | Select-String "python-telegram-bot"

if (-not $installed) {
    Write-Host "⚠️  python-telegram-bot not installed" -ForegroundColor Yellow
    Write-Host "Installing..." -ForegroundColor Yellow
    docker-compose exec -T backend pip install python-telegram-bot==20.7
    Write-Host "✅ Installed python-telegram-bot" -ForegroundColor Green
} else {
    Write-Host "✅ python-telegram-bot already installed" -ForegroundColor Green
}

# Check if telegram_bot.py exists
if (-not (Test-Path "telegram_bot.py")) {
    Write-Host "`n❌ telegram_bot.py not found!" -ForegroundColor Red
    Write-Host "Please ensure telegram_bot.py is in the project root." -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ telegram_bot.py found" -ForegroundColor Green

# Ask if user wants to add to docker-compose
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DOCKER COMPOSE CONFIGURATION" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$addToCompose = Read-Host "Add telegram bot to docker-compose.yml? (y/n)"

if ($addToCompose -eq 'y') {
    Write-Host "`nAdd this to your docker-compose.yml:" -ForegroundColor Yellow
    Write-Host @"

  telegram_bot:
    build:
      context: .
      dockerfile: Dockerfile
    command: python /app/telegram_bot.py
    volumes:
      - ./backend:/app/backend
      - ./telegram_bot.py:/app/telegram_bot.py
    environment:
      - TELEGRAM_BOT_TOKEN=`${TELEGRAM_BOT_TOKEN}
      - DJANGO_SETTINGS_MODULE=backend.core.settings
    depends_on:
      - backend
      - redis
    restart: unless-stopped

"@ -ForegroundColor Gray

    Write-Host "`nThen run: docker-compose up -d telegram_bot`n" -ForegroundColor White
}

# Test bot (standalone mode)
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TESTING BOT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$testNow = Read-Host "Test bot in standalone mode? (y/n)"

if ($testNow -eq 'y') {
    Write-Host "`nStarting bot..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray
    
    # Copy telegram_bot.py to backend folder for Docker access
    Copy-Item telegram_bot.py backend/telegram_bot.py -Force
    
    docker-compose exec backend python /app/telegram_bot.py
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "1. Open Telegram and search for your bot" -ForegroundColor White
Write-Host "2. Send /start to begin" -ForegroundColor White
Write-Host "3. Bot will show your chat ID" -ForegroundColor White
Write-Host "4. Link chat ID to your agency:" -ForegroundColor White
Write-Host "   docker-compose exec backend python manage.py shell" -ForegroundColor Gray
Write-Host "   >>> from monitors.models import Agency" -ForegroundColor Gray
Write-Host "   >>> agency = Agency.objects.get(name='Agency-admin')" -ForegroundColor Gray
Write-Host "   >>> agency.telegram_chat_id = 'YOUR_CHAT_ID'" -ForegroundColor Gray
Write-Host "   >>> agency.save()" -ForegroundColor Gray
Write-Host "5. Send /start again to use the bot!`n" -ForegroundColor White

Write-Host "📖 Full documentation: TELEGRAM_BOT_SETUP.md`n" -ForegroundColor Cyan
