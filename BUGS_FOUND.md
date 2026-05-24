# Critical Bugs Found in Vatican Bot

## 🐛 BUG #1: Orchestrator Not Scheduled in Celery Beat
**Location:** `backend/core/settings.py` - CELERY_BEAT_SCHEDULE
**Severity:** CRITICAL - Bot not monitoring at all

### Problem:
The orchestrator task `orchestrate_vatican_tasks_search_api` is **NOT in the Celery Beat schedule**. 
Only `instant_sniper_scan` is scheduled (every 5 seconds), which calls the orchestrator, but this is inefficient.

### Current Schedule:
```python
CELERY_BEAT_SCHEDULE = {
    'instant-sniper-scan': {
        'task': 'instant_sniper_scan',
        'schedule': 5.0,  # every 5 seconds
        'options': {'queue': 'vatican', 'priority': 0},
    },
    # ... other tasks ...
    # ❌ orchestrate_vatican_tasks_search_api is MISSING!
}
```

### Impact:
- Monitoring relies on `instant_sniper_scan` which is meant for sniping, not monitoring
- Inefficient task dispatching
- Confusing logs

### Fix:
Add explicit orchestrator schedule OR ensure instant_sniper_scan is working properly.

---

## 🐛 BUG #2: Task Grouping Uses Stale ticket_id
**Location:** `backend/monitors/tasks_search_api.py` line 351
**Severity:** HIGH - Causes duplicate checks

### Problem:
```python
key = (date, task.ticket_id, task.language, task.visitors)
```

The orchestrator groups tasks by `ticket_id`, but Vatican changes IDs frequently. This means:
- Tasks with stale IDs get grouped separately
- Same ticket checked multiple times
- Wastes API calls and proxy bandwidth

### Example:
```
Task A: ticket_id=123 (stale), ticket_name="Musei Vaticani"
Task B: ticket_id=456 (fresh), ticket_name="Musei Vaticani"
Result: 2 separate checks for the SAME ticket!
```

### Fix:
Group by `(date, ticket_name, language, visitors)` instead of ticket_id.

---

## 🐛 BUG #3: normalize_date Silently Skips Past Dates
**Location:** `backend/monitors/tasks.py` line 70
**Severity:** MEDIUM - Tasks disappear without warning

### Problem:
```python
if dt < today:
    logger.info(f"⏭️ Skipping past date: {date_str} ({dt})")
    return None
```

When a date becomes past, it's silently skipped. Users don't know their tasks stopped working.

### Impact:
- Tasks with past dates never run
- No notification to user
- Looks like bot is broken

### Fix:
- Mark tasks as "expired" in database
- Send notification to agency
- Auto-disable expired tasks

---

## 🐛 BUG #4: Bare except Blocks Hide Errors
**Location:** Multiple files (see grep results)
**Severity:** MEDIUM - Hard to debug

### Problem:
```python
except Exception:
    pass  # ❌ Silently swallows all errors
```

Found in:
- `tasks_bulk_hold.py` (3 instances)
- `tasks.py` (3 instances)  
- `tasks_sweep.py` (3 instances)
- `tasks_hold.py` (4 instances)
- `views.py` (8 instances)
- `playwright_checkout.py` (10 instances)

### Impact:
- Errors disappear silently
- Impossible to debug issues
- System fails without logs

### Fix:
Replace with:
```python
except Exception as e:
    logger.warning(f"Non-critical error: {e}")
```

---

## 🐛 BUG #5: N+1 Query Problem in Orchestrator
**Location:** `backend/monitors/tasks_search_api.py` line 327
**Severity:** MEDIUM - Performance issue

### Problem:
```python
tasks = MonitorTask.objects.filter(
    site='vatican',
    is_active=True
).select_related('agency')  # ✅ Good

# But later:
for task in tasks:
    # ... processing ...
    approved_groups = TelegramGroup.objects.filter(  # ❌ N+1 query!
        agency=task.agency,
        status='approved',
        notification_enabled=True
    )
```

### Impact:
- 1 query to get tasks
- N queries to get Telegram groups (one per task)
- Slow with many tasks

### Fix:
Use `prefetch_related`:
```python
tasks = MonitorTask.objects.filter(
    site='vatican',
    is_active=True
).select_related('agency').prefetch_related(
    'agency__telegramgroup_set'
)
```

---

## 🐛 BUG #6: Redis State Seeding Happens Every Cycle
**Location:** `backend/monitors/tasks_search_api.py` line 368
**Severity:** LOW - Inefficient

