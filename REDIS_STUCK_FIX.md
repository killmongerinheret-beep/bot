# Redis Stuck Loading - Emergency Fix

## Problem

Redis is stuck loading the dataset in memory. This happens when Redis has too much data (220k+ keys) and takes too long to load on startup.

**Symptoms:**
- Commands hang/timeout
- "Redis is loading the dataset in memory" error
- Workers can't connect
- Bot not running

## Quick Fix (2 minutes)

### Option 1: Automated Script (Recommended)

```bash
fix_redis_now.bat
```

This will:
1. Stop Redis
2. Clear Redis data
3. Restart all services
4. Verify everything works

### Option 2: Manual Commands

```bash
# Stop Redis
docker-compose stop redis

# Remove Redis data (safe - will rebuild)
docker volume rm root_redis-data

# Start Redis fresh
docker-compose up -d redis

# Wait 10 seconds
timeout /t 10

# Restart services
docker-compose restart backend worker_vatican beat

# Verify
docker-compose exec redis redis-cli DBSIZE
```

## What Gets Deleted?

**Safe to delete:**
- ✅ Old Celery task results (220k+ keys)
- ✅ Expired state keys
- ✅ Old cooldown keys

**Will rebuild automatically:**
- ✅ Ticket state keys (rebuilt on first check)
- ✅ Session data (rebuilt as needed)

**NOT deleted:**
- ✅ Database data (agencies, tasks, users)
- ✅ Telegram groups
- ✅ Check history

## After Fix

1. **Verify Redis is working:**
   ```bash
   docker-compose exec redis redis-cli DBSIZE
   ```
   Should show < 100 keys (fresh start)

2. **Verify workers are running:**
   ```bash
   docker-compose logs -f worker_vatican | grep ORCHESTRATOR
   ```
   Should see tasks every 5 seconds

3. **Monitor for 5 minutes:**
   - Redis key count should stay < 10,000
   - Workers should be checking continuously
   - No errors in logs

## Prevention

The fix we applied earlier will prevent this from happening again:
- Task results auto-expire after 1 hour
- Daily cleanup removes stale keys
- Memory limits prevent runaway growth

But Redis needs to be restarted to apply the new settings.

## Why This Happened

1. Old Celery settings stored results forever
2. 220,000+ keys accumulated
3. Redis takes 20+ seconds to load
4. Workers timeout trying to connect
5. Redis gets stuck in loading state

## Long-term Solution

After this emergency fix:
1. ✅ New settings prevent bloat (already applied)
2. ✅ Daily cleanup runs automatically (already scheduled)
3. ✅ Memory limits prevent issues (already configured)

**This should be the last time you need to do this!**

## Verification Commands

```bash
# Check Redis key count (should be < 10k)
docker-compose exec redis redis-cli DBSIZE

# Check Redis memory (should be < 100MB)
docker-compose exec redis redis-cli INFO memory | grep used_memory_human

# Check workers are running
docker-compose logs worker_vatican | tail -20

# Check for errors
docker-compose logs worker_vatican | grep -i error | tail -10
```

## If Still Having Issues

1. **Check all services are running:**
   ```bash
   docker-compose ps
   ```

2. **Restart everything:**
   ```bash
   docker-compose restart
   ```

3. **Check logs:**
   ```bash
   docker-compose logs backend
   docker-compose logs worker_vatican
   docker-compose logs beat
   docker-compose logs redis
   ```

---

**Run `fix_redis_now.bat` to fix the issue now!**
