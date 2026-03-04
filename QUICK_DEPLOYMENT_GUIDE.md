# Quick Deployment Guide - Visitor Count Fix

## What Was Fixed

The bot was checking with wrong visitor counts (always 2) instead of using the actual task configuration. This caused Task #19 (1 visitor, March 16) to miss real availability.

## Deploy in 3 Steps

### Step 1: Restart Services
```bash
docker-compose restart celery_worker
```

### Step 2: Verify
```bash
python verify_visitor_count_fix.py
```

### Step 3: Test
```bash
# Watch logs
docker-compose logs -f celery_worker | grep -E "(visitor|fromtag|visitorNum)"

# Look for:
# ✅ /fromtag/1/... (for 1-visitor tasks)
# ✅ visitorNum=1 (in API calls)
# ✅ Smart Group: .../1v → (grouping by visitor count)
```

## What to Expect

### Before Fix
```
🕸️ Navigating to: .../fromtag/2/1773615600000/MV-Biglietti/1
❌ Wrong visitor count (always 2)
```

### After Fix
```
🕸️ Navigating to: .../fromtag/1/1773615600000/MV-Biglietti/1
✅ Correct visitor count (matches task)
📊 Smart Group: 16/03/2026/929041748/None/1v → 1 agencies
```

## Verify Task #19

```bash
python backend/manage.py shell
```

```python
from monitors.models import MonitorTask
task = MonitorTask.objects.get(id=19)
print(f"Visitors: {task.visitors}")  # Should be 1
print(f"Dates: {task.dates}")        # Should include 16/03/2026

# Trigger check
from monitors.tasks import orchestrate_all_tasks
orchestrate_all_tasks()
```

## Rollback (if needed)

```bash
git checkout HEAD~1 backend/monitors/tasks.py
git checkout HEAD~1 worker_vatican/god_tier_monitor.py
git checkout HEAD~1 worker_vatican/hydra_monitor.py
docker-compose restart
```

## Files Changed

- `backend/monitors/tasks.py` - 5 changes
- `worker_vatican/god_tier_monitor.py` - 6 changes
- `worker_vatican/hydra_monitor.py` - 3 changes

## Success Criteria

- [ ] Logs show correct visitor count in deep links
- [ ] Logs show correct visitorNum in API calls
- [ ] Task #19 finds availability for March 16
- [ ] No errors in logs
- [ ] Dashboard shows correct data

## Need Help?

See `FINAL_VERIFICATION_REPORT.md` for complete details.
