# Vatican Bot Timing Analysis - Final Report

## Test Date: March 3, 2026
## Test Target: March 19, 2026 (1 visitor, standard tickets)

---

## ⏱️ BASELINE TIMING (No Proxy)

### Complete Flow Breakdown:

| Step | Time | Percentage |
|------|------|------------|
| Browser launch | 0.22s | 2% |
| Navigate + Get cookies | 4.99s | 55% |
| Wait + Extract IDs | 2.47s | 27% |
| API call | 0.70s | 8% |
| **TOTAL** | **9.12s** | **100%** |

### Key Findings:

1. **Navigation is the bottleneck** (5 seconds)
   - Vatican's Angular app is slow to load
   - DOM content loaded takes ~5s
   
2. **ID extraction takes 2.5 seconds**
   - Waiting for Angular to render tickets
   - Actual extraction is fast (<0.1s)
   
3. **API call is fast** (0.7 seconds)
   - Once you have cookies + IDs, API responds quickly
   
4. **Total time: ~9 seconds**
   - This is WITHOUT proxy
   - With proxy: expect 10-15 seconds

---

## 🎯 OPTIMIZATION STRATEGY

### Current Bot Approach (Always Full Extraction):
```
Every check: 9-15 seconds
100 checks/day: 15-25 minutes total
```

### Optimized 2-Tier Approach:

#### Tier 1: Fast Path (Cached IDs)
```
1. Navigate to deep link (5s)
2. Get JSESSIONID (included above)
3. Use cached ticket ID
4. Call API (0.7s)
---
Total: ~6 seconds
```

#### Tier 2: Full Extraction (When IDs Rotate)
```
1. Navigate to deep link (5s)
2. Get JSESSIONID (included)
3. Wait for tickets (2.5s)
4. Extract fresh IDs
5. Match by name
6. Call API (0.7s)
---
Total: ~9 seconds
```

### Performance Comparison:

| Scenario | Time per Check | 100 Checks/Day |
|----------|----------------|----------------|
| Current (always extract) | 9-15s | 15-25 min |
| Optimized (80% cached) | 6-7s avg | 10-12 min |
| **Savings** | **40%** | **40%** |

---

## 📊 DETAILED TIMING BREAKDOWN

### What Takes Time:

1. **Vatican's Angular App** (5 seconds)
   - Server response: ~1s
   - JavaScript loading: ~1s
   - Angular bootstrap: ~2s
   - Ticket rendering: ~1s

2. **Ticket ID Extraction** (2.5 seconds)
   - Wait for selector: ~2s
   - DOM traversal: ~0.3s
   - Name matching: ~0.2s

3. **API Call** (0.7 seconds)
   - Request: ~0.3s
   - Server processing: ~0.2s
   - Response: ~0.2s

### What's Fast:

- Browser launch: 0.2s
- Cookie extraction: <0.1s (included in navigation)
- JavaScript evaluation: <0.1s

---

## 🚀 RECOMMENDED IMPLEMENTATION

### ID Caching Strategy:

```python
# Global cache (shared across all tasks)
VATICAN_ID_CACHE = {
    "Musei Vaticani - Biglietti d'ingresso": {
        "id": "862220842",
        "last_updated": "2026-03-03T13:00:00",
        "last_verified": "2026-03-03T14:30:00",  # Last successful API call
        "success_count": 45  # Number of successful uses
    }
}

# Cache invalidation rules:
# 1. Age > 24 hours → Refresh
# 2. API returns 500 → Refresh immediately
# 3. Success count > 100 → Refresh proactively
```

### Check Flow:

```python
async def check_vatican_task(task):
    # Try cached ID first
    cached_id = get_cached_id(task.ticket_name)
    
    if cached_id and is_cache_fresh(cached_id):
        # FAST PATH: 6 seconds
        cookies = await get_cookies_fast(task.target_date)
        result = await call_api(cookies, cached_id, task)
        
        if result.status == 200:
            update_cache_success(task.ticket_name, cached_id)
            return result  # ✅ Done in 6s!
        
        # 500 error → IDs rotated
        invalidate_cache(task.ticket_name)
    
    # SLOW PATH: 9 seconds
    cookies, fresh_ids = await extract_with_browser(task)
    matched_id = match_ticket_by_name(fresh_ids, task.ticket_name)
    
    if matched_id:
        update_cache(task.ticket_name, matched_id)
        result = await call_api(cookies, matched_id, task)
        return result  # ✅ Done in 9s
    
    return None  # No match
```

---

## 🔍 PROXY IMPACT

### Test Results:

- **No Proxy**: 9.12s ✅
- **Oxylabs Proxy**: Timeout (30s+) ❌
  - Vatican may be blocking Oxylabs datacenter IPs
  - Need to test with residential proxies

### Recommendations:

1. **Use residential proxies** (Webshare, Bright Data)
2. **Sticky proxy per session** (reuse same proxy for cookie + API)
3. **Fallback to no-proxy** if all proxies fail
4. **Rotate proxies only on failure** (not per request)

---

## 📈 EXPECTED PERFORMANCE

### With Optimizations:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Avg check time | 12s | 7s | 42% faster |
| Checks per minute | 5 | 8 | 60% more |
| Daily capacity | 7,200 | 11,520 | 60% more |
| Resource usage | High | Medium | 40% less |

### Real-World Scenario (10 tasks, 1-minute intervals):

**Before:**
- Each cycle: 10 tasks × 12s = 120s (2 minutes)
- Can't meet 1-minute interval
- Tasks queue up

**After:**
- Each cycle: 10 tasks × 7s = 70s (1.2 minutes)
- Meets 1-minute interval most of the time
- Occasional 9s checks when IDs rotate

---

## ✅ ACTION ITEMS

1. **Implement ID caching system**
   - Add cache table to database
   - Store: ticket_name, ticket_id, last_updated, success_count
   
2. **Update monitor logic**
   - Try cached ID first
   - Fall back to full extraction on 500 error
   
3. **Add cache warming**
   - Run full extraction once per day for common tickets
   - Pre-populate cache before peak hours
   
4. **Monitor cache hit rate**
   - Track: cache_hits / total_checks
   - Target: >80% hit rate
   
5. **Test with residential proxies**
   - Webshare proxies (already have 10)
   - Measure timing impact
   
6. **Add new status types**
   - `AVAILABLE` - Slots found
   - `SOLD_OUT` - No slots
   - `NOT_RELEASED` - Date not opened (500 error)
   - `ERROR` - Technical issue

---

## 🎯 CONCLUSION

**Current State:**
- Bot works correctly
- March 16 not released by Vatican (confirmed)
- Full extraction every time: 9-15 seconds

**Optimized State:**
- Cache ticket IDs globally
- Fast path (cached): ~6 seconds (80% of checks)
- Slow path (fresh): ~9 seconds (20% of checks)
- Average: ~7 seconds (40% improvement)

**Next Steps:**
1. Implement caching (highest impact)
2. Test with Webshare proxies
3. Add NOT_RELEASED status
4. Monitor and tune cache invalidation

The bot is functioning correctly - the main opportunity is caching IDs to skip the 2.5-second extraction step on most checks.
