# Task Grouping Logic Explanation

## Your Question: "How does checking names reduce duplicates if Search API is pingable?"

You're right to question this! Let me explain the actual problem and solution.

## The Real Problem

### Scenario:
```
Agency A: Monitoring "Musei Vaticani" for March 28, ticket_id=123 (old)
Agency B: Monitoring "Musei Vaticani" for March 28, ticket_id=456 (new)
Agency C: Monitoring "Musei Vaticani" for March 28, ticket_id=789 (newer)
```

### OLD Grouping (by ticket_id):
```python
key = (date, task.ticket_id, task.language, task.visitors)

# Results in 3 separate groups:
Group 1: (28/03/2026, 123, None, 2) -> [Agency A]
Group 2: (28/03/2026, 456, None, 2) -> [Agency B]  
Group 3: (28/03/2026, 789, None, 2) -> [Agency C]

# Dispatches 3 separate API calls:
1. Check ticket 123 for March 28 (Search API resolves to fresh ID)
2. Check ticket 456 for March 28 (Search API resolves to fresh ID)
3. Check ticket 789 for March 28 (Search API resolves to fresh ID)
```

**Result:** 3 API calls for the SAME ticket!

### NEW Grouping (by ticket_name):
```python
key = (date, task.ticket_name, task.language, task.visitors)

# Results in 1 group:
Group 1: (28/03/2026, "Musei Vaticani", None, 2) -> [Agency A, Agency B, Agency C]

# Dispatches 1 API call:
1. Check "Musei Vaticani" for March 28 (Search API resolves once)
   -> Notifies all 3 agencies
```

**Result:** 1 API call for all agencies!

## Why This Matters

### Search API Flow:
```
1. Call Search API -> Get fresh ticket IDs
2. Match by name -> Find correct ticket
3. Call timeavail API -> Get slots
4. Notify all agencies in the group
```

Even though Search API is "pingable" (fast), we still want to:
- **Reduce API calls** (respect rate limits)
- **Save proxy bandwidth** (proxies cost money)
- **Faster response** (1 check vs 3 checks)
- **Lower server load** (Vatican's servers)

## Example with Real Data

### Scenario: 10 agencies monitoring same ticket

**OLD (group by ticket_id):**
```
Agency 1: ticket_id=111 (stale)
Agency 2: ticket_id=222 (stale)
Agency 3: ticket_id=333 (stale)
Agency 4: ticket_id=444 (stale)
Agency 5: ticket_id=555 (current)
Agency 6: ticket_id=555 (current)
Agency 7: ticket_id=666 (newer)
Agency 8: ticket_id=666 (newer)
Agency 9: ticket_id=777 (newest)
Agency 10: ticket_id=777 (newest)

Groups: 7 different ticket_ids
API Calls: 7 (one per unique ticket_id)
```

**NEW (group by ticket_name):**
```
All agencies: "Musei Vaticani - Biglietti d'ingresso"

Groups: 1 (same name)
API Calls: 1 (shared across all agencies)
```

**Savings:** 7 API calls → 1 API call = **86% reduction**

## Why ticket_id Changes

Vatican rotates ticket IDs frequently:
- **Daily:** IDs change for some tickets
- **Weekly:** IDs change for most tickets
- **Per visitor count:** Different IDs for 1 vs 2 visitors
- **Per date:** Sometimes different IDs for different dates

So even if you update ticket_id today, it might be stale tomorrow.

## The Solution

Group by **stable identifiers**:
- ✅ `ticket_name` - Never changes
- ✅ `date` - Stable
- ✅ `language` - Stable
- ✅ `visitors` - Stable

Don't group by **unstable identifiers**:
- ❌ `ticket_id` - Changes frequently

## Current Implementation

```python
# Orchestrator groups tasks
for task in tasks:
    for date in task.dates:
        # Group by stable identifiers
        key = (date, task.ticket_name, task.language, task.visitors)
        
        if key not in task_groups:
            task_groups[key] = {
                'date': date,
                'ticket_name': task.ticket_name,  # Used for matching
                'ticket_id': task.ticket_id,      # Ignored (just for reference)
                'language': task.language,
                'visitors': task.visitors,
                'task_ids': []
            }
        
        task_groups[key]['task_ids'].append(task.id)

# Dispatch one check per group
for group in task_groups.values():
    run_search_api_vatican_monitor.delay(
        date=group['date'],
        ticket_name=group['ticket_name'],  # ✅ Used for Search API matching
        ticket_id=group['ticket_id'],      # ❌ Ignored (stale)
        language=group['language'],
        visitors=group['visitors'],
        task_ids=group['task_ids']         # All agencies in this group
    )
```

## Inside the Monitor

```python
def run_search_api_vatican_monitor(date, ticket_name, ticket_id, ...):
    # Step 1: Call Search API to get fresh IDs
    fresh_tickets = monitor.resolve_ticket_ids(date, visitors, ticket_type)
    # Returns: [
    #   {'id': '2129030053', 'name': 'Musei Vaticani - Biglietti d\'ingresso'},
    #   {'id': '1594188966', 'name': 'Specola Vaticana - Visita Guidata'},
    #   ...
    # ]
    
    # Step 2: Match by name (ignore passed ticket_id)
    fresh_id = match_ticket_by_name(fresh_tickets, ticket_name)
    # Finds: '2129030053' (fresh ID for today)
    
    # Step 3: Check availability with fresh ID
    success, slots = monitor.check_availability(fresh_id, date, visitors)
    
    # Step 4: Notify ALL agencies in task_ids
    for task_id in task_ids:
        # Send notification if slots found
        ...
```

## Performance Impact

### Before (group by ticket_id):
```
10 agencies, same ticket, different stale IDs
→ 7 unique ticket_ids
→ 7 API calls
→ 7 × 2 seconds = 14 seconds total
```

### After (group by ticket_name):
```
10 agencies, same ticket, same name
→ 1 unique ticket_name
→ 1 API call
→ 1 × 2 seconds = 2 seconds total
```

**Result:** 7× faster, 86% fewer API calls

## Why Not Just Update ticket_id?

Even if we update ticket_id in the database:
1. **Race condition:** Multiple workers might update simultaneously
2. **Stale immediately:** Vatican changes IDs frequently
3. **Maintenance burden:** Need to constantly refresh
4. **Still duplicates:** Between updates, still have stale IDs

**Better solution:** Don't rely on ticket_id at all. Use ticket_name (stable) and resolve fresh ID every time via Search API.

## Summary

**Question:** "How does checking names reduce duplicates if Search API is pingable?"

**Answer:** 
- Grouping by `ticket_name` combines multiple agencies monitoring the SAME ticket
- Without grouping, each agency triggers a separate API call
- With grouping, one API call serves all agencies
- Even though Search API is fast, reducing calls is still beneficial:
  - Respects rate limits
  - Saves proxy bandwidth
  - Faster overall response
  - Lower server load

**Analogy:**
- OLD: 10 people each call the restaurant to check if table is available
- NEW: 1 person calls, then tells all 10 people the answer

Both work, but NEW is more efficient!
