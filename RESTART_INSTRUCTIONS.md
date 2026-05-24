# Vatican Bot - Restart Instructions

## Critical Bugs Fixed ✅

1. **Token Pool Balance Check** - No more CAPTCHA error spam
2. **Task Grouping** - Eliminates duplicate checks (50% fewer API calls)
3. **Orchestrator Scheduling** - Now runs every 30s (was 5s)
4. **N+1 Queries** - Database performance improved
5. **Log Noise** - Cleaner, more readable logs

## How to Restart

### Option 1: Restart All Services (Recommended)
```bash
docker-compose restart
```

### Option 2: Restart Specific Services
```bash
# Restart worker (applies token pool fix)
docker-compose restart worker_vatican

# Restart beat (applies orchestrator schedule fix)
docker-compose restart beat

# Restart backend (applies all fixes)
docker-compose restart backend
```

### Option 3: Full Rebuild (If issues persist)
```bash
docker-compose down
docker-compose up -d --build
```

## Verification Steps

### 1. Check Services Are Running
```bash
docker-compose ps
```

Expected output:
```
NAME                              STATUS
travelagenntbot-backend-1         Up
travelagenntbot-beat-1            Up
travelagenntbot-worker_vatican-1  Up
...
```

### 2. Check Token Pool Status
```bash
docker-compose logs worker_vatican | grep "token pool"
```

**If you have 2captcha balance:**
```
✅ 2captcha balance: $3.50 — starting token pool
🔐 Token pool started
```

**If you have $0 balance:**
```
⚠️ 2captcha balance too low ($0.000) — token pool disabled
   Top up at https://2captcha.com to enable auto-booking features
```

### 3. Check Orchestrator Is Running
```bash
docker-compose logs beat | grep "vatican-monitor-orchestrator"
```

Expected output (every 30 seconds):
```
[INFO] Scheduler: Sending due task Vatican Monitor - Orchestrate All Tasks (orchestrate_vatican_tasks_search_api)
```

### 4. Check Monitoring Is Working
```bash
docker-compose logs worker_vatican --tail=50 | grep "ORCHESTRATOR"
```

Expected output:
```
[INFO] 🎯 ORCHESTRATOR: Starting Vatican task orchestration (Search API)
[INFO] 📊 Found 10 tasks grouped into 5 unique checks
[INFO] ✅ Dispatched: 28/03/2026 | Musei Vaticani - Biglietti d'ingresso | 3 agencies
[INFO] 🎯 ORCHESTRATOR: Dispatched 5/5 checks
```

### 5. Check for Errors
```bash
# Should see NO ERROR_ZERO_BALANCE messages
docker-compose logs worker_vatican --tail=100 | grep "ERROR"
```

## Troubleshooting

### Issue: Docker not responding
**Solution:**
1. Restart Docker Desktop manually
2. Wait 30-60 seconds for Docker to fully start
3. Run `docker ps` to verify
4. Then run `docker-compose restart`

### Issue: No tasks found
**Check:**
```bash
docker-compose exec backend python backend/manage.py shell
```
```python
from monitors.models import MonitorTask
print(f"Active Vatican tasks: {MonitorTask.objects.filter(site='vatican', is_active=True).count()}")
```

### Issue: Still seeing CAPTCHA errors
**Check:**
1. Did you restart worker_vatican?
2. Check 2captcha balance: https://2captcha.com
3. If balance is $0, errors should stop after restart

### Issue: No monitoring logs
**Check:**
1. Are there active tasks? (see above)
2. Are task dates in the future?
3. Is Celery Beat running? `docker-compose ps beat`
4. Check Beat logs: `docker-compose logs beat --tail=50`

## What Changed

### Files Modified:
1. `backend/core/settings.py` - Orchestrator schedule
2. `backend/core/celery.py` - Token pool startup (re-enabled)
3. `backend/monitors/tasks_search_api.py` - Task grouping + N+1 fix
4. `backend/monitors/turnstile_pool.py` - Balance check
5. `backend/monitors/tasks.py` - Log level adjustment

### No Database Changes:
- No migrations needed
- No data loss
- Safe to restart anytime

## Expected Behavior After Restart

### With 2captcha Balance:
- ✅ Monitoring every 30 seconds
- ✅ Token pool maintaining 5 tokens
- ✅ Auto-booking enabled
- ✅ Clean logs

### Without 2captcha Balance:
- ✅ Monitoring every 30 seconds
- ⚠️ Token pool disabled (with clear message)
- ⚠️ Auto-booking disabled
- ✅ Telegram notifications still work
- ✅ Clean logs (no CAPTCHA spam)

## Performance Improvements

- **83% fewer orchestration runs** (30s vs 5s)
- **50% fewer API calls** (no duplicate checks)
- **N-1 fewer database queries** (prefetch optimization)
- **Clean logs** (no CAPTCHA spam)

## Next Steps

1. **Restart services** (see above)
2. **Wait 2-3 minutes** for system to stabilize
3. **Check logs** to verify fixes
4. **Monitor Telegram** for notifications
5. **Top up 2captcha** if you need auto-booking

## Support

If issues persist after restart:
- Check `BUGS_FOUND.md` for known issues
- Check `BUG_FIXES_APPLIED.md` for what was fixed
- Review logs for specific error messages
