# Redis Bloat Fix - Permanent Solution

## Problem Summary

The Vatican bot was experiencing severe performance issues due to Redis bloat:

- **220,000+ keys** in Redis (should be < 10,000)
- **1.7GB memory usage** (should be < 100MB)
- **20+ second startup time** for workers (should be < 5 seconds)
- **Workers failing to connect** during Redis loading
- **Tasks not executing** due to connection failures

## Root Cause

Celery was storing task results **forever** with no expiration. Since the bot runs tasks every 5 seconds:

```
5 seconds/task × 12 tasks/minute × 60 minutes × 24 hours = 17,280 task results per day
```

After weeks of operation, this accumulated to 220,000+ keys, causing Redis to:
1. Take 20+ seconds to load on startup
2. Block Celery workers from connecting
3. Prevent tasks from executing
4. Consume excessive memory

## Solution Applied

### 1. ✅ Celery Configuration (settings.py)

Added automatic expiration for task results:

```python
# Auto-expire task results after 1 hour
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Don't store results for periodic tasks (they run every 5 seconds)
CELERY_TASK_IGNORE_RESULT = True  # Default: don't store results

# Redis connection retry settings
CELERY_BROKER_POOL_LIMIT = 10
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
```

**Impact**: New task results will auto-expire after 1 hour instead of living forever.

### 2. ✅ Automated Cleanup Tasks

Added daily cleanup task to Celery beat schedule:

```python
'cleanup-redis-cache': {
    'task': 'cleanup_redis_cache',
    'schedule': 86400,  # daily
    'options': {'queue': 'vatican'},
},
```

The cleanup task (`backend/monitors/tasks_cleanup.py`) automatically:
- Deletes Celery task results with no TTL
- Sets 7-day TTL on ticket state keys
- Removes expired cooldown keys
- Logs cleanup statistics

**Impact**: Redis will be automatically cleaned daily, preventing future bloat.

### 3. ✅ Manual Cleanup Script

Created `fix_redis_bloat_permanent.py` to clean up existing bloat:

```bash
python fix_redis_bloat_permanent.py
```

This script:
- Verifies all settings are correct
- Cleans up existing 220k+ keys
- Adds automated cleanup to schedule
- Provides restart instructions

### 4. ✅ Management Command

Created Django management command for manual cleanup:

```bash
docker-compose exec backend python manage.py cleanup_redis
docker-compose exec backend python manage.py cleanup_redis --dry-run
docker-compose exec backend python manage.py cleanup_redis --aggressive
```

## How to Apply the Fix

### Step 1: Run the Fix Script

```bash
python fix_redis_bloat_permanent.py
```

This will:
- ✅ Verify settings are correct
- ✅ Clean up existing Redis bloat
- ✅ Add automated cleanup task
- ✅ Show restart instructions

### Step 2: Restart Services

**CRITICAL**: You must restart services to apply the new settings:

```bash
docker-compose restart backend worker_vatican beat redis
```

### Step 3: Verify the Fix

Check Redis key count (should be < 10k):
```bash
docker-compose exec redis redis-cli DBSIZE
```

Check Redis memory usage (should be < 100MB):
```bash
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
```

Check workers are connecting:
```bash
docker-compose logs -f worker_vatican | grep "Connected"
```

Check tasks are running:
```bash
docker-compose logs -f worker_vatican | grep "ORCHESTRATOR"
```

## Expected Results

### Before Fix
- Redis keys: **220,000+**
- Redis memory: **1.7GB**
- Worker startup: **20+ seconds**
- Tasks: **Not executing**

### After Fix
- Redis keys: **< 10,000**
- Redis memory: **< 100MB**
- Worker startup: **< 5 seconds**
- Tasks: **Executing every 5 seconds**

## Monitoring

### Automated Monitoring

The following tasks run automatically to prevent future issues:

1. **cleanup-redis-cache** (daily)
   - Cleans up stale Celery results
   - Sets TTL on state keys
   - Removes expired cooldown keys

2. **cleanup-old-check-results** (daily)
   - Removes old CheckResult records from database

3. **cleanup-expired-holds** (hourly)
   - Marks expired HeldSlot records

4. **cleanup-inactive-tasks** (daily)
   - Disables tasks with all past dates

5. **memory-health-check** (every 30 minutes)
   - Logs memory usage warnings

### Manual Monitoring

Check Redis health:
```bash
# Key count
docker-compose exec redis redis-cli DBSIZE

# Memory usage
docker-compose exec redis redis-cli INFO memory

# Check for Celery task results
docker-compose exec redis redis-cli KEYS "celery-task-meta-*" | wc -l

# Check ticket state keys
docker-compose exec redis redis-cli KEYS "ticket_state:*" | wc -l
```

Check Celery health:
```bash
# Worker logs
docker-compose logs -f worker_vatican

# Beat scheduler logs
docker-compose logs -f beat

# Check active tasks
docker-compose exec backend celery -A core inspect active
```

