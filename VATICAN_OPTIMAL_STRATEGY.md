# Vatican Optimal Monitoring Strategy

## Benchmark Results (March 3, 2026)

### Timing Analysis

| Strategy | Time | Success Rate | Gets IDs |
|----------|------|--------------|----------|
| Cookie only | ~2s | 100% | ❌ No |
| DOM + 3s wait | ~6s | 67% | ⚠️ Unreliable |
| DOM + 8s wait | ~13s | 100% | ✅ Yes |
| Smart selector wait | ~10s | 100% | ✅ Yes |

### Key Findings

1. **Cookie acquisition is fast**: 1-2 seconds
2. **Angular rendering is slow**: 8-10 seconds for tickets to appear
3. **Smart waiting is optimal**: Wait for selector instead of fixed time
4. **IDs are reusable**: Same IDs work for hours/days

## Recommended 2-Tier Strategy

### Tier 1: Fast Path (2-3 seconds total)
```python
1. Get JSESSIONID (2s)
2. Use cached ticket ID
3. Call API
4. If 200 OK → Done! ✅
5. If 500 Error → Go to Tier 2
```

**When to use**: Every check (try first)
**Success rate**: ~80% (when IDs haven't rotated)
**Time**: 2-3 seconds

### Tier 2: Full Extraction (10-12 seconds total)
```python
1. Navigate to deep link
2. Wait for selector: div[id^="ticket_"]
3. Extract all ticket IDs
4. Update cache
5. Match ticket by name
6. Call API
```

**When to use**: When Tier 1 fails (500 error)
**Success rate**: 100%
**Time**: 10-12 seconds

## Implementation Pattern

```python
async def check_vatican_availability(task):
    # Tier 1: Try cached ID (FAST)
    cached_id = get_cached_id(task.ticket_name)
    
    if cached_id:
        jsessionid = await get_cookie_fast(task.target_date)  # 2s
        result = await call_api(jsessionid, cached_id, task)  # 1s
        
        if result.status == 200:
            return result  # SUCCESS in 3s!
        
        # 500 error → IDs rotated, go to Tier 2
    
    # Tier 2: Full extraction (SLOW but reliable)
    jsessionid, fresh_ids = await extract_ids_with_wait(task)  # 10s
    matched_id = match_ticket_by_name(fresh_ids, task.ticket_name)
    
    if matched_id:
        update_cache(task.ticket_name, matched_id)
        result = await call_api(jsessionid, matched_id, task)  # 1s
        return result  # SUCCESS in 11s
    
    return None  # No match found
```

## Cache Strategy

### What to Cache
```python
VATICAN_ID_CACHE = {
    "ticket_name": {
        "id": "862220842",
        "last_updated": "2026-03-03T13:00:00",
        "last_verified": "2026-03-03T13:45:00"
    }
}
```

### Cache Invalidation Rules
1. **Age-based**: Refresh if older than 24 hours
2. **Error-based**: Refresh immediately on 500 error
3. **Success-based**: Update `last_verified` on 200 OK

### Cache Warming
- Run full extraction once per day for common tickets
- Store IDs globally (not per-date)
- Share cache across all monitor tasks

## Performance Comparison

### Current Implementation (Always Full Extraction)
- Every check: 15-20 seconds
- 100 checks/day: 25-33 minutes total

### Optimized Implementation (2-Tier)
- 80% fast path (3s): 240 seconds
- 20% slow path (11s): 220 seconds
- 100 checks/day: **7.7 minutes total**

**Savings: 70% faster!**

## Error Handling

| Error | Meaning | Action |
|-------|---------|--------|
| 500 with cached ID | IDs rotated | Go to Tier 2 |
| 500 with fresh ID | Date not released | Report NOT_RELEASED |
| 401/403 | Cookie expired | Refresh cookie |
| Timeout | Vatican slow | Retry with longer timeout |

## Status Reporting

Add new status types:
- `AVAILABLE` - Slots found (200 OK + slots)
- `SOLD_OUT` - No slots (200 OK + empty)
- `NOT_RELEASED` - Date not opened (500 error)
- `ERROR` - Technical issue

## Next Steps

1. ✅ Benchmark completed
2. ⏳ Implement ID caching system
3. ⏳ Update monitor to use 2-tier strategy
4. ⏳ Add NOT_RELEASED status to database
5. ⏳ Update dashboard to show new statuses

## Testing Results

March 19, 2026 (has tickets):
- Strategy 1 (cookie only): 2.07s avg ✅
- Strategy 4 (smart wait): 9.97s avg ✅ (10 IDs extracted)

**Conclusion**: 2-tier approach will reduce average check time from 15s to 3-4s (75% improvement)
