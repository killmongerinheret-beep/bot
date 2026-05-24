# Quick Fix for Redis Bloat - 3 Steps

## Problem
Vatican bot not working because Redis has 220k+ keys and takes 20+ seconds to load.

## Solution (3 Steps)

### Step 1: Run Fix Script
```bash
python fix_redis_bloat_permanent.py
```

**What it does:**
- ✅ Cleans up 220k+ keys in Redis
- ✅ Adds automated daily cleanup
- ✅ Verifies all settings are correct

**Expected output:**
```
✅ Connected to Redis
✅ Deleted 200,000+ Celery task results
✅ Set TTL on ticket state keys
✅ Deleted old cooldown keys
Redis keys: 5,000 (was 220,000)
```

---

### Step 2: Restart Services
```bash
docker-compose restart backend worker_vatican beat redis
```

**Why:** New settings only apply after restart.

**Expected:** Services restart in < 30 seconds.

---

### Step 3: Verify Fix
```bash
# Check Redis key count (should be < 10k)
docker-compose exec redis redis-cli DBSIZE

# Check workers are running
docker-compose logs -f worker_vatican | grep "ORCHESTRATOR"
```

**Expected output:**
```
(integer) 5432  # < 10,000 ✅

🎯 ORCHESTRATOR: Starting Vatican task orchestration
✅ Dispatched: 04/05/2026 | Palazzo Papale | 3 agencies
```

---

## Done! 🎉

Your bot should now:
- ✅ Start in < 5 seconds (was 20+ seconds)
- ✅ Execute tasks every 5 seconds
- ✅ Send Telegram notifications
- ✅ Auto-cleanup Redis daily

---

## If Still Not Working

### Check 1: Redis is clean
```bash
docker-compose exec redis redis-cli DBSIZE
```
Should be < 10,000. If not, run:
```bash
docker-compose exec backend python manage.py cleanup_redis --aggressive
docker-compose restart redis worker_vatican beat
```

### Check 2: Workers are connected
```bash
docker-compose logs worker_vatican | tail -50
```
Should see "Connected to broker" and "ORCHESTRATOR" messages.

### Check 3: Tasks are scheduled
```bash
docker-compose logs beat | tail -50
```
Should see "Scheduler: Sending due task" every 5 seconds.

---

## Monitoring

Check Redis health anytime:
```bash
# Key count
docker-compose exec redis redis-cli DBSIZE

# Memory usage
docker-compose exec redis redis-cli INFO memory | grep used_memory_human

# Worker status
docker-compose logs worker_vatican | tail -20
```

---

## Prevention

The fix includes **automated daily cleanup** that runs at midnight:
- Deletes old Celery task results
- Sets TTL on state keys
- Removes expired cooldown keys

**You don't need to do anything** - it's automatic! 🚀

---

## Full Documentation

See `REDIS_BLOAT_FIX.md` for complete details.
