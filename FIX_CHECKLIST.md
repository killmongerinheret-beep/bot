# Redis Bloat Fix - Checklist

## ✅ What Was Done

### 1. Configuration Fixed (Permanent)
- [x] Added `CELERY_RESULT_EXPIRES = 3600` to settings.py
- [x] Added `CELERY_TASK_IGNORE_RESULT = True` to settings.py
- [x] Added Redis connection retry settings
- [x] Added `cleanup-redis-cache` task to beat schedule
- [x] Enhanced `cleanup_redis_cache()` function

### 2. Cleanup Tools Created
- [x] `backend/fix_redis_bloat.py` - Docker cleanup script
- [x] `run_redis_fix.bat` - Windows automated fix
- [x] `run_redis_fix.sh` - Linux/Mac automated fix
- [x] Django management command already exists

### 3. Documentation Created
- [x] `REDIS_BLOAT_FIX.md` - Complete documentation
- [x] `REDIS_FIX_SUMMARY.md` - Summary
- [x] `QUICK_FIX_REDIS.md` - Quick reference
- [x] `FIX_CHECKLIST.md` - This checklist

---

## 🚀 What You Need to Do

### Step 1: Run the Fix (Choose One)

**Option A: Automated (Recommended)**
```bash
# Windows
run_redis_fix.bat

# Linux/Mac
bash run_redis_fix.sh
```

**Option B: Manual**
```bash
docker-compose exec backend python fix_redis_bloat.py
docker-compose restart backend worker_vatican beat redis
```

### Step 2: Verify It Worked

```bash
# Should show < 10,000 keys
docker-compose exec redis redis-cli DBSIZE

# Should show tasks running
docker-compose logs -f worker_vatican | grep ORCHESTRATOR
```

### Step 3: Done! ✅

Your bot should now:
- Start in < 5 seconds
- Execute tasks every 5 seconds
- Send Telegram notifications
- Auto-cleanup Redis daily

---

## 📋 Verification Checklist

After running the fix, check these:

- [ ] Redis key count < 10,000
  ```bash
  docker-compose exec redis redis-cli DBSIZE
  ```

- [ ] Redis memory < 100MB
  ```bash
  docker-compose exec redis redis-cli INFO memory | grep used_memory_human
  ```

- [ ] Workers are connected
  ```bash
  docker-compose logs worker_vatican | grep "Connected"
  ```

- [ ] Tasks are executing
  ```bash
  docker-compose logs worker_vatican | grep "ORCHESTRATOR"
  ```

- [ ] No connection errors
  ```bash
  docker-compose logs worker_vatican | grep -i "error\|refused"
  ```

- [ ] Telegram notifications work
  - Wait for a ticket to open
  - Check Telegram group for notification

---

## 🔄 Ongoing Monitoring (Optional)

### Daily Check (30 seconds)
```bash
# Check Redis is healthy
docker-compose exec redis redis-cli DBSIZE

# Check workers are running
docker-compose logs worker_vatican | tail -20
```

### Weekly Check (2 minutes)
```bash
# Check Redis memory
docker-compose exec redis redis-cli INFO memory | grep used_memory_human

# Check cleanup tasks ran
docker-compose logs backend | grep "cleanup"

# Check for any errors
docker-compose logs worker_vatican | grep -i "error" | tail -20
```

### Monthly Check (5 minutes)
- Review this checklist
- Verify automated cleanup is working
- Check Redis key count trend

---

## 🆘 If Something Goes Wrong

### Redis still has 100k+ keys
```bash
docker-compose exec backend python manage.py cleanup_redis --aggressive
docker-compose restart redis worker_vatican beat
```

### Workers not connecting
```bash
docker-compose restart worker_vatican beat
docker-compose logs worker_vatican | tail -50
```

### Tasks not executing
```bash
docker-compose restart beat
docker-compose logs beat | tail -50
```

### Need to start completely fresh
```bash
# WARNING: This deletes ALL Redis data
docker-compose exec redis redis-cli FLUSHDB
docker-compose restart worker_vatican beat
docker-compose exec backend python setup_60_day_monitoring.py
```

---

## 📞 Need Help?

1. Check logs:
   ```bash
   docker-compose logs backend
   docker-compose logs worker_vatican
   docker-compose logs beat
   docker-compose logs redis
   ```

2. Check service status:
   ```bash
   docker-compose ps
   ```

3. Read documentation:
   - Quick fix: `QUICK_FIX_REDIS.md`
   - Complete guide: `REDIS_BLOAT_FIX.md`
   - Summary: `REDIS_FIX_SUMMARY.md`

---

## ✅ Success Criteria

Your fix is successful when:

1. ✅ Redis has < 10,000 keys (was 220,000+)
2. ✅ Redis uses < 100MB memory (was 1.7GB)
3. ✅ Workers start in < 5 seconds (was 20+ seconds)
4. ✅ Tasks execute every 5 seconds
5. ✅ Telegram notifications are sent
6. ✅ No "connection refused" errors in logs

---

**Status**: 🟡 READY TO RUN  
**Next Action**: Run `run_redis_fix.bat` (Windows) or `bash run_redis_fix.sh` (Linux/Mac)  
**Estimated Time**: 5 minutes  
**Difficulty**: Easy (automated)
