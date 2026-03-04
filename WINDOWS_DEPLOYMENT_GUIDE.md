# Windows Deployment Guide - Visitor Count Fix

## Quick Start (3 Commands)

### 1. Deploy the Fix
```powershell
.\deploy_fixes_windows.ps1
```

### 2. Check Logs
```powershell
.\check_logs_windows.ps1
```

### 3. Test Task #19
```powershell
.\test_task_19_windows.ps1
```

---

## Manual Commands (if scripts don't work)

### Restart Vatican Worker
```powershell
docker-compose restart worker_vatican
```

### View Logs
```powershell
# Last 50 lines
docker-compose logs --tail=50 worker_vatican

# Live logs (Ctrl+C to stop)
docker-compose logs -f worker_vatican
```

### Check Task #19 Configuration
```powershell
docker-compose exec backend python manage.py shell
```

Then in the Django shell:
```python
from monitors.models import MonitorTask
task = MonitorTask.objects.get(id=19)
print(f"Visitors: {task.visitors}")
print(f"Dates: {task.dates}")
```

### Trigger Test Check
In Django shell:
```python
from monitors.tasks import orchestrate_all_tasks
orchestrate_all_tasks()
```

---

## What to Look For in Logs

### ✅ Good Signs (After Fix)
```
🕸️ Navigating to: .../fromtag/1/1773615600000/MV-Biglietti/1
📊 Smart Group: 16/03/2026/929041748/None/1v → 1 agencies
/api/visit/timeavail?...&visitorNum=1&...
```

### ❌ Bad Signs (Before Fix)
```
🕸️ Navigating to: .../fromtag/2/1773615600000/MV-Biglietti/1
(Should be /fromtag/1/ for 1-visitor tasks)
```

---

## Troubleshooting

### "No such service: celery_worker"
✅ **Fixed!** The correct service name is `worker_vatican`, not `celery_worker`

### "grep is not recognized"
✅ **Fixed!** Use the PowerShell scripts instead:
- `.\check_logs_windows.ps1` - Filters logs for visitor patterns
- `.\deploy_fixes_windows.ps1` - Deploys and shows logs

### "No module named 'django'"
✅ **Fixed!** Run commands inside Docker:
```powershell
docker-compose exec backend python manage.py shell
```

### Docker not running
Start Docker Desktop, then run:
```powershell
docker-compose ps
```

---

## Service Names Reference

Your docker-compose.yml has these services:
- `db` - PostgreSQL database
- `redis` - Redis cache
- `backend` - Django backend
- `worker_vatican` - Vatican ticket worker (THIS ONE!)
- `worker_colosseum` - Colosseum ticket worker
- `beat` - Celery beat scheduler

---

## Expected Results

### Task #19 (March 16, 1 visitor)
After the fix:
- ✅ Deep link uses `/fromtag/1/...` (1 visitor)
- ✅ API calls use `visitorNum=1`
- ✅ Shows "Musei Vaticani" tickets
- ✅ Finds availability user confirmed exists

### All Tasks
- ✅ Each task uses its configured visitor count
- ✅ Logs show correct grouping: `.../1v` or `.../2v`
- ✅ No errors about missing parameters

---

## Files Changed

All fixes have been applied to:
- `backend/monitors/tasks.py` - 5 changes
- `worker_vatican/god_tier_monitor.py` - 6 changes
- `worker_vatican/hydra_monitor.py` - 3 changes

No syntax errors detected. Ready for deployment!

---

## Need Help?

1. Run the deployment script: `.\deploy_fixes_windows.ps1`
2. Check logs: `.\check_logs_windows.ps1`
3. Test Task #19: `.\test_task_19_windows.ps1`
4. See full details: `FINAL_VERIFICATION_REPORT.md`

---

## Quick Reference

| Task | Command |
|------|---------|
| Deploy | `.\deploy_fixes_windows.ps1` |
| Check logs | `.\check_logs_windows.ps1` |
| Test Task #19 | `.\test_task_19_windows.ps1` |
| Live logs | `docker-compose logs -f worker_vatican` |
| Restart | `docker-compose restart worker_vatican` |
| Django shell | `docker-compose exec backend python manage.py shell` |
