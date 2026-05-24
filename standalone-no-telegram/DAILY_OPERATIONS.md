# Daily Operations Guide

## 🚀 Quick Start (Every Day)

### 1. Check System Status (30 seconds)

```powershell
# Check all services running
docker-compose ps

# Should see:
# backend         Up
# worker_vatican  Up
# postgres        Up
# redis           Up
# nginx           Up
```

### 2. Check Active Tasks (1 minute)

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import MonitorTask
from django.utils import timezone

# Active tasks
active = MonitorTask.objects.filter(is_active=True)
print(f"✅ Active tasks: {active.count()}")

# Tasks by date
from collections import Counter
dates = Counter([t.date for t in active])
for date, count in sorted(dates.items()):
    print(f"   {date}: {count} tasks")

# Recent activity
recent = MonitorTask.objects.filter(
    last_checked__gte=timezone.now() - timezone.timedelta(minutes=5)
)
print(f"\n✅ Recently checked: {recent.count()} tasks")

exit()
```

### 3. Check Extension Status (30 seconds)

1. Open Chrome/Edge
2. Click extension icon
3. Verify:
   - ✅ Backend Listener: ON
   - ✅ Polling: Every 10 seconds
   - ✅ Backend URL: Correct
   - ✅ Available Slots: Number shown

---

## 📊 Adding New Booking Requests

### Method 1: Google Sheets (Recommended)

1. Open your Google Sheets
2. Go to "Booking Requests" tab
3. Add new row:
   ```
   REQ-XXX | DD/MM/YYYY | 2 | standard | | pending | | 2026-05-22 10:00:00
   ```
4. Go to "Participants" tab
5. Add participant rows:
   ```
   REQ-XXX | John | Doe | john@example.com | +39 123456789 | 1990-01-01 | Roma | Italia
   ```
6. Wait 5 minutes for auto-sync (or trigger manually)

### Method 2: Manual Sync (Instant)

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.tasks_booking_sync import sync_booking_requests
result = sync_booking_requests()
print(f"✅ Created {result['total_created']} tasks")
exit()
```

---

## 🔍 Monitoring Operations

### Check Worker Logs (Real-Time)

```powershell
# Follow worker logs
docker-compose logs -f worker_vatican

# Look for:
# [INFO] Monitoring 5 tasks
# [INFO] Task REQ-001: 28/03/2026, 2 visitors
# [INFO] ✅ Found 3 available slots for 28/03/2026
```

### Check Backend Logs (Real-Time)

```powershell
# Follow backend logs
docker-compose logs -f backend

# Look for:
# [INFO] Scheduler: Sending due task sync-booking-requests
# [INFO] Syncing booking requests for agency 1
# [INFO] Created task 123 for request REQ-001
```

### Check Extension Logs

1. Right-click extension icon
2. Click "Inspect popup"
3. Go to Console tab
4. Look for:
   ```
   [Backend Listener] Polling...
   [Backend Listener] Found 2 available slots
   [Auto Booking] Opening incognito window...
   ```

---

## 📈 Performance Monitoring

### Check Redis Memory

```powershell
docker-compose exec redis redis-cli INFO memory
```

Look for:
- `used_memory_human`: Should be <100MB
- `used_memory_peak_human`: Should be <500MB

If too high:
```powershell
docker-compose exec redis redis-cli FLUSHDB
```

### Check Database Size

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import CheckResult, HeldSlot, MonitorTask
from django.utils import timezone
from datetime import timedelta

# Check old results
old_results = CheckResult.objects.filter(
    check_time__lt=timezone.now() - timedelta(days=7)
)
print(f"Old check results: {old_results.count()}")

# Check expired holds
expired_holds = HeldSlot.objects.filter(
    status='held',
    hold_started_at__lt=timezone.now() - timedelta(hours=24)
)
print(f"Expired holds: {expired_holds.count()}")

exit()
```

### Check Worker Memory

```powershell
docker stats worker_vatican --no-stream
```

Look for:
- `MEM USAGE`: Should be <500MB
- `MEM %`: Should be <10%

If too high, restart:
```powershell
docker-compose restart worker_vatican
```

---

## 🛠️ Common Tasks

### Restart Services

```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart worker_vatican
```

### View Recent Bookings

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import HeldSlot
from django.utils import timezone
from datetime import timedelta

# Bookings in last 24 hours
recent = HeldSlot.objects.filter(
    status='paid',
    hold_started_at__gte=timezone.now() - timedelta(hours=24)
).order_by('-hold_started_at')

print(f"✅ Recent bookings: {recent.count()}")
for slot in recent[:10]:
    print(f"   {slot.date} {slot.slot_time} - {slot.visitors}v - {slot.task.external_reference}")

exit()
```

### Update Google Sheets URL

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Agency

agency = Agency.objects.first()
agency.google_sheet_url = "https://docs.google.com/spreadsheets/d/NEW_SHEET_ID/edit"
agency.save()
print("✅ Google Sheet URL updated")