### Problem:
```python
# ✅ SEED: Pre-populate Redis state as 'closed'
seeded = 0
for group in task_groups.values():
    for tid in group['task_ids']:
        key = f"ticket_state:{tid}:{group['date']}"
        if cache.get(key) is None:  # ❌ Checks Redis every time
            cache.set(key, 'closed', timeout=86400 * 7)
            seeded += 1
```

### Impact:
- Extra Redis calls every 5 seconds
- Unnecessary network overhead
- Slows down orchestration

### Fix:
Only seed once per task creation, not every orchestration cycle.

---

## 🐛 BUG #7: Auto-Hold Cooldown Key Not Stable
**Location:** `backend/monitors/tasks_search_api.py` line 213
**Severity:** HIGH - Duplicate holds

### Problem:
```python
hold_cooldown_key = f"hold_cooldown:{task.id}:{date}:{slot_time}"
```

If Vatican changes slot IDs (which they do), the cooldown key changes, allowing duplicate holds.

### Impact:
- Same slot held multiple times
- Wastes 2captcha balance
- Confuses users

### Fix:
Already correct - uses `task.id:date:slot_time` (not slot_id). ✅

---

## 🐛 BUG #8: Token Pool Runs Even Without Balance
**Location:** `backend/monitors/turnstile_pool.py` line 88
**Severity:** HIGH - Floods logs

### Problem:
```python
def _refill_loop():
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    if not api_key:
        logger.warning("No TWOCAPTCHA_API_KEY — token pool disabled")
        _refill_running = False
        return
    
    # ❌ No balance check! Keeps trying even with $0 balance
    while _refill_running:
        token = _solve_one_token(api_key)  # Fails with ERROR_ZERO_BALANCE
```

### Impact:
- Floods logs with 1,599+ errors per day
- Hides real monitoring logs
- Looks like bot is broken

### Fix:
Check balance before starting pool:
```python
def start_pool(force=False):
    # Check balance first
    r = requests.get('https://2captcha.com/res.php', params={
        'key': api_key, 'action': 'getbalance', 'json': 1
    })
    balance = float(r.json().get('request', 0))
    if balance < 0.01:
        logger.warning(f"2captcha balance too low: ${balance}")
        return
    # ... start pool ...
```

---

## 🐛 BUG #9: Duplicate Notifications to Same Group
**Location:** `backend/monitors/tasks_search_api.py` line 267
**Severity:** MEDIUM - Spam

### Problem:
```python
# ── Per-group dedup key ──
group_sent_key = f"notified:{chat_id}:{date}"
if cache.get(group_sent_key):
    logger.info(f"⏭️ Already notified {chat_id} for {date} — skipping")
    continue
```

This prevents duplicate notifications per date, but if multiple tasks for the same agency/date open at different times, each triggers a notification.

### Impact:
- Multiple notifications for same date
- Annoying for users
- Looks unprofessional

### Fix:
Use `notified:{chat_id}:{date}:{ticket_name}` for more granular dedup.

---

## 🐛 BUG #10: instant_sniper_scan Runs Every 5 Seconds
**Location:** `backend/core/settings.py` line 197
**Severity:** MEDIUM - Resource waste

### Problem:
```python
'instant-sniper-scan': {
    'task': 'instant_sniper_scan',
    'schedule': 5.0,  # every 5 seconds ❌ Too frequent for monitoring
    'options': {'queue': 'vatican', 'priority': 0},
},
```

### Impact:
- Orchestrator runs every 5 seconds
- Dispatches same checks repeatedly
- Wastes CPU, Redis, database queries
- For monitoring, 30-60 seconds is sufficient

### Fix:
Change to 30 seconds for monitoring, or separate snipe vs monitor orchestrators.

---

## Summary

### Critical (Fix Immediately):
1. ✅ **BUG #1**: Orchestrator not scheduled properly
2. ✅ **BUG #2**: Task grouping uses stale ticket_id
3. ✅ **BUG #8**: Token pool runs without balance check

### High Priority:
4. **BUG #3**: Silent date skipping
5. **BUG #7**: Duplicate holds (already fixed)

### Medium Priority:
6. **BUG #4**: Bare except blocks
7. **BUG #5**: N+1 queries
8. **BUG #9**: Duplicate notifications
9. **BUG #10**: Too frequent orchestration

### Low Priority:
10. **BUG #6**: Inefficient Redis seeding
