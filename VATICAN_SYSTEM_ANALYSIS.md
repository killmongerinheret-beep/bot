# Vatican System Analysis - March 11, 2026

## ✅ TICKET TYPE DIFFERENTIATION - WORKING CORRECTLY

### Standard Tickets (Type 0)
- **Count**: 6 tasks
- **Language**: `None` (correct)
- **Search API Tag**: `MV-Biglietti`
- **visitLang Parameter**: Empty string `""`
- **Example**: Task #1, #3, #5, #7, #8, #9

### Guided Tours (Type 1)
- **Count**: 3 tasks
- **Language**: `ENG`, `ITA` (correct)
- **Search API Tag**: `MV-Visite-Guidate`
- **visitLang Parameter**: Language code (`ENG`, `ITA`)
- **Example**: Task #2 (ENG), #4 (ENG), #6 (ITA)

### Verification from Logs
```
✅ SEARCH API CHECK: 10/03/2026 | Ticket: Musei Vaticani - Biglietti d'ingresso | Lang: None
✅ SEARCH API CHECK: 10/03/2026 | Ticket: Musei Vaticani - Visita Guidata | Lang: ENG
✅ SEARCH API CHECK: 20/06/2026 | Ticket: Musei Vaticani - Visita Guidata | Lang: ITA
```

**CONCLUSION**: System correctly differentiates between standard tickets and guided tours. No confusion detected.

---

## ❌ NOTIFICATION SPAM ISSUE - ROOT CAUSES IDENTIFIED

### Problem 1: Cache State Not Persisting
**Symptom**: Logs show "First check" happening repeatedly
```
[18:22:40] ℹ️ First check: Musei Vaticani - Visita Guidata is AVAILABLE - NOT alerting
[18:22:41] ℹ️ First check: Musei Vaticani - Biglietti d'ingresso is AVAILABLE - NOT alerting
[18:23:22] ℹ️ First check: Musei Vaticani - Visita Guidata is AVAILABLE - alerting (user requested any_change)!
[18:23:23] ℹ️ First check: Musei Vaticani - Biglietti d'ingresso is AVAILABLE - NOT alerting
```

**Root Cause**: The `state_key` uses `ticket_id` in the key, but `ticket_id` changes every time (fresh ID from Search API). This means the cache key is different on each check, so it always appears as "first check".

**Current Code**:
```python
state_key = f"ticket_state:{task.id}:{fresh_id}:{date}"  # ❌ fresh_id changes!
```

**Fix**: Use task.id and date only (not ticket_id):
```python
state_key = f"ticket_state:{task.id}:{date}"  # ✅ Stable key
```

### Problem 2: Tasks with `notification_mode='any_change'`
**Affected Tasks**: Task #1, #2, #5, #6
**Issue**: These tasks alert on first check when `notification_mode='any_change'`

**Current Logic**:
```python
if is_first_check and is_now_available:
    if task.notification_mode == 'any_change':
        should_alert = True  # ❌ Alerts on first check
```

**Fix**: Never alert on first check, regardless of notification_mode:
```python
if is_first_check:
    # Never alert on first check - just establish baseline
    logger.info(f"ℹ️ First check: {ticket_name} - establishing baseline")
    should_alert = False
```

### Problem 3: Cooldown Key Uses Changing ticket_id
**Current Code**:
```python
alert_cooldown_key = f"alert_cooldown:{task.id}:{fresh_id}:{date}"  # ❌ fresh_id changes!
```

**Fix**: Use stable key:
```python
alert_cooldown_key = f"alert_cooldown:{task.id}:{date}"  # ✅ Stable key
```

---

## 🔧 FIXES TO IMPLEMENT

### Fix 1: Update `run_god_tier_vatican_monitor()` in `backend/monitors/tasks.py`

**Lines to Change**: ~700-750 (notification logic section)

**Changes**:
1. Remove `fresh_id` from `state_key` and `alert_cooldown_key`
2. Remove `is_first_check` alert logic for `any_change` mode
3. Simplify notification logic

### Fix 2: Update `run_smart_vatican_monitor()` in `backend/monitors/tasks.py`

**Lines to Change**: ~450-550 (notification logic section)

**Same changes as Fix 1**

---

## 📊 EXPECTED BEHAVIOR AFTER FIX

### First Check (Establishing Baseline)
```
ℹ️ First check: Musei Vaticani - Biglietti d'ingresso - establishing baseline
✅ State saved: closed (0 slots)
🔕 NO NOTIFICATION SENT
```

### Subsequent Check - No Change
```
ℹ️ Musei Vaticani - Biglietti d'ingresso still CLOSED - no alert needed
🔕 NO NOTIFICATION SENT
```

### State Change: Closed → Open
```
🔔 STATE CHANGE: Musei Vaticani - Biglietti d'ingresso went from CLOSED → OPEN!
✅ TELEGRAM NOTIFICATION sent to 1/1 groups
⏳ Cooldown set for 1 hour
```

### Subsequent Check - Still Open
```
ℹ️ Musei Vaticani - Biglietti d'ingresso still AVAILABLE - no alert needed
🔕 NO NOTIFICATION SENT (cooldown active)
```

---

## 🎯 SUMMARY

**Ticket Type Differentiation**: ✅ WORKING PERFECTLY
- Standard tickets use `ticket_type=0`, `language=None`, `visitLang=""`
- Guided tours use `ticket_type=1`, `language=ENG/ITA/etc`, `visitLang=<code>`
- Search API correctly uses different tags and parameters

**Notification Spam**: ❌ NEEDS FIX
- Root cause: Cache keys include changing `fresh_id`
- Solution: Use stable keys (task.id + date only)
- Additional fix: Never alert on first check

**Next Steps**:
1. Apply fixes to `backend/monitors/tasks.py`
2. Restart worker_vatican container
3. Monitor logs for 5-10 minutes
4. Verify no spam and proper state tracking
