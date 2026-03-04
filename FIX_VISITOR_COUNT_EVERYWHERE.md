# Fix: Visitor Count Must Be Passed Everywhere

## Root Cause Analysis

The bot has the new API method with JSESSIONID cookies and IDs implemented correctly in `god_tier_monitor_v2.py`, BUT the visitor count is not being passed through the call chain.

### Call Chain

```
orchestrate_all_tasks()
  ↓
run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids)  ← Missing visitors!
  ↓
monitor.check_availability_headless(date_str, ticket_type, languages)  ← Missing visitors!
  ↓
Falls back to:
run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids)  ← Missing visitors!
  ↓
bot.resolve_all_dynamic_ids(page, ticket_type, target_date, visitors=2)  ← HARDCODED!
```

## Files That Need Changes

### 1. backend/monitors/tasks.py

#### Change 1: run_god_tier_vatican_monitor function signature
**Line 394**:
```python
# BEFORE:
def run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, use_browser_fallback=True):

# AFTER:
def run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors=2, use_browser_fallback=True):
```

#### Change 2: Pass visitors to check_availability_headless
**Line ~420**:
```python
# BEFORE:
return await monitor.check_availability_headless(
    date_str=date,
    ticket_type=ticket_type,
    languages=languages
)

# AFTER:
return await monitor.check_availability_headless(
    date_str=date,
    ticket_type=ticket_type,
    languages=languages,
    visitors=visitors
)
```

#### Change 3: Pass visitors to fallback
**Line ~438**:
```python
# BEFORE:
return run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids)

# AFTER:
return run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors)
```

#### Change 4: run_smart_vatican_monitor function signature
**Line 179**:
```python
# BEFORE:
def run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids):

# AFTER:
def run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors=2):
```

#### Change 5: Pass visitors to resolve_all_dynamic_ids
**Line 213**:
```python
# BEFORE:
resolved_ids = await bot.resolve_all_dynamic_ids(
    page,
    ticket_type=ticket_type,
    target_date=date,
    visitors=2  ← HARDCODED!
)

# AFTER:
resolved_ids = await bot.resolve_all_dynamic_ids(
    page,
    ticket_type=ticket_type,
    target_date=date,
    visitors=visitors  ← Use parameter!
)
```

#### Change 6: orchestrate_all_tasks must pass visitors
**Find where run_god_tier_vatican_monitor is called** (around line 100-150):
```python
# BEFORE:
run_god_tier_vatican_monitor.delay(
    date=date_str,
    ticket_id=ticket_id,
    ticket_name=ticket_name,
    language=language,
    task_ids=task_ids
)

# AFTER:
run_god_tier_vatican_monitor.delay(
    date=date_str,
    ticket_id=ticket_id,
    ticket_name=ticket_name,
    language=language,
    task_ids=task_ids,
    visitors=visitors  ← Add this!
)
```

### 2. worker_vatican/god_tier_monitor.py

#### Change: check_availability_headless function signature
**Find the function** (should be around line 50-100):
```python
# BEFORE:
async def check_availability_headless(self, date_str, ticket_type, languages):

# AFTER:
async def check_availability_headless(self, date_str, ticket_type, languages, visitors=2):
```

#### Pass visitors to check_availability
```python
# BEFORE:
return await self.check_availability(
    date_str=date_str,
    ticket_type=ticket_type,
    languages=languages
)

# AFTER:
return await self.check_availability(
    date_str=date_str,
    ticket_type=ticket_type,
    languages=languages,
    visitors=visitors
)
```

### 3. worker_vatican/hydra_monitor.py

#### Change 1: check_via_click default parameter
**Line 1132**:
```python
# BEFORE:
async def check_via_click(self, page, ticket_id, ticket_name, ticket_index=0, visit_date=None, visitors=2):

# AFTER:
async def check_via_click(self, page, ticket_id, ticket_name, ticket_index=0, visit_date=None, visitors=1):
```
**Note**: Change default from 2 to 1, or better yet, make it required (no default)

#### Change 2: check_via_api default parameter
**Line 1207**:
```python
# BEFORE:
async def check_via_api(self, page, visit_type_id, target_date, visitors=2, language="ENG", visit_lang=""):

# AFTER:
async def check_via_api(self, page, visit_type_id, target_date, visitors=1, language="ENG", visit_lang=""):
```

#### Change 3: Line 1363 - Pass actual visitors
```python
# BEFORE:
slots = await self.check_via_api(page, v_id, date, visitors=2, language=language, visit_lang=visit_lang)

# AFTER:
slots = await self.check_via_api(page, v_id, date, visitors=visitors, language=language, visit_lang=visit_lang)
```
**Note**: Need to ensure `visitors` variable is available in this scope

## How to Get Visitors Value in orchestrate_all_tasks

The orchestrate function needs to get the visitor count from the tasks. Since multiple tasks might have different visitor counts, we need to group by visitor count:

```python
# Group tasks by (date, ticket_type, language, visitors)
groups = {}
for task in tasks:
    key = (task.dates[0], task.ticket_type, task.language, task.visitors)
    if key not in groups:
        groups[key] = []
    groups[key].append(task.id)

# Dispatch checks for each group
for (date, ticket_type, language, visitors), task_ids in groups.items():
    run_god_tier_vatican_monitor.delay(
        date=date,
        ticket_id='',  # Will be resolved dynamically
        ticket_name='Musei Vaticani - Biglietti d\'ingresso',
        language=language,
        task_ids=task_ids,
        visitors=visitors  ← Now includes visitor count!
    )
```

## Testing After Fix

### Test 1: Task #19 (March 16, 1 visitor)
```bash
# Should navigate to:
https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1
                                              ↑ Correct!

# Should show:
Candidates: ['Musei Vaticani - Biglietti d\'ingresso', ...]
✅ Found X slots for March 16, 2026
```

### Test 2: Task #15 (March 26, 2 visitors)
```bash
# Should navigate to:
https://tickets.museivaticani.va/home/fromtag/2/1774479600000/MV-Biglietti/1
                                              ↑ Correct!

# Should show correct tickets for 2 visitors
```

### Test 3: Task #18 (March 28, 1 visitor)
```bash
# Should navigate to:
https://tickets.museivaticani.va/home/fromtag/1/1774652400000/MV-Biglietti/1
                                              ↑ Correct!
```

## Verification Commands

**Check logs for visitor count**:
```bash
docker logs travelagenntbot-worker_vatican-1 --tail 100 | grep "fromtag"
```

**Should see**:
```
🕸️ Navigating to: .../fromtag/1/...  ← For 1 visitor tasks
🕸️ Navigating to: .../fromtag/2/...  ← For 2 visitor tasks
```

**Check API calls**:
```bash
docker logs travelagenntbot-worker_vatican-1 --tail 100 | grep "visitorNum"
```

**Should see**:
```
visitorNum=1  ← For 1 visitor tasks
visitorNum=2  ← For 2 visitor tasks
```

## Priority

🔴 **CRITICAL** - Without this fix:
- Bot checks wrong tickets
- Misses real availability
- Shows false "sold out" status
- User reported March 16 has slots for 1 visitor but bot can't see them

## Summary of Changes

1. Add `visitors` parameter to all monitor functions
2. Pass `visitors` through entire call chain
3. Remove all hardcoded `visitors=2`
4. Group tasks by visitor count in orchestration
5. Verify deep links use correct visitor count
6. Verify API calls use correct visitor count

**Total files to modify**: 3
- `backend/monitors/tasks.py` (6 changes)
- `worker_vatican/god_tier_monitor.py` (2 changes)
- `worker_vatican/hydra_monitor.py` (3 changes)
