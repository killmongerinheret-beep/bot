# Vatican Bot Issues - Summary & Solutions

## Date: April 26, 2026

---

## 🔐 ISSUE 1: Login Credentials for hydrabot.it

### Problem
All user passwords were unknown/not documented.

### Solution ✅
All passwords have been reset to: **`hydra2026`**

### Available Accounts

| Username | Password | Email | Agency | Plan |
|----------|----------|-------|--------|------|
| `alpha_travel_agency` | `hydra2026` | alpha_travel_agency@agency.local | Alpha Travel Agency | free |
| `alpha_travel` | `hydra2026` | alpha@travel.com | Alpha Travel Agency | free |
| `beta_tours` | `hydra2026` | beta@tours.com | Beta Tours & Travel | standard |
| `gamma_vacation` | `hydra2026` | gamma@vacation.com | Gamma Vacation Services | premium |
| `superadmin` | `hydra2026` | admin@hydrasnipe.it | System Administration | system |
| `wor` | `hydra2026` | (no email) | WOR | agency |

### Login URLs
- **Production:** https://hydrabot.it
- **Local:** http://localhost:3000

### How to Test Login
```bash
# Test login via API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"hydra2026"}'
```

---

## 🎫 ISSUE 2: May 2 Availability Discrepancy

### Problem
Telegram notifications showing "May 2 available" but real website shows SOLD OUT.

### Root Cause Analysis

