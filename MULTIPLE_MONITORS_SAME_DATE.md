# Multiple Monitors for Same Date - Explained

## Quick Answer

**YES and NO** - It depends on what you mean by "different time":

### ✅ YES - You Can Have Multiple Monitors for Same Date If:

1. **Different Visitor Counts**
   ```
   Task 1: April 15, 2026 - 1 visitor
   Task 2: April 15, 2026 - 2 visitors
   Task 3: April 15, 2026 - 4 visitors
   ```
   ✅ These are DIFFERENT checks (different API calls)
   ✅ Each gets checked separately
   ✅ No duplication - system is smart!

2. **Different Ticket Types**
   ```
   Task 1: April 15, 2026 - Standard Ticket
   Task 2: April 15, 2026 - Guided Tour (English)
   Task 3: April 15, 2026 - Guided Tour (Italian)
   ```
   ✅ These are DIFFERENT tickets
   ✅ Each gets checked separately

3. **Different Agencies**
   ```
   Agency A: April 15, 2026 - 1 visitor
   Agency B: April 15, 2026 - 1 visitor
   ```
   ✅ System checks ONCE and notifies BOTH agencies
   ✅ Ultra-efficient (smart grouping)

### ❌ NO - You CANNOT Have Multiple Monitors for:

**Same Date + Same Visitors + Same Ticket Type**
```
Task 1: April 15, 2026 - 1 visitor - preferred_times: ['09:00', '10:00']
Task 2: April 15, 2026 - 1 visitor - preferred_times: ['14:00', '15:00']
```
❌ This is REDUNDANT - the bot checks ALL available slots anyway!

---

## How It Actually Works

### The Bot Checks ALL Time Slots Automatically ✅

When the bot checks a date, it gets **ALL available time slots** from Vatican:

```json
{
  "timetable": [
    {"time": "08:30", "availability": "AVAILABLE"},
    {"time": "09:00", "availability": "AVAILABLE"},
    {"time": "09:30", "availability": "SOLD_OUT"},
    {"time": "10:00", "availability": "AVAILABLE"},
    {"time": "10:30", "availability": "AVAILABLE"},
    {"time": "11:00", "availability": "AVAILABLE"},
    {"time": "11:30", "availability": "SOLD_OUT"},
    {"time": "12:00", "availability": "AVAILABLE"},
    {"time": "12:30", "availability": "AVAILABLE"},
    {"time": "13:00", "availability": "AVAILABLE"},
    {"time": "13:30", "availability": "AVAILABLE"},
    {"time": "14:00", "availability": "AVAILABLE"},
    {"time": "14:30", "availability": "SOLD_OUT"},
    {"time": "15:00", "availability": "AVAILABLE"},
    {"time": "15:30", "availability": "AVAILABLE"},
    {"time": "16:00", "availability": "AVAILABLE"}
  ]
}
```

**The bot returns ALL available slots, not just your preferred times!**

### Preferred Times = Filter for Notifications

The `preferred_times` field is used to **filter which slots trigger alerts**, not which slots to check:

```python
# Example Task
preferred_times = ['09:00', '10:00', '14:00', '15:00']

# Bot checks and finds these available:
all_available = ['08:30', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']

# Notification logic:
if any(time in preferred_times for time in all_available):
    send_alert("Your preferred times are available!")
    # Shows: 09:00, 10:00, 14:00, 15:00
else:
    # Still logs all available slots, just doesn't alert
    log("Available but not preferred: 08:30, 11:00, 12:00, 13:00, 16:00")
```

---

## Smart Grouping System

### How the System Optimizes Checks

The orchestrator groups tasks by `(date, ticket_id, language, visitors)`:

```python
# Example: 3 agencies want same date/ticket/visitors
Agency A: April 15, 2026 - 1 visitor - preferred: ['09:00', '10:00']
Agency B: April 15, 2026 - 1 visitor - preferred: ['14:00', '15:00']
Agency C: April 15, 2026 - 1 visitor - preferred: ['16:00']

# System groups them:
Group Key: (2026-04-15, ticket_123, None, 1)
Task IDs: [A, B, C]

# Checks ONCE:
✅ Navigate to Vatican (7s)
✅ Get ALL time slots (0.5s)
✅ Found: ['08:30', '09:00', '10:00', '11:00', '14:00', '15:00', '16:00']

# Notifies ALL agencies:
✅ Agency A: Alert! (09:00, 10:00 available)
✅ Agency B: Alert! (14:00, 15:00 available)
✅ Agency C: Alert! (16:00 available)

# Total time: 7.5 seconds for 3 agencies!
```

### What Creates Separate Checks

Only these differences create separate checks:

1. **Different Dates**
   ```
   April 15 vs April 16 = 2 separate checks
   ```

2. **Different Visitor Counts**
   ```
   1 visitor vs 2 visitors = 2 separate checks
   (Vatican API returns different availability)
   ```

3. **Different Ticket Types**
   ```
   Standard vs Guided Tour = 2 separate checks
   ```

4. **Different Languages (for guided tours)**
   ```
   English vs Italian guided tour = 2 separate checks
   ```

---

## Practical Examples

### ✅ GOOD: Multiple Visitor Counts

```
Task 1: April 15, 2026 - 1 visitor
Task 2: April 15, 2026 - 2 visitors
Task 3: April 15, 2026 - 4 visitors
```

**Why this makes sense:**
- Vatican has different availability for different group sizes
- 1 visitor might have 20 slots available
- 4 visitors might have only 10 slots available
- These are genuinely different checks

**System behavior:**
- 3 separate API calls
- Each returns different availability
- Each can trigger separate alerts

### ❌ BAD: Duplicate Same Configuration

