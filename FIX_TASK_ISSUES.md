# Fix: Task 15 & 19 Showing 0 Slots + Proxy Warning

## Issues Found

### Issue 1: Proxy Files Missing
**Log**: `⚠️ Could not find proxy files, defaulting to 3 levels up` → `✅ Loaded 0 proxies from /`

**Cause**: The bot is looking for proxy files but can't find them:
- `Webshare_10_proxies.txt`
- `Proxy lists.json`

**Impact**: Bot works without proxies, but might be slower or get rate-limited

### Issue 2: Task #19 (March 16) - Language Mismatch
**Task Config**:
```json
{
  "id": 19,
  "dates": ["2026-03-16"],
  "language": "ENG",  ← Problem!
  "ticket_type": 0,   ← Standard ticket (not guided)
  "ticket_name": "Musei Vaticani - Biglietti d'ingresso"
}
```

**Problem**: Task has `language="ENG"` but `ticket_type=0` (standard ticket)
- Standard tickets don't have language options
- Language should be `null` for standard tickets
- Bot filters out all tickets because of this mismatch

**Log**: `🎯 Filtered to 0 Musei Vaticani admission tickets`

### Issue 3: Task #15 (March 26) - Actually Sold Out
**Task Config**:
```json
{
  "id": 15,
  "dates": ["2026-03-26"],
  "visitors": 2,
  "ticket_type": 0
}
```

**Status**: API returns `❌ No slots available (all sold out)` for 2 visitors
- This is REAL - March 26 is actually sold out for 2 visitors
- Bot is working correctly

## Fixes

### Fix 1: Create Proxy Files (Optional)

The bot works without proxies, but if you want to add them:

**Option A: Skip proxies (works fine)**
- Bot will work without proxies
- Might be slightly slower
- No action needed

**Option B: Add proxy files**

Create `Webshare_10_proxies.txt` in project root:
```
proxy1.example.com:8080:username:password
proxy2.example.com:8080:username:password
```

Or create `Proxy lists.json`:
```json
[
  {
    "entryPoint": "isp.oxylabs.io",
    "port": "8001"
  }
]
```

### Fix 2: Remove Language from Task #19

Task #19 has incorrect configuration. Fix it:

**Option A: Via Django Admin**
1. Go to http://localhost:8000/admin/
2. Login
3. Go to Monitors → Monitor tasks
4. Find Task #19
5. Set `language` to empty/null
6. Save

**Option B: Via Django Shell**
```bash
docker exec -it travelagenntbot-backend-1 python manage.py shell
```

```python
from backend.monitors.models import MonitorTask

# Fix Task #19
task = MonitorTask.objects.get(id=19)
print(f"Before: language={task.language}, ticket_type={task.ticket_type}")

# Standard tickets should have language=None
task.language = None
task.save()

print(f"After: language={task.language}, ticket_type={task.ticket_type}")
```

**Option C: Via API**
```powershell
# Get current task
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/19/" -Method GET

# Update task (remove language)
$body = @{
    language = $null
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/19/" -Method PATCH -Body $body -ContentType "application/json"
```

### Fix 3: Task #15 - No Fix Needed

March 26 is actually sold out for 2 visitors. The bot is working correctly.

**To verify**:
1. Visit https://tickets.museivaticani.va/
2. Select March 26, 2026
3. Select 2 visitors
4. Check if any slots are available

**If you want to find availability**:
- Try different dates
- Try 1 visitor instead of 2
- Check March 28 (Task #18) which has 8 slots available

## Verification

### After fixing Task #19:

**Check logs:**
```powershell
docker logs travelagenntbot-worker_vatican-1 --tail 50 | Select-String "2026-03-16"
```

**Expected**:
```
🎯 Filtered to 1 Musei Vaticani admission tickets  ← Should be 1, not 0
✅ Found X slots for Musei Vaticani - Biglietti d'ingresso
```

**Check API:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/19/" -UseBasicParsing | Select-Object -ExpandProperty Content | python -m json.tool
```

**Expected**:
```json
{
  "id": 19,
  "language": null,  ← Should be null now
  "last_status": "available" or "sold_out",  ← Should show real status
  "latest_check": {
    "details": {
      "slots": [...]  ← Should have slots if available
    }
  }
}
```

## Summary

| Task | Issue | Status | Fix |
|------|-------|--------|-----|
| #18 | None | ✅ Working | 8 slots available |
| #19 | Language mismatch | ⚠️ Needs fix | Set language=null |
| #15 | Actually sold out | ✅ Working | No fix needed |
| Proxies | Files missing | ⚠️ Optional | Add proxy files or ignore |

## Quick Fix Script

Save as `fix_task_19.py`:
```python
#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from backend.monitors.models import MonitorTask

# Fix Task #19
task = MonitorTask.objects.get(id=19)
print(f"Task #19 - Before:")
print(f"  Language: {task.language}")
print(f"  Ticket Type: {task.ticket_type}")
print(f"  Ticket Name: {task.ticket_name}")

# Standard tickets (ticket_type=0) should have language=None
if task.ticket_type == 0 and task.language:
    print(f"\n⚠️ Fixing: Standard ticket should not have language")
    task.language = None
    task.save()
    print(f"✅ Fixed! Language set to None")
else:
    print(f"\n✅ Task is already correct")

print(f"\nTask #19 - After:")
print(f"  Language: {task.language}")
print(f"  Ticket Type: {task.ticket_type}")
```

Run it:
```bash
docker exec -it travelagenntbot-backend-1 python /app/fix_task_19.py
```

## Expected Results After Fix

**Task #18 (March 28, 1 visitor)**:
- ✅ Status: available
- ✅ Slots: 8 available
- ✅ Working perfectly

**Task #19 (March 16, 1 visitor)** - After fix:
- ✅ Language: null
- ✅ Bot will check correctly
- ✅ Will show real availability

**Task #15 (March 26, 2 visitors)**:
- ✅ Status: sold_out (real status)
- ✅ Bot working correctly
- ℹ️ Try 1 visitor or different date

## Why This Happened

**Task #19 Issue**:
- Someone set language="ENG" on a standard ticket
- Standard tickets don't have language options
- Only guided tours (ticket_type=1) have languages
- Bot correctly filtered it out

**Correct Configuration**:
```
Standard Ticket (ticket_type=0):
  - language: null
  - ticket_name: "Musei Vaticani - Biglietti d'ingresso"

Guided Tour (ticket_type=1):
  - language: "ENG" or "ITA" or "FRA" etc.
  - ticket_name: "Musei Vaticani - Visita guidata"
```

---

**Next Step**: Fix Task #19 by setting language=null, then verify it starts finding slots (if available)
