# Cleanup Features Added ✅

**Date:** March 4, 2026  
**Time:** 16:19 CET  
**Status:** ✅ **COMPLETED**

---

## Summary

Added two new automated cleanup features to prevent queue backups and automatically remove expired tasks/times:

1. ✅ **Automatic Queue Cleanup** - Purges backed-up Celery queues every hour
2. ✅ **Smart Time-Based Cleanup** - Removes past times and dates from monitor tasks every 30 minutes

---

## Feature 1: Automatic Queue Cleanup

### Purpose
Prevents Celery queues from backing up with duplicate or stale tasks, which can cause:
- Worker slowdown
- Memory issues
- Task execution delays

### Implementation

**File:** `backend/monitors/tasks.py`

**New Task:** `cleanup_backed_up_queues()`

```python
@shared_task(name="cleanup_backed_up_queues")
def cleanup_backed_up_queues():
    """
    Periodically checks and cleans backed-up Celery queues.
    Runs every hour to prevent queue overflow.
    
    Monitors:
    - vatican queue (threshold: 100 tasks)
    - colosseum queue (threshold: 50 tasks)
    - celery queue (threshold: 200 tasks)
    
    If queue exceeds threshold, purges old tasks.
    """
```

### Queue Thresholds

| Queue | Threshold | Purpose |
|-------|-----------|---------|
| vatican | 100 tasks | Vatican ticket monitoring |
| colosseum | 50 tasks | Colosseum ticket monitoring |
| celery | 200 tasks | General Celery tasks |

### Schedule
- **Frequency:** Every 1 hour
- **Method:** Periodic task via django_celery_beat

### Test Results

**Before cleanup:**
```
⚠️ Queue 'vatican' backed up: 307 tasks (threshold: 100)
⚠️ Queue 'colosseum' backed up: 200 tasks (threshold: 50)
⚠️ Queue 'celery' backed up: 382 tasks (threshold: 200)
```

**After cleanup:**
```
✅ Queue 'vatican' healthy: 0 tasks
✅ Queue 'colosseum' healthy: 0 tasks
✅ Queue 'celery' healthy: 29 tasks
```

**Result:** Cleaned 889 backed-up tasks!

---

## Feature 2: Smart Time-Based Cleanup

### Purpose
Automatically removes:
- Past dates from monitor tasks
- Past times from today's tasks
- Tasks with no future dates/times

This ensures:
- No wasted checks on expired times
- Automatic task cleanup
- Better resource utilization

### Implementation

**File:** `backend/monitors/tasks.py`

**Enhanced Task:** `cleanup_expired_monitor_tasks()`

```python
@shared_task(name="cleanup_expired_monitor_tasks")
def cleanup_expired_monitor_tasks():
    """
    ✅ ENHANCED: Removes dates/times from the past.
    - Removes past dates entirely
    - For today's date, removes times that have already passed
    - If a task has no future dates/times, it is deleted
    """
```

### Features

#### 1. Past Date Removal
Removes dates that are before today:
```python
if dt < now_date:
    # Remove this date
    changed = True
```

#### 2. Past Time Removal (NEW!)
For today's date, removes times that have already passed:
```python
if dt == now_date:
    # Check preferred times
    for time_str in task.preferred_times:
        task_time = parse_time(time_str)
        
        # Add 30-minute buffer
        if task_time > (now_time - 30 minutes):
            keep_time()
        else:
            remove_time()
```

**30-Minute Buffer:** Times are kept if they're within 30 minutes of current time to avoid race conditions.

#### 3. Task Deletion
If a task has no future dates/times after cleanup:
```python
if not new_dates:
    task.delete()
    logger.info(f"🗑️ Task #{task.id} has no future dates/times. Deleting.")
```

### Schedule
- **Frequency:** Every 30 minutes
- **Method:** Periodic task via django_celery_beat

### Test Results

**Task #32 (March 4, 2026):**
- Original times: 09:00, 10:00, 11:00, 14:00, 15:00, 16:00
- Current time: 16:18
- **Removed:** 09:00, 10:00, 11:00, 14:00, 15:00 (5 times)
- **Kept:** 16:00 (within 30-min buffer)

**Log Output:**
```
[INFO] ⏰ Removed past time 09:00 from Task #32
[INFO] ⏰ Removed past time 10:00 from Task #32
[INFO] ⏰ Removed past time 11:00 from Task #32
[INFO] ⏰ Removed past time 14:00 from Task #32
[INFO] ⏰ Removed past time 15:00 from Task #32
[INFO] 🧹 Cleanup: Updated 2 tasks, Deleted 0 tasks, Removed 5 past times
```

---

## Periodic Task Configuration

### All Periodic Tasks

| Task Name | Frequency | Purpose |
|-----------|-----------|---------|
| Orchestrate All Monitors | Every 10 seconds | Main monitoring loop |
| Cleanup Expired Monitor Tasks | Every 30 minutes | Remove past dates/times |
| Cleanup Backed-Up Queues | Every 1 hour | Purge backed-up queues |
| Cleanup Old Results | Daily at 3 AM | Remove old check results |
| Refresh Vatican Session | Every 30 minutes | Keep Vatican cookies fresh |
| Refresh Colosseum Session | Every 30 minutes | Keep Colosseum cookies fresh |