```
Task 1: April 15, 2026 - 1 visitor - preferred: ['09:00']
Task 2: April 15, 2026 - 1 visitor - preferred: ['14:00']
```

**Why this is redundant:**
- Both tasks check the SAME date/visitors/ticket
- Bot gets ALL slots in one check anyway
- Just wastes database space
- No benefit over one task with both times

**Better approach:**
```
Task 1: April 15, 2026 - 1 visitor - preferred: ['09:00', '14:00']
```

### ✅ GOOD: Different Agencies

```
Agency A: April 15, 2026 - 1 visitor
Agency B: April 15, 2026 - 1 visitor
```

**Why this makes sense:**
- Different agencies need separate notifications
- System checks ONCE, notifies BOTH
- Ultra-efficient (smart grouping)

**System behavior:**
- 1 API call
- 2 notifications (one per agency)
- Optimal efficiency

---

## What You Should Do

### For 35 Dates Monitoring

**Option 1: One Task Per Date (Recommended)**
```
Task 1: April 15, 2026 - 1 visitor - preferred: ['09:00', '10:00', '14:00', '15:00']
Task 2: April 16, 2026 - 1 visitor - preferred: ['09:00', '10:00', '14:00', '15:00']
...
Task 35: May 20, 2026 - 1 visitor - preferred: ['09:00', '10:00', '14:00', '15:00']
```

**Benefits:**
- ✅ Clean and organized
- ✅ One check per date
- ✅ Gets ALL available slots
- ✅ Filters by preferred times for alerts
- ✅ Minimal system load

**Option 2: Multiple Visitor Counts (If Needed)**
```
Task 1: April 15, 2026 - 1 visitor
Task 2: April 15, 2026 - 2 visitors
Task 3: April 15, 2026 - 4 visitors
```

**Benefits:**
- ✅ Covers different group sizes
- ✅ Each is a genuine different check
- ✅ Useful if you need flexibility

**System Load:**
- 35 dates × 3 visitor counts = 105 checks
- Still within capacity (85+ dates at 60s interval)
- Would use ~123% capacity (need to optimize)

---

## Capacity Calculation

### Current Setup (35 dates, 1 visitor count each)
```
Dates: 35
Visitor variants: 1
Total checks: 35
Capacity used: 41%
✅ Plenty of headroom
```

### If You Add Multiple Visitor Counts
```
Dates: 35
Visitor variants: 3 (1, 2, 4 visitors)
Total checks: 105
Capacity used: 123%
⚠️ Over capacity - need optimization
```

**Solutions if over capacity:**
1. Reduce check_interval to 90s (instead of 60s)
2. Add 10 more proxies
3. Increase parallel workers to 15
4. Only monitor critical visitor counts

---

## Notification Strategy

### Match Strategy Options

**1. ANY (Default)**
```python
match_strategy = 'any'
# Alert if ANY preferred time is available
# Example: If 09:00 OR 10:00 OR 14:00 is available → Alert
```

**2. ALL**
```python
match_strategy = 'all'
# Alert only if ALL preferred times are available
# Example: Only alert if 09:00 AND 10:00 AND 14:00 are ALL available
```

### Notification Mode Options

**1. available_only (Recommended)**
```python
notification_mode = 'available_only'
# Only alert when tickets become available
# No alerts when sold out
```

**2. any_change**
```python
notification_mode = 'any_change'
# Alert on any status change (available → sold_out, sold_out → available)
```

**3. silent**
```python
notification_mode = 'silent'
# No alerts, just log status
# Useful for monitoring without notifications
```

---

## Best Practice Recommendations

### ✅ Recommended Setup

**For 35 dates with flexible time preferences:**
```python
# One task per date
for date in your_35_dates:
    MonitorTask.objects.create(
        dates=[date],
        visitors=1,  # or your preferred count
        preferred_times=['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
        match_strategy='any',  # Alert if ANY time is available
        notification_mode='available_only',  # Only alert when available
        check_interval=60
    )
```

**Benefits:**
- ✅ Gets ALL available slots
- ✅ Alerts for any preferred time
- ✅ Minimal system load
- ✅ Easy to manage

### ⚠️ Advanced Setup (If You Need Multiple Visitor Counts)

**Only if you genuinely need different group sizes:**
```python
visitor_counts = [1, 2, 4]  # Different group sizes

for date in your_35_dates:
    for visitors in visitor_counts:
        MonitorTask.objects.create(
            dates=[date],
            visitors=visitors,
            preferred_times=['09:00', '10:00', '14:00', '15:00'],
            match_strategy='any',
            notification_mode='available_only',
            check_interval=90  # Slower to handle load
        )
```

**Considerations:**
- ⚠️ 3x more checks (105 total)
- ⚠️ Need to increase check_interval to 90s
- ⚠️ Or add more proxies
- ✅ Useful if you need flexibility in group size

---

## Summary

### Can You Add Multiple Monitors for Same Date?

**YES, if:**
- ✅ Different visitor counts (1 vs 2 vs 4)
- ✅ Different ticket types (standard vs guided)
- ✅ Different agencies (smart grouping)

**NO, if:**
- ❌ Same date + same visitors + different preferred times
- ❌ This is redundant - bot checks ALL slots anyway!

### Key Insight

**The bot ALWAYS checks ALL available time slots for a date.**

Your `preferred_times` field is just a **filter for notifications**, not a filter for what gets checked.

So there's **no benefit** to creating multiple tasks for the same date/visitors/ticket just to monitor different times - one task with multiple preferred times does the same thing!

### Recommended Approach

**For 35 dates:**
- Create 35 tasks (one per date)
- Set preferred_times to ALL times you care about
- Let the bot check ALL slots
- Get alerts when ANY preferred time is available

**This is the most efficient and gives you complete coverage!** ✅
