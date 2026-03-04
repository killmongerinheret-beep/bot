# Manual Commands - Dashboard Sold Out Fix

If the PowerShell scripts have issues, use these manual commands instead.

## Quick Fix (5 Commands)

### 1. Restart Vatican Worker
```powershell
docker-compose restart worker_vatican
```

### 2. Wait 5 seconds
```powershell
Start-Sleep -Seconds 5
```

### 3. Trigger Fresh Check
```powershell
docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; print(orchestrate_all_tasks())"
```

### 4. Watch Logs
```powershell
docker-compose logs -f worker_vatican
```
Press `Ctrl+C` to stop.

Look for:
- ✅ `/fromtag/1/...` (for 1-visitor tasks)
- ✅ `visitorNum=1` (in API calls)
- ✅ `Smart Group: .../1v`

### 5. Test Backend API
Open in browser:
```
http://localhost:8000/api/tasks/
```

---

## Check Task #19 Configuration

```powershell
docker-compose exec -T backend python -c "from monitors.models import MonitorTask; t = MonitorTask.objects.get(id=19); print(f'Visitors: {t.visitors}, Dates: {t.dates[:3]}, Status: {t.last_status}')"
```

---

## Check Recent Results

```powershell
docker-compose exec -T backend python -c "from monitors.models import CheckResult; from django.utils import timezone; from datetime import timedelta; r = CheckResult.objects.filter(check_time__gte=timezone.now()-timedelta(hours=1), task__site='vatican'); print(f'Recent checks: {r.count()}, Available: {r.filter(status=\"available\").count()}, Sold out: {r.filter(status=\"sold_out\").count()}')"
```

---

## View Recent Logs

### Last 50 lines
```powershell
docker-compose logs --tail=50 worker_vatican
```

### Live logs
```powershell
docker-compose logs -f worker_vatican
```

### Filter for visitor patterns
```powershell
docker-compose logs --tail=100 worker_vatican | Select-String "fromtag"
docker-compose logs --tail=100 worker_vatican | Select-String "visitorNum"
docker-compose logs --tail=100 worker_vatican | Select-String "Smart Group"
```

---

## Check Services Status

```powershell
docker-compose ps
```

Should show:
- backend (running)
- worker_vatican (running)
- db (running)
- redis (running)

---

## Restart All Services

```powershell
docker-compose restart
```

---

## Test Cloudflare Tunnel

If you're using Cloudflare tunnel, test it:

```powershell
# In browser, open:
https://your-tunnel-url.trycloudflare.com/api/tasks/
```

Should show same JSON as `http://localhost:8000/api/tasks/`

---

## Vercel Dashboard

1. Go to: https://bot-pl2x.vercel.app/
2. Hard refresh: `Ctrl + Shift + R`
3. Check browser console (F12) for errors

---

## Timeline

After triggering fresh check:

- **0-30 sec**: Tasks queued
- **30-90 sec**: Workers processing
- **90-180 sec**: Results saved to database
- **180+ sec**: Dashboard should show updated data

---

## Troubleshooting

### Worker keeps restarting
```powershell
docker-compose logs worker_vatican
```
Look for Python errors.

### Backend not accessible
```powershell
docker-compose restart backend
docker-compose logs backend
```

### Database issues
```powershell
docker-compose restart db
```

### Redis issues
```powershell
docker-compose restart redis
```

---

## Expected Log Output (After Fix)

```
🕸️ [Multi-Scan] Navigating to Deep Link: .../fromtag/1/1773615600000/MV-Biglietti/1
📊 Smart Group: 16/03/2026/929041748/None/1v → 1 agencies
/api/visit/timeavail?lang=it&visitTypeId=929041748&visitorNum=1&visitDate=16/03/2026
✅ Found X slots
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Restart worker | `docker-compose restart worker_vatican` |
| Trigger check | `docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; print(orchestrate_all_tasks())"` |
| View logs | `docker-compose logs -f worker_vatican` |
| Check services | `docker-compose ps` |
| Test backend | Open `http://localhost:8000/api/tasks/` |
| Restart all | `docker-compose restart` |

---

## If Scripts Don't Work

Just run these 3 commands:

```powershell
# 1. Restart worker
docker-compose restart worker_vatican

# 2. Wait and trigger check
Start-Sleep -Seconds 5
docker-compose exec -T backend python -c "from monitors.tasks import orchestrate_all_tasks; print(orchestrate_all_tasks())"

# 3. Watch logs
docker-compose logs -f worker_vatican
```

Then wait 2-3 minutes and refresh the dashboard.
