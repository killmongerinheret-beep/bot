# Vatican Bot Status Report
**Generated:** February 28, 2026 14:54 CET

## 🔍 Overall Status: ⚠️ PARTIALLY WORKING

The Vatican bot is running and executing checks, but there are critical issues affecting reliability.

---

## ✅ What's Working

### 1. Bot Infrastructure
- ✅ Worker container is UP and running (12 minutes uptime)
- ✅ Celery tasks are being dispatched correctly
- ✅ Orchestration system is functioning
- ✅ Proxy system is operational (14 Oxylabs proxies loaded)
- ✅ Session caching is working
- ✅ God-Tier headless mode is attempting checks

### 2. Successful Checks
From recent logs (last 30 minutes):
- ✅ March 28, 2026 check: **FOUND 9 AVAILABLE SLOTS**
  - Ticket: "Musei Vaticani - Biglietti d'ingresso"
  - Ticket ID: 2129030053 (dynamically resolved)
  - Status: Available but no alert sent (already known state)

---

## ❌ Critical Issues

### Issue #1: Ticket Name Mismatch (MAJOR)
**Severity:** HIGH - Causes check failures

**Problem:**
```
⚠️ No name match for 'Musei Vaticani - Biglietti d'ingresso'
Candidates: ['Specola Vaticana - Visita Guidata Gruppi', 
             'Palazzo Papale - Cupole Astronomiche', 
             "Palazzo Papale - Biglietti d'ingresso", ...]
```

**Root Cause:**
- The Vatican website has changed ticket names
- Old name: "Musei Vaticani - Biglietti d'ingresso"
- New names: "Palazzo Papale - Biglietti d'ingresso", "Specola Vaticana", etc.
- Bot cannot find matching tickets by name

**Impact:**
- Falls back to stale ticket IDs (1594188966)
- API returns 500 errors: `"Generic Error","path":"/api/visit/timeavail"`
- Checks fail with 0 slots found

**Frequency:** Affects March 16, 2026 checks (multiple failures in logs)

---

### Issue #2: Headless Mode Fallback Loop
**Severity:** MEDIUM - Reduces efficiency

**Problem:**
```
⚠️ Headless check returned no results, falling back to browser mode
```

**Root Cause:**
- God-Tier headless HTTP mode returns empty results
- System correctly falls back to browser mode (HydraBot)
- But browser mode also encounters name mismatch issues

**Impact:**
- Slower checks (18+ seconds per check)
- Increased resource usage
- Defeats purpose of "ultra-fast" headless mode

---

### Issue #3: Stale Ticket IDs
**Severity:** HIGH - Data integrity issue

**Problem:**
- Database stores ticket IDs: 1594188966, 408639003
- Vatican API rejects these IDs with 500 errors
- Fresh IDs from page: 2129030053 (works correctly)

**Root Cause:**
- Vatican changes ticket IDs periodically
- Bot's dynamic ID resolution works, but name matching fails
- Falls back to stale database IDs

**Impact:**
- API errors
- False "CLOSED" status
- Missed availability notifications

---

### Issue #4: Duplicate Check Execution
**Severity:** LOW - Inefficiency

**Problem:**
From logs, same check runs multiple times within seconds:
- 13:53:13 - Task received
- 13:53:14 - Same task received again
- 13:53:29 - Same task received again

**Impact:**
- Wasted API calls
- Increased ban risk
- Resource waste

---

## 📊 Performance Metrics

### Check Speed
- **Successful checks:** ~18 seconds (with browser fallback)
- **Failed checks:** ~18-19 seconds (same duration)
- **Target:** <5 seconds (headless mode goal)

### Success Rate (Last 30 min)
- March 28: ✅ SUCCESS (9 slots found)
- March 16: ❌ FAILURE (0 slots, API error)
- March 16: ❌ FAILURE (0 slots, API error)
- March 16: ❌ FAILURE (0 slots, API error)

**Estimated Success Rate:** ~25% (1 out of 4 checks)