### Setup Script

Created `setup_cleanup_tasks.py` to configure periodic tasks:

```bash
docker cp setup_cleanup_tasks.py travelagenntbot-backend-1:/app/
docker-compose exec backend python /app/setup_cleanup_tasks.py
```

---

## Benefits

### 1. Prevents Queue Overflow ✅
- Automatic detection of backed-up queues
- Purges old tasks before they cause issues
- Keeps workers responsive

### 2. Automatic Task Cleanup ✅
- No manual intervention needed
- Tasks auto-delete when expired
- Saves database space

### 3. Smart Time Management ✅
- Only checks future times
- Removes past times automatically
- 30-minute buffer prevents race conditions

### 4. Resource Optimization ✅
- Reduces unnecessary checks
- Frees up worker capacity
- Improves system performance

---

## Usage Examples

### Manual Queue Cleanup

```bash
# Check queue status
docker-compose exec -T redis redis-cli LLEN vatican
docker-compose exec -T redis redis-cli LLEN colosseum
docker-compose exec -T redis redis-cli LLEN celery

# Run cleanup manually
docker-compose exec backend python /app/test_cleanup_tasks.py
```

### Manual Task Cleanup

```bash
# Run cleanup manually
docker-compose exec backend python -c "
import os, sys, django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from monitors.tasks import cleanup_expired_monitor_tasks
print(cleanup_expired_monitor_tasks())
"
```

### Check Periodic Task Status

```bash
docker-compose exec backend python /app/setup_cleanup_tasks.py
```

---

## Monitoring

### Queue Health Check

```bash
# Check all queue lengths
docker-compose exec -T redis redis-cli LLEN vatican
docker-compose exec -T redis redis-cli LLEN colosseum
docker-compose exec -T redis redis-cli LLEN celery
```

**Healthy Status:**
- vatican: < 100 tasks
- colosseum: < 50 tasks
- celery: < 200 tasks

### Task Cleanup Logs

```bash
# Watch cleanup logs
docker-compose logs -f worker_vatican | grep "🧹\|⏰\|🗑️"
```

**Expected Output:**
```
[INFO] ⏰ Removed past time 09:00 from Task #32
[INFO] 🧹 Cleanup: Updated 2 tasks, Deleted 0 tasks, Removed 5 past times
[INFO] 🗑️ Task #45 has no future dates/times. Deleting.
```

---

## Configuration

### Adjust Queue Thresholds

Edit `backend/monitors/tasks.py`:

```python
queue_thresholds = {
    'vatican': 100,      # Increase if needed
    'colosseum': 50,     # Increase if needed
    'celery': 200        # Increase if needed
}
```

### Adjust Time Buffer

Edit `backend/monitors/tasks.py`:

```python
# Current: 30 minutes
buffer_time = (datetime.combine(now_date, now_time) - td(minutes=30)).time()

# Change to 60 minutes:
buffer_time = (datetime.combine(now_date, now_time) - td(minutes=60)).time()
```

### Change Cleanup Frequency

```bash
# Edit periodic task schedule
docker-compose exec backend python /app/setup_cleanup_tasks.py

# Or manually via Django admin:
# http://localhost:8000/admin/django_celery_beat/periodictask/
```

---

## Troubleshooting

### Queue Still Backing Up

**Symptom:** Queue length keeps growing despite cleanup

**Possible Causes:**
1. Workers not processing tasks fast enough
2. Too many tasks being queued
3. Tasks taking too long to execute

**Solutions:**
```bash
# 1. Check worker status
docker-compose ps worker_vatican

# 2. Check worker logs for errors
docker-compose logs worker_vatican --tail=100

# 3. Increase worker concurrency
# Edit docker-compose.yml:
# command: celery -A core worker --loglevel=info --concurrency=4

# 4. Lower queue threshold
# Edit tasks.py queue_thresholds
```

### Tasks Not Being Cleaned Up

**Symptom:** Old tasks still in database

**Possible Causes:**
1. Periodic task not running
2. Date format issues
3. Timezone issues

**Solutions:**
```bash
# 1. Check periodic task status
docker-compose exec backend python /app/setup_cleanup_tasks.py

# 2. Run cleanup manually
docker-compose exec backend python /app/test_cleanup_tasks.py

# 3. Check beat logs
docker-compose logs beat --tail=50
```

---

## Summary

**Added Features:**
1. ✅ Automatic queue cleanup (every hour)
2. ✅ Smart time-based task cleanup (every 30 minutes)
3. ✅ Periodic task configuration
4. ✅ Test scripts for validation

**Results:**
- Cleaned 889 backed-up tasks
- Removed 5 past times from tasks
- All queues now healthy
- System running smoothly

**Status:** ✅ **FULLY OPERATIONAL**

---

**Implemented by:** Kiro AI  
**Date:** March 4, 2026 16:19 CET  
**Services restarted:** worker_vatican, beat