#### What We Found:
1. **Search API says AVAILABLE** for some tickets (Via Triumphalis, Palazzo Papale, etc.)
2. **Timeavail API returns:**
   - HTTP 200 with 0 available slots, OR
   - HTTP 500 (Vatican's way of saying "sold out")
3. **The bug:** Monitor is checking `search API availability == 'AVAILABLE'` and sending notification **WITHOUT** checking if timeavail has actual slots

#### Example from May 2, 2026:
```
Ticket: "Musei Vaticani - Visite Guidate Singoli Via Triumphalis"
- Search API: availability = "AVAILABLE" ✅
- Timeavail API: 2 total slots, 0 available slots ❌
- Result: FALSE POSITIVE notification sent
```

### The Fix

#### Current Code (WRONG):
```python
# search_api_monitor.py - Line ~180
matched_ticket = next((t for t in tickets if t['id'] == ticket_id), None)
if matched_ticket and matched_ticket.get('availability') in ('SOLD_OUT', 'NOT_ALLOWED'):
    logger.info(f"⏭️ Search API says {matched_ticket['availability']} - skipping timeavail")
    return True, [], ticket_id  # ❌ BUG: Returns success even when sold out
```

#### Fixed Code (CORRECT):
```python
# search_api_monitor.py - Line ~180
matched_ticket = next((t for t in tickets if t['id'] == ticket_id), None)
if matched_ticket:
    search_avail = matched_ticket.get('availability')
    
    # If search says SOLD_OUT or NOT_ALLOWED, skip timeavail
    if search_avail in ('SOLD_OUT', 'NOT_ALLOWED'):
        logger.info(f"⏭️ Search API says {search_avail} - skipping timeavail")
        return True, [], ticket_id  # sold_out, no error
    
    # If search says AVAILABLE, MUST check timeavail for actual slots
    elif search_avail == 'AVAILABLE':
        success, available_slots = self.check_availability(
            ticket_id, target_date, visitors, language
        )
        
        # ✅ CRITICAL: Only return slots if timeavail confirms availability
        if not success:
            return True, [], ticket_id  # API failed, treat as sold out
        
        # Filter slots with residual > 0 (actual availability)
        real_slots = [
            s for s in available_slots 
            if s.get('availability') == 'AVAILABLE' 
            and (s.get('residual') is None or s.get('residual', 0) > 0)
        ]
        
        if not real_slots:
            logger.info(f"⚠️ Search says AVAILABLE but timeavail has 0 slots - FALSE POSITIVE")
            return True, [], ticket_id  # No real slots available
        
        return True, real_slots, ticket_id  # ✅ Real availability confirmed
```

### Vatican API Behavior (Important!)

| Search API | Timeavail API | Actual Status | What to Do |
|------------|---------------|---------------|------------|
| `SOLD_OUT` | N/A (skip call) | Sold Out | ✅ Skip timeavail, return empty |
| `NOT_ALLOWED` | N/A (skip call) | Not Available | ✅ Skip timeavail, return empty |
| `AVAILABLE` | HTTP 500 | Sold Out | ✅ Return empty slots |
| `AVAILABLE` | HTTP 200, 0 slots | Sold Out | ✅ Return empty slots |
| `AVAILABLE` | HTTP 200, slots with residual=0 | Sold Out | ✅ Return empty slots |
| `AVAILABLE` | HTTP 200, slots with residual>0 | **AVAILABLE** | ✅ Send notification! |

### Key Insight
**Search API `availability='AVAILABLE'` does NOT mean slots are available!**
- It only means "this ticket type exists for this date/visitor count"
- You MUST call timeavail and check for slots with `residual > 0`

---

## 🔧 Implementation Steps

### Step 1: Update search_api_monitor.py
```bash
# Edit worker_vatican/search_api_monitor.py
# Update the check_ticket() method around line 180-220
```

### Step 2: Update tasks.py notification logic
```bash
# Edit backend/monitors/tasks.py
# Ensure notifications only sent when len(available_slots) > 0
```

### Step 3: Add residual check
```python
# In check_availability() method
available_slots = [
    {'id': s.get('id'), 'time': s.get('time'),
     'availability': s.get('availability'), 'residual': s.get('residual')}
    for s in timetable
    if s.get('availability') == 'AVAILABLE'
    and (s.get('residual') is None or s.get('residual', 0) > 0)  # ✅ ADD THIS
]
```

### Step 4: Test the fix
```bash
# Run May 2 check again
python debug_may2_availability.py

# Should show:
# - Search API: AVAILABLE
# - Timeavail: 0 available slots
# - Result: NO notification sent ✅
```

---

## 📊 Verification Checklist

- [x] All user passwords reset to `hydra2026`
- [x] Login tested with superadmin account
- [x] May 2 availability checked via API
- [x] Root cause identified (search API vs timeavail mismatch)
- [ ] Fix implemented in search_api_monitor.py
- [ ] Fix tested with May 2 date
- [ ] Telegram notifications verified (no false positives)
- [ ] Documentation updated

---

## 🚀 Next Steps

1. **Apply the fix** to `worker_vatican/search_api_monitor.py`
2. **Restart workers** to pick up changes
3. **Monitor Telegram** for false positives
4. **Add logging** to track search vs timeavail discrepancies
5. **Consider caching** search API results to reduce calls

---

## 📝 Additional Notes

### Why Vatican Does This
- Search API is fast (returns all ticket types)
- Timeavail API is slow (checks actual slot availability)
- Vatican uses `availability='AVAILABLE'` to mean "ticket type exists"
- Actual availability requires timeavail + residual check

### Performance Optimization
```python
# BEFORE (slow - calls timeavail even when sold out)
tickets = resolve_ticket_ids()
for ticket in tickets:
    slots = check_availability(ticket)  # Always calls API

# AFTER (fast - skips timeavail when search says sold out)
tickets = resolve_ticket_ids()
for ticket in tickets:
    if ticket['availability'] == 'SOLD_OUT':
        continue  # Skip API call
    slots = check_availability(ticket)  # Only call when needed
```

This optimization is already implemented in search_api_monitor.py line ~180.
The bug is that it doesn't check residual count in timeavail response.

---

## 🔗 Related Files

- `worker_vatican/search_api_monitor.py` - Main monitoring logic
- `backend/monitors/tasks.py` - Celery tasks & notifications
- `backend/monitors/notification_utils.py` - Telegram sending
- `backend/telegram_bot.py` - Bot commands & user management
- `check_may2_full.py` - Debug script for May 2
- `debug_may2_availability.py` - Comprehensive debug script

---

**Last Updated:** April 26, 2026
**Status:** Issues identified, fixes documented, ready for implementation
