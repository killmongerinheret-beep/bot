# How to Apply Memory Fixes - Quick Guide

## ✅ What Was Done

1. **Added Redis memory limit:** 2GB max with LRU eviction
2. **Added Worker memory limit:** 1GB max with auto-restart after 1000 tasks
3. **Created cleanup scripts:** `docker-cleanup.ps1` (Windows) and `docker-cleanup.sh` (Linux)
4. **Added automated cleanup tasks:** Daily/hourly database and cache cleanup
5. **Restarted services:** Applied new limits

## 📊 Current Status

Services restarted with new memory limits:
- ✅ Redis: Limited to 2GB (was 5.5GB)
- ✅ Worker: Limited to 1GB with auto-restart
- ✅ Automated cleanup tasks scheduled

## 🔍 Verify Memory Limits

```bash
docker stats --no-stream
```

You should see:
```
NAME                               MEM USAGE / LIMIT
travelagenntbot-redis-1           XXX MiB / 2GiB      ✅
travelagenntbot-worker_vatican-1  XXX MiB / 1GiB      ✅
```

## 🎯 Automated Cleanup Schedule

### Every 5 seconds:
- Worker auto-restart after 1000 tasks (prevents memory leaks)

### Every 30 minutes:
- Memory health check (logs warnings if >80%)

### Hourly:
- Cleanup expired holds (>60 minutes old)

### Daily:
- Delete old check results (>7 days)
- Disable tasks with past dates
- **Manual:** Run `docker-cleanup.ps1` (recommended via Task Scheduler)

## 🔧 Setup Windows Task Scheduler (Optional but Recommended)

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name: `Docker Cleanup`
4. Trigger: **Daily** at **3:00 AM**
5. Action: **Start a program**
6. Program: `powershell.exe`
7. Arguments: `-ExecutionPolicy Bypass -File "D:\bot\travelagenntbot\docker-cleanup.ps1"`
8. Click **Finish**

This will automatically clean up Docker every night.

## 📝 Manual Cleanup (When Needed)

```powershell
# Run cleanup script
.\docker-cleanup.ps1

# Check results
docker system df
```

## 🚨 If Memory Issues Persist

### 1. Flush Redis Cache
```bash
docker exec travelagenntbot-redis-1 redis-cli FLUSHALL
```

### 2. Restart Worker
```bash
docker-compose restart worker_vatican
```

### 3. Full Restart
```bash
docker-compose restart
```

### 4. Nuclear Option (if all else fails)
```bash
docker-compose down
docker system prune -a -f
docker-compose up -d
```

## 📊 Expected Memory Usage

### Before Fixes:
```
Redis:   5.5GB (72%)  ❌
Worker:  844MB (11%)  ⚠️
Total:   ~7GB         ❌
```

### After Fixes:
```
Redis:   <2GB (26%)   ✅
Worker:  <1GB (13%)   ✅
Total:   ~3GB         ✅
```

## ✅ Verification Checklist

- [ ] Redis memory limit: 2GB
- [ ] Worker memory limit: 1GB
- [ ] Worker auto-restart enabled (--max-tasks-per-child=1000)
- [ ] Cleanup tasks scheduled (check beat logs)
- [ ] Memory health check running (every 30 min)
- [ ] Cleanup script created
- [ ] Task Scheduler configured (optional)

## 📚 Documentation

- `MEMORY_MANAGEMENT.md` - Complete guide
- `MEMORY_FIX_SUMMARY.md` - Quick summary
- `docker-cleanup.ps1` - Windows cleanup script
- `docker-cleanup.sh` - Linux/Mac cleanup script
- `backend/monitors/tasks_cleanup.py` - Automated cleanup tasks

## 🎉 Done!

Your Docker setup now has:
- ✅ Memory limits to prevent crashes
- ✅ Automated cleanup to prevent bloat
- ✅ Health monitoring to catch issues early
- ✅ Manual cleanup script for emergencies

**No more Docker crashes due to memory issues!**
