# 🔧 QUICK FIX FOR VATICAN BOT
# This script fixes the proxy and stale ID issues

Write-Host "🔧 FIXING VATICAN BOT..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Check current proxy status
Write-Host "📊 Step 1: Checking current proxy status..." -ForegroundColor Yellow
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import Proxy; print(f'Before: {Proxy.objects.count()} proxies')"
Write-Host ""

# Step 2: Seed proxies
Write-Host "🌱 Step 2: Seeding proxies into database..." -ForegroundColor Yellow
docker exec travelagenntbot-backend-1 python /app/backend/manage.py seed_proxies
Write-Host ""

# Step 3: Verify proxies were added
Write-Host "✅ Step 3: Verifying proxies..." -ForegroundColor Yellow
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import Proxy; total = Proxy.objects.count(); active = Proxy.objects.filter(is_active=True).count(); print(f'After: {total} total proxies, {active} active')"
Write-Host ""

# Step 4: Clear stale ticket IDs
Write-Host "🗑️ Step 4: Clearing stale ticket IDs..." -ForegroundColor Yellow
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import MonitorTask; updated = MonitorTask.objects.filter(site='vatican').update(ticket_id=None); print(f'Cleared {updated} stale ticket IDs')"
Write-Host ""

# Step 5: Restart worker
Write-Host "🔄 Step 5: Restarting worker..." -ForegroundColor Yellow
docker-compose restart worker_vatican
Write-Host ""

Write-Host "✅ FIX COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Wait 2-3 minutes for worker to start checking"
Write-Host "2. Monitor logs: docker-compose logs -f worker_vatican"
Write-Host "3. Look for: 'Session Cookies', 'Resolved X Dynamic IDs', 'Found X slots'"
Write-Host ""
Write-Host "🔍 To check logs now, run:" -ForegroundColor Yellow
Write-Host "docker-compose logs -f worker_vatican | Select-String -Pattern 'Session Cookies|Resolved.*IDs|Found.*slots|STATE CHANGE'"
