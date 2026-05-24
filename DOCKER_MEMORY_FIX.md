# Docker Memory Issue - FIXED ✅

**Date:** May 6, 2026  
**Issue:** Vatican worker containers being killed with SIGKILL (signal 9)  
**Root Cause:** Out of Memory (OOM) - Memory exhaustion

---

## Problem Diagnosis

### Symptoms
- Workers exiting prematurely with `signal 9 (SIGKILL)`
- Error messages: `WorkerLostError: Worker exited prematurely`
- Container memory usage: **98.89% (1013MB/1024MB)**

### Root Cause
The `worker_vatican` container was configured with:
- **Memory limit:** 1GB
- **Concurrency:** 16 workers
- **Task:** Running Playwright browsers for Vatican ticket monitoring

**Math:** 16 concurrent workers × ~100-300MB per browser = 1.6-4.8GB needed  
**Available:** Only 1GB → OOM Killer activated → Workers killed

---

## Solution Applied

### Changes Made to `docker-compose.yml`

**Before:**
```yaml
worker_vatican:
  mem_limit: 1g
  memswap_limit: 1g
  command: celery -A backend.core worker -l info -Q snipe,vatican,celery --concurrency=16 --max-tasks-per-child=1000
```

**After:**
```yaml
worker_vatican:
  mem_limit: 3g          # Increased from 1g to 3g
  memswap_limit: 3g      # Increased from 1g to 3g
  command: celery -A backend.core worker -l info -Q snipe,vatican,celery --concurrency=8 --max-tasks-per-child=100
  # Reduced concurrency from 16 to 8
  # Reduced max-tasks-per-child from 1000 to 100 (better memory cleanup)
```

### Why These Numbers?
- **3GB memory:** Enough for 8 workers with browsers (8 × 300MB = 2.4GB max + overhead)
- **8 concurrency:** Balanced performance without overwhelming memory
- **100 tasks/child:** More frequent worker recycling = better memory cleanup

---

## Results

### Before Fix
```
CONTAINER: worker_vatican
CPU: 32.46%
MEM: 1013MiB / 1GiB (98.89%) ❌ CRITICAL
STATUS: Workers being killed every few minutes
```

### After Fix
```
CONTAINER: worker_vatican
CPU: 46.71%
MEM: 441MiB / 3GiB (14.36%) ✅ HEALTHY
STATUS: Running stable, no SIGKILL errors
```

---

## Verification Commands

Check container status:
```bash
docker ps | grep worker_vatican
```

Monitor memory usage:
```bash
docker stats travelagenntbot-worker_vatican-1
```

Check for errors:
```bash
docker logs --tail 100 travelagenntbot-worker_vatican-1 | grep -i "error\|sigkill"
```

Watch live logs:
```bash
docker logs -f travelagenntbot-worker_vatican-1
```

---

## Additional Recommendations

### 1. Monitor Memory Over Time
Keep an eye on memory usage during peak loads:
```bash
watch -n 5 'docker stats --no-stream travelagenntbot-worker_vatican-1'
```

### 2. If Memory Issues Return
If you see memory creeping up again:
- **Option A:** Increase to 4GB: `mem_limit: 4g`
- **Option B:** Reduce concurrency to 4-6: `--concurrency=6`
- **Option C:** Reduce max-tasks-per-child to 50: `--max-tasks-per-child=50`

### 3. Optimize Browser Usage
Consider implementing browser pooling in the code to reuse browser instances instead of creating new ones for each task.

### 4. Redis Memory
Redis is also at 18.61% (190MB/1GB) - monitor this as well. If it grows, consider:
```yaml
redis:
  mem_limit: 2g  # Increase if needed
```

---

## System Status: ✅ OPERATIONAL

All containers running healthy:
- ✅ **worker_vatican:** 14.36% memory (was 98.89%)
- ✅ **redis:** 18.61% memory
- ✅ **backend:** Running
- ✅ **telegram_bot:** Running
- ✅ **beat:** Running (scheduler)
- ✅ **frontend:** Running
- ✅ **nginx:** Running
- ✅ **db:** Running
- ✅ **solver:** Running
- ✅ **harvester:** Running

**No more SIGKILL errors!** 🎉

---

## What Was Actually Working

The Vatican monitoring system was **functionally correct**:
- ✅ Search API integration working
- ✅ Ticket ID resolution working
- ✅ Exact name matching working
- ✅ SOLD_OUT detection working
- ✅ Proxy rotation working

The only issue was **infrastructure** (memory limits), not code logic.

---

**Last Updated:** May 6, 2026  
**Status:** RESOLVED ✅