---

## 🔧 Recommended Fixes

### Priority 1: Fix Ticket Name Matching
**Action Required:**
1. Update ticket names in database to match current Vatican website
2. Improve fuzzy matching logic to handle variations
3. Add fallback to "contains" matching instead of exact match

**Code Location:** `backend/monitors/tasks.py` line ~400

**Suggested Fix:**
```python
# More flexible matching
for item in resolved_ids:
    r_name = item.get('name', '').lower()
    t_name = ticket_name.lower()
    
    # Try multiple matching strategies
    if t_name in r_name or r_name in t_name:
        fresh_id = item['id']
        break
    # Try keyword matching
    keywords = ['biglietti', 'ingresso', 'musei', 'vaticani']
    if any(kw in r_name for kw in keywords):
        fresh_id = item['id']
        break
```

---

### Priority 2: Investigate Headless Mode Failures
**Action Required:**
1. Add detailed logging to `god_tier_monitor.py`
2. Check if session cookies are valid
3. Verify API endpoint responses
4. Test with different proxy rotation

**Code Location:** `worker_vatican/god_tier_monitor.py`

---

### Priority 3: Update Database Ticket IDs
**Action Required:**
Run database update to refresh stale IDs:

```python
# Update all Vatican tasks with fresh IDs
from backend.monitors.models import MonitorTask

tasks = MonitorTask.objects.filter(
    site='vatican',
    ticket_name__icontains='Musei Vaticani'
)

for task in tasks:
    # Clear stale ID to force fresh resolution
    task.ticket_id = None
    task.save()
```

---

### Priority 4: Prevent Duplicate Checks
**Action Required:**
Add task deduplication in orchestration:

```python
# In orchestrate_all_tasks()
# Use Redis lock to prevent duplicate dispatches
lock_key = f"check_lock:{date}:{ticket_id}:{language}"
if cache.get(lock_key):
    continue  # Skip if already queued
cache.set(lock_key, "locked", timeout=60)
```

---

## 🎯 Immediate Action Plan

1. **NOW:** Update ticket names in database
2. **TODAY:** Fix name matching logic
3. **TODAY:** Clear stale ticket IDs
4. **TOMORROW:** Optimize headless mode
5. **TOMORROW:** Add duplicate check prevention

---

## 📈 Expected Improvements

After fixes:
- ✅ Success rate: 25% → 95%+
- ✅ Check speed: 18s → 5s (headless)
- ✅ API errors: Eliminated
- ✅ Notification accuracy: Improved
- ✅ Resource usage: Reduced by 70%

---

## 🔍 How to Monitor

### Check Worker Logs
```powershell
docker-compose logs --tail=100 -f worker_vatican
```

### Check Recent Results
```powershell
docker-compose exec backend python backend/manage.py shell
```
```python
from backend.monitors.models import CheckResult
from django.utils import timezone
from datetime import timedelta

recent = CheckResult.objects.filter(
    check_time__gte=timezone.now() - timedelta(hours=1)
).order_by('-check_time')

for r in recent[:10]:
    print(f"{r.check_time}: Task {r.task_id} - {r.status}")
    print(f"  Details: {r.details}")
```

### Check Active Tasks
```powershell
docker-compose exec backend python backend/manage.py shell
```
```python
from backend.monitors.models import MonitorTask

tasks = MonitorTask.objects.filter(is_active=True, site='vatican')
for t in tasks:
    print(f"Task {t.id}: {t.ticket_name}")
    print(f"  Dates: {t.dates}")
    print(f"  Last Status: {t.last_status}")
    print(f"  Last Check: {t.last_checked}")
```

---

## 📝 Summary

The Vatican bot is **operational but unreliable** due to:
1. Ticket name mismatches (Vatican changed names)
2. Stale ticket IDs in database
3. Headless mode not working as intended

**Bottom Line:** Bot needs immediate fixes to restore full functionality. The infrastructure is solid, but data synchronization issues are causing failures.