exit()
```

### Manually Create Task

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Agency, MonitorTask

agency = Agency.objects.first()

task = MonitorTask.objects.create(
    agency=agency,
    site='vatican',
    area_name='Vatican Museums',
    dates=['28/03/2026'],
    preferred_times=['10:00', '14:00'],
    visitors=2,
    adult_count=2,
    child_count=0,
    ticket_type=0,  # 0=standard, 1=guided
    language=None,  # None for standard, 'ENG' for guided
    check_interval=60,
    tier='snipe',
    is_active=True,
    external_reference='MANUAL-001'
)

print(f"✅ Created task {task.id}")
exit()
```

---

## 🔧 Troubleshooting

### Issue: No Tasks Being Created

**Check Google Sheets sync:**
```powershell
docker-compose logs backend | Select-String "Syncing booking requests"
```

**Manually trigger sync:**
```powershell
docker-compose exec backend python manage.py shell
```
```python
from monitors.tasks_booking_sync import sync_booking_requests
result = sync_booking_requests()
print(result)
exit()
```

**Common causes:**
1. Sheet not shared with service account
2. Wrong sheet names
3. Status not "pending"
4. Missing required columns

### Issue: Extension Not Detecting Slots

**Check backend API:**
```powershell
# Test API endpoint
curl http://localhost:8000/api/v1/available-slots/
```

**Check extension settings:**
1. Click extension icon
2. Click "Settings"
3. Verify backend URL
4. Verify Backend Listener Mode is ON

**Check extension logs:**
1. Right-click extension icon
2. Click "Inspect popup"
3. Check Console for errors

### Issue: Worker Not Monitoring

**Check worker logs:**
```powershell
docker-compose logs worker_vatican | Select-String "Monitoring"
```

**Restart worker:**
```powershell
docker-compose restart worker_vatican
```

**Check Celery Beat:**
```powershell
docker-compose logs backend | Select-String "vatican-monitor-orchestrator"
```

### Issue: High Memory Usage

**Check Redis:**
```powershell
docker-compose exec redis redis-cli INFO memory
```

**Clear Redis cache:**
```powershell
docker-compose exec redis redis-cli FLUSHDB
```

**Restart services:**
```powershell
docker-compose restart backend worker_vatican
```

---

## 📅 Weekly Maintenance

### Sunday Night (10 minutes)

1. **Clean old data:**
```powershell
docker-compose exec backend python manage.py shell
```
```python
from monitors.models import CheckResult, HeldSlot
from django.utils import timezone
from datetime import timedelta

# Delete old check results (>7 days)
old_results = CheckResult.objects.filter(
    check_time__lt=timezone.now() - timedelta(days=7)
)
count = old_results.count()
old_results.delete()
print(f"✅ Deleted {count} old check results")

# Delete expired holds (>24 hours)
expired = HeldSlot.objects.filter(
    status='held',
    hold_started_at__lt=timezone.now() - timedelta(hours=24)
)
count = expired.count()
expired.delete()
print(f"✅ Deleted {count} expired holds")

exit()
```

2. **Restart services:**
```powershell
docker-compose restart
```

3. **Check disk space:**
```powershell
docker system df
```

4. **Clean Docker:**
```powershell
docker system prune -f
```

---

## 📊 Monthly Reports

### Generate Booking Report

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import HeldSlot
from django.utils import timezone
from datetime import timedelta
from collections import Counter

# Last 30 days
start_date = timezone.now() - timedelta(days=30)
bookings = HeldSlot.objects.filter(
    status='paid',
    hold_started_at__gte=start_date
)

print(f"📊 Monthly Report")
print(f"=" * 50)
print(f"Total Bookings: {bookings.count()}")
print(f"Total Visitors: {sum(b.visitors for b in bookings)}")
print(f"Total Revenue: €{sum(b.total_price or 0 for b in bookings):.2f}")

# By date
dates = Counter([b.date for b in bookings])
print(f"\n📅 Bookings by Date:")
for date, count in sorted(dates.items()):
    print(f"   {date}: {count} bookings")

# By ticket type
types = Counter([b.task.ticket_type for b in bookings if b.task])
print(f"\n🎫 Bookings by Type:")
print(f"   Standard: {types.get(0, 0)}")
print(f"   Guided: {types.get(1, 0)}")

exit()
```

---

## 🎯 Quick Commands Reference

```powershell
# System Status
docker-compose ps

# View Logs
docker-compose logs -f backend
docker-compose logs -f worker_vatican

# Restart Services
docker-compose restart backend
docker-compose restart worker_vatican

# Manual Sync
docker-compose exec backend python manage.py shell
# Then: from monitors.tasks_booking_sync import sync_booking_requests; sync_booking_requests()

# Check Tasks
docker-compose exec backend python manage.py shell
# Then: from monitors.models import MonitorTask; print(MonitorTask.objects.filter(is_active=True).count())

# Clean Redis
docker-compose exec redis redis-cli FLUSHDB

# Database Shell
docker-compose exec backend python manage.py shell

# Django Admin
# Open browser: http://localhost:8000/admin/
```

---

**Daily Time Required**: 5-10 minutes  
**Weekly Time Required**: 10-15 minutes  
**Monthly Time Required**: 30 minutes  
**Automation Level**: 95%
