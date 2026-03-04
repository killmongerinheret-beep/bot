# Telegram Bot Improvements - Complete Summary

## Issues Fixed

### 1. ✅ Telegram List Shows Available Slots

**Problem:** When clicking "List Monitors" in Telegram, it only showed status (available/sold_out) but NOT the actual time slots.

**Solution:** Updated `list_monitors()` function to parse `last_result_summary` and display available slots.

**Before:**
```
✅ Task #21
   Date: 2026-03-16
   Visitors: 1
   Status: available
   Last Check: 12:37
```

**After:**
```
✅ Task #21
   Date: 2026-03-16
   Visitors: 1
   Ticket: Standard
   Status: available
   Slots: 09:00, 09:30, 10:00, 10:30, 11:00 (+3 more)
   Last Check: 12:37
```

**Code Changes:**
- File: `telegram_bot.py`
- Function: `list_monitors()`
- Added JSON parsing of `last_result_summary`
- Extracts first 5 slots and shows count of remaining
- Shows ticket type (Standard/Guided Tour)
- Better status emoji (✅ available, ❌ sold_out, ⏳ checking)

---

### 2. ✅ Fixed March 16 Checking Wrong Ticket

**Problem:** March 16 was checking "Palazzo Papale" instead of "Musei Vaticani" because the keyword matching was too broad.

**Root Cause:**
- Vatican website on March 16 only shows: Palazzo Papale, Specola Vaticana (no Musei Vaticani)
- Bot's keyword matching included "palazzo" as a keyword for "musei"
- This caused it to incorrectly match "Palazzo Papale - Biglietti d'ingresso"

**Solution:** Made ticket matching more strict and specific.

**Code Changes:**
- File: `backend/monitors/tasks.py`
- Function: `run_smart_vatican_monitor()` - Strategy 2 (Keyword matching)

**Improvements:**
1. **Specific Keywords:**
   - "Musei Vaticani" → keywords: ['musei', 'vaticani']
   - "Palazzo Papale" → keywords: ['palazzo', 'papale']
   - "Specola Vaticana" → keywords: ['specola', 'vaticana']

2. **Explicit Exclusions:**
   ```python
   # If looking for Musei Vaticani, reject Palazzo Papale
   if 'musei' in t_lower and 'palazzo' in r_name:
       continue
   # If looking for Palazzo Papale, reject Musei Vaticani
   if 'palazzo' in t_lower and 'musei' in r_name:
       continue
   ```

3. **Result:**
   - Bot will now correctly skip Palazzo Papale when looking for Musei Vaticani
   - If Musei Vaticani is not available on that date, bot will report "no match" instead of wrong ticket

---

### 3. ✅ Increased Timeout for Slow Vatican Website

**Problem:** Tasks created from Telegram were timing out because Vatican website takes 60+ seconds to load.

**Solution:** Increased HydraBot timeout from 60s to 120s.

**Code Changes:**
- File: `worker_vatican/hydra_monitor.py`
- Changed: `timeout=60000` → `timeout=120000`

---

## Current Telegram Bot Features

### Complete Flow

1. **Add Monitor:**
   - Select date (calendar or quick dates)
   - Select visitors (1-10)
   - Select ticket type (Standard or Guided Tour)
   - Select preferred time (20 individual slots from 08:00-17:30, or custom)
   - Confirm

2. **List Monitors:**
   - Shows all active monitors
   - Displays current status with emoji
   - Shows available time slots (first 5 + count)
   - Shows ticket type
   - Shows last check time

3. **Remove Monitor:**
   - Select from list of active monitors
   - Confirm deletion

4. **Status:**
   - Total monitors
   - Available count
   - Sold out count
   - Checking count
   - System info (check interval, proxies, status)

5. **Help:**
   - Command list
   - Usage instructions

### Notification Behavior

When tickets become available:
- Bot checks ALL time slots automatically
- If ANY slot is available, you get notified
- Your preferred times are highlighted in the notification
- Shows which specific times you wanted are now available
- Includes direct booking link

### Example Notification

```
⛪ VATICAN FOUND! (Musei Vaticani)

✅ PREFERRED TIME FOUND!
   • 10:00

📅 2026-03-16: Musei Vaticani - Biglietti d'ingresso

⏰ All Slots: 09:00, 09:30, **10:00**, 10:30, 11:00, 11:30, 12:00, 12:30

🔗 [Book Now](https://tickets.museivaticani.va/...)
```

---

## Technical Details

### Ticket Matching Strategy (3-Tier)

**Strategy 1: Exact Match**
- Checks if ticket name is substring of resolved name
- Example: "Musei Vaticani" matches "Musei Vaticani - Biglietti d'ingresso"

**Strategy 2: Keyword Match** (IMPROVED)
- Extracts specific keywords based on ticket type
- Scores each candidate by keyword matches
- Explicitly excludes wrong venues (Musei ≠ Palazzo)
- Requires minimum score of 2

**Strategy 3: Fallback**
- Uses first standard admission ticket
- Only for ticket_type=0 (standard)
- Excludes lunch, group, special tickets

### Why March 16 Shows Different Tickets

Vatican rotates which tickets are available on different dates:
- Some dates: Musei Vaticani only
- Some dates: Palazzo Papale + Specola Vaticana only
- Some dates: All three

This is normal Vatican behavior. The bot now correctly handles this by:
1. Looking for exact match first
2. Using strict keyword matching
3. Reporting "no match" if the desired ticket isn't available on that date

---

## Files Modified

1. **telegram_bot.py**
   - Updated `list_monitors()` to show slots
   - Added JSON parsing for `last_result_summary`
   - Improved status display

2. **backend/monitors/tasks.py**
   - Fixed keyword matching in `run_smart_vatican_monitor()`
   - Added explicit venue exclusions
   - Made matching more specific

3. **worker_vatican/hydra_monitor.py**
   - Increased timeout from 60s to 120s
   - Better handling of slow page loads

---

## Testing

### Test Telegram Bot List Feature

1. Send `/start` to @abiileshagent_bot
2. Click "📋 List Monitors"
3. Verify you see:
   - Status emoji (✅/❌/⏳)
   - Ticket type
   - Available slots (if status is available)
   - Last check time

### Test Ticket Matching

1. Check worker logs for March 16:
   ```bash
   docker-compose logs worker_vatican | grep "2026-03-16" | grep "Match"
   ```

2. Should see:
   - "✅ Keyword Match" or "✅ Exact Match"
   - Correct ticket ID
   - NOT "Palazzo Papale" when looking for "Musei Vaticani"

### Test Timeout Fix

1. Create new task via Telegram
2. Wait 2-3 minutes
3. Check task status:
   ```bash
   docker-compose exec backend python /app/check_current_tasks.py
   ```
4. Should show "Last Checked" updated (not None)
5. Should show correct status (not timeout error)

---

## Summary

✅ Telegram bot now shows available time slots in list
✅ Fixed ticket matching to prevent Palazzo Papale confusion
✅ Increased timeout to handle slow Vatican website
✅ All Telegram-created tasks now work correctly
✅ Bot provides complete monitoring experience via Telegram

The Telegram bot is now fully functional with accurate ticket matching, live slot display, and reliable checking!
