# Achieving 90+ Health Score

**Current:** 75/100 (GOOD)  
**Target:** 90/100 (EXCELLENT)  
**Status:** ⏳ In Progress

---

## How to Reach 90/100 Health

### Current Score Breakdown

**Starting Score:** 100 points

**Deductions:**
- -10 points: 6 tasks without ticket_id
- -15 points: 1 task never checked (Task #26)
- -0 points: 0 tasks in error
- -0 points: Queues healthy
- -0 points: No stale tasks
- -0 points: All proxies available

**Current Total:** 75/100

---

## Two Options to Reach 90+

### Option 1: Wait for Automatic Resolution (RECOMMENDED) ⏳

**What happens:**
- Task #26 is currently being resolved
- Once it completes its first check: never_checked = 0
- Score: 100 - 10 (tasks without ID) = **90/100**

**Time:** 1-2 minutes  
**Action:** None (automatic)

**Status:** ✅ Task #26 queued for resolution

---

### Option 2: Force Resolve All Tasks (For 100/100) 🚀

**What happens:**
- Force resolve ticket_id for all 6 tasks
- All tasks will have ticket_id
- Score: 100 - 0 = **100/100**

**Time:** 5-10 minutes  
**Action:** Run force_100_health.py

**Status:** ✅ All 6 tasks queued for resolution

---

## What Was Done

### ✅ Executed: Force 100/100 Health

Ran `force_100_health.py` which:

1. Found 6 tasks without ticket_id:
   - Task #28 (April 4, 2026)
   - Task #26 (March 23, 2026)
   - Task #24 (April 22, 2026)
   - Task #29 (May 26, 2026)
   - Task #21 (March 16, 2026)
   - Task #22 (March 26, 2026)

2. Cleared any stuck resolution locks

3. Queued all 6 tasks for immediate resolution:
   ```python
   resolve_and_check_task.apply_async(args=[task_id], queue='vatican', countdown=2)
   ```

4. Tasks will resolve in sequence over 5-10 minutes

---

## Expected Timeline

### Immediate (Now)
- ✅ 6 tasks queued for resolution
- ⏳ Workers processing tasks

### 2 Minutes
- ✅ Task #26 completes first check
- 📊 Health: 90/100 (EXCELLENT)

### 5-10 Minutes
- ✅ All 6 tasks resolve ticket_id
- ✅ All tasks checked at least once
- 📊 Health: 100/100 (PERFECT)

---

## Monitoring Progress

### Watch Resolution Logs:
```bash
docker-compose logs -f worker_vatican | grep "RESOLVING\|Resolved and saved"
```

**Expected output:**
```
🔍 RESOLVING ticket_id for Task #28...
✅ Resolved and saved ticket_id 2129030053 for Task #28
🔍 RESOLVING ticket_id for Task #26...
✅ Resolved and saved ticket_id 327712780 for Task #26
...
```

### Check Health Score:
```bash
docker-compose exec backend python /app/comprehensive_system_check.py
```

### Quick Status Check:
```bash
docker-compose exec backend python /app/achieve_90_health.py
```

---

## Health Score Progression

| Time | Tasks Resolved | Never Checked | Health Score | Status |
|------|----------------|---------------|--------------|--------|
| Start | 0/6 | 1 | 75/100 | GOOD |
| +2 min | 1/6 | 0 | 90/100 | EXCELLENT ✅ |
| +5 min | 3/6 | 0 | 90/100 | EXCELLENT |
| +10 min | 6/6 | 0 | 100/100 | PERFECT ✅ |

---

## What Happens During Resolution

For each task:

1. **Navigate to Vatican Website**
   - Opens deep link with correct date/visitors
   - Extracts JSESSIONID cookies

2. **Extract Dynamic Ticket IDs**
   - Finds all available tickets on page
   - Extracts IDs from `data-cy="bookTicket_{ID}"` attributes

3. **Match by Name**
   - Uses 3-tier matching strategy:
     - Exact substring match
     - Keyword scoring
     - Fallback to first standard ticket

4. **Save ticket_id**
   - Stores in database
   - Task now has permanent ticket_id

5. **Check Availability**
   - Calls Vatican API with fresh ticket_id
   - Gets available time slots
   - Updates task status

**Time per task:** ~30-60 seconds

---

## Verification Commands

### Check if Task #26 is resolved:
```bash
docker-compose exec backend python -c "
import os, sys, django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from monitors.models import MonitorTask
task = MonitorTask.objects.get(id=26)
print(f'Task #26:')
print(f'  ticket_id: {task.ticket_id}')
print(f'  last_checked: {task.last_checked}')
print(f'  status: {task.last_status}')
"
```

### Count tasks without ticket_id:
```bash
docker-compose exec backend python -c "
import os, sys, django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from monitors.models import MonitorTask
count = MonitorTask.objects.filter(is_active=True, ticket_id__isnull=True).count()
print(f'Tasks without ticket_id: {count}')
"
```

---

## Troubleshooting

### If resolution is slow:

**Check worker status:**
```bash
docker-compose ps worker_vatican
```

**Check for errors:**
```bash
docker-compose logs worker_vatican --tail=50 | grep "ERROR\|CRITICAL"
```

**Check queue length:**
```bash
docker-compose exec -T redis redis-cli LLEN vatican
```

### If tasks fail to resolve:

**Possible causes:**
1. Vatican website temporarily down
2. Proxy issues
3. Page structure changed

**Solution:**
- Wait and retry automatically
- System will retry on next orchestration cycle
- Check logs for specific error messages

---

## Success Criteria

### 90/100 Health (EXCELLENT):
- ✅ Task #26 checked at least once
- ✅ 0 tasks never checked
- ⚠️ 6 tasks still without ticket_id (acceptable)

### 100/100 Health (PERFECT):
- ✅ All tasks checked at least once
- ✅ All tasks have ticket_id
- ✅ No errors
- ✅ All queues healthy

---

## Current Status

**Action Taken:** ✅ Queued all 6 tasks for resolution

**ETA to 90/100:** 2 minutes  
**ETA to 100/100:** 5-10 minutes

**Next Steps:**
1. Wait 2 minutes
2. Run health check
3. Verify 90+ score
4. Wait 10 minutes total
5. Verify 100 score

---

## Commands Summary

**Force 100/100 health:**
```bash
docker-compose exec backend python /app/force_100_health.py
```

**Check progress:**
```bash
docker-compose logs -f worker_vatican | grep "RESOLVING\|Resolved"
```

**Check health:**
```bash
docker-compose exec backend python /app/comprehensive_system_check.py
```

**Quick status:**
```bash
docker-compose exec backend python /app/achieve_90_health.py
```

---

**Started:** March 4, 2026 16:44 CET  
**Expected 90/100:** 16:46 CET  
**Expected 100/100:** 16:54 CET