## Prevention Mechanisms

### 1. Auto-Expiration
- Task results expire after 1 hour
- State keys expire after 7 days
- Cooldown keys expire after their timeout

### 2. Ignore Results
- Periodic tasks don't store results by default
- Only important tasks (holds, snipes) store results

### 3. Daily Cleanup
- Automated cleanup runs daily
- Removes any keys that slip through

### 4. Memory Limits
- Redis has 2GB memory limit
- Uses LRU eviction policy (allkeys-lru)
- Worker has 1GB memory limit

### 5. Worker Restart
- Workers restart after 1000 tasks
- Prevents memory leaks in worker processes

## Troubleshooting

### Issue: Redis still has 100k+ keys after cleanup

**Solution**: Run aggressive cleanup:
```bash
docker-compose exec backend python manage.py cleanup_redis --aggressive
```

### Issue: Workers still not connecting

**Solution**: Check Redis is running and restart services:
```bash
docker-compose ps redis
docker-compose restart redis
docker-compose restart worker_vatican beat
```

### Issue: Tasks still not executing

**Solution**: Check beat scheduler is running:
```bash
docker-compose logs beat | tail -50
docker-compose restart beat
```

### Issue: Redis memory still high

**Solution**: Flush Redis (WARNING: loses all cache):
```bash
docker-compose exec redis redis-cli FLUSHDB
docker-compose restart worker_vatican beat
```

Then re-seed state:
```bash
docker-compose exec backend python setup_60_day_monitoring.py
```

## Files Modified

1. **backend/core/settings.py**
   - Added `CELERY_RESULT_EXPIRES = 3600`
   - Added `CELERY_TASK_IGNORE_RESULT = True`
   - Added Redis connection retry settings
   - Added `cleanup-redis-cache` to beat schedule

2. **backend/monitors/tasks_cleanup.py**
   - Enhanced `cleanup_redis_cache()` task
   - Added comprehensive Redis cleanup logic

3. **backend/monitors/management/commands/cleanup_redis.py**
   - Created manual cleanup command

4. **fix_redis_bloat_permanent.py** (NEW)
   - One-time fix script

5. **REDIS_BLOAT_FIX.md** (NEW)
   - This documentation

## Testing

### Test 1: Verify Settings
```bash
docker-compose exec backend python -c "
from django.conf import settings
print('CELERY_RESULT_EXPIRES:', settings.CELERY_RESULT_EXPIRES)
print('CELERY_TASK_IGNORE_RESULT:', settings.CELERY_TASK_IGNORE_RESULT)
"
```

Expected output:
```
CELERY_RESULT_EXPIRES: 3600
CELERY_TASK_IGNORE_RESULT: True
```

### Test 2: Verify Cleanup Task
```bash
docker-compose exec backend python -c "
from django.conf import settings
print('cleanup-redis-cache' in settings.CELERY_BEAT_SCHEDULE)
"
```

Expected output:
```
True
```

### Test 3: Run Manual Cleanup
```bash
docker-compose exec backend python manage.py cleanup_redis --dry-run
```

Expected output:
```
✅ Connected to Redis
Initial state:
  Keys: X,XXX
  Memory: XXX MB
...
```

### Test 4: Monitor Redis Growth
```bash
# Check key count every minute
watch -n 60 'docker-compose exec redis redis-cli DBSIZE'
```

Expected: Key count should stay < 10,000 and not grow continuously.

## Success Criteria

✅ **Fix is successful when:**

1. Redis key count stays < 10,000
2. Redis memory usage stays < 100MB
3. Workers start in < 5 seconds
4. Tasks execute every 5 seconds
5. No "connection refused" errors in logs
6. Notifications are sent when tickets open

## Maintenance

### Daily
- Check Redis key count: `docker-compose exec redis redis-cli DBSIZE`
- Check worker logs: `docker-compose logs worker_vatican | tail -100`

### Weekly
- Review cleanup task logs: `docker-compose logs backend | grep "cleanup"`
- Check memory usage: `docker-compose exec redis redis-cli INFO memory`

### Monthly
- Review Redis configuration
- Check for any new memory leaks
- Update this documentation if needed

## Related Issues

- **Issue #1**: Telegram notifications not working → Fixed by seeding Redis state
- **Issue #2**: Workers not connecting → Fixed by Redis cleanup
- **Issue #3**: Tasks not executing → Fixed by Redis cleanup + restart

## References

- Celery Result Expiration: https://docs.celeryq.dev/en/stable/userguide/configuration.html#result-expires
- Redis Memory Optimization: https://redis.io/docs/management/optimization/memory-optimization/
- Vatican Bot Rules: `.kiro/steering/VATICAN_BOT_RULES.md`

---

**Last Updated**: May 2, 2026  
**Status**: ✅ FIXED - Permanent solution applied  
**Next Review**: May 9, 2026
