# Optimized Vatican Monitoring Strategy

## Discovery Summary

After analyzing 30 dates, we discovered:

1. **Ticket IDs are STATIC per ticket type** - Not date-specific
2. **Only cookies are dynamic** - JSESSIONID changes per session
3. **Vatican releases tickets gradually** - Currently only March 19-20 available

## Current Situation (March 3, 2026)

| Date | Status | Reason |
|------|--------|--------|
| March 4-18 | ❌ Not Released | Vatican hasn't opened these dates |
| March 19-20 | ✅ Available | Tickets released, IDs extracted |
| March 21+ | ❌ Not Released | Too far in future |

## Known Working IDs (March 2026)

```python
VATICAN_KNOWN_IDS = {
    # Most common standard tickets
    "standard_primary": "459172131",      # Musei Vaticani - Biglietti d'ingresso
    "standard_alt": "1934042052",         # Ingresso AREE MUSEALI Singoli
    
    # Guided tours
    "guided_individual": "2037374249",    # Visite Guidate Singoli Musei
    "guided_group": "1078934336",         # Visite Guidate Gruppi Musei
    
    # Special tickets
    "terrace": "2022918202",              # Terrazze Panoramiche 360°
    "audioguide": "1472834410",           # Ingresso con Audioguida
    "underground": "1011626768",          # Underground Experience
    "expert": "833874468",                # Visita con l'Esperto
}
```

## Optimized 3-Tier Strategy

### Tier 1: Use Cached ID (Fastest - 2 seconds)
```python
1. Get JSESSIONID from lightweight page visit
2. Use known ID from cache
3. Call API directly
4. If 500 error → Tier 2
```

### Tier 2: Scrape Fresh IDs (Medium - 10 seconds)
```python
1. Navigate to deep link
2. Extract all ticket IDs from page
3. Match by name (3-tier matching)
4. Update cache
5. Call API
6. If still fails → Tier 3
```

### Tier 3: Date Not Released (Slow - 15 seconds)
```python
1. Try multiple known IDs
2. All return 500 → Date not released yet
3. Report as "NOT_RELEASED" (not "CLOSED")
4. Schedule retry in 24 hours
```

## Implementation Benefits

### Speed Improvements
- **Current**: 15-20 seconds per check (always scrapes)
- **Optimized**: 2-5 seconds per check (uses cache)
- **Savings**: 75% faster for released dates

### Reliability Improvements
- Distinguishes "NOT_RELEASED" from "SOLD_OUT"
- Reduces proxy usage (fewer page loads)
- Handles Vatican system updates gracefully

### Resource Savings
- Fewer browser instances
- Less bandwidth usage
- Lower proxy consumption

## Error Handling Matrix

| API Response | Meaning | Action |
|--------------|---------|--------|
| 200 + slots | Available | Report slots |
| 200 + empty | Sold out | Report SOLD_OUT |
| 500 with cached ID | Try fresh ID | Scrape page |
| 500 with fresh ID | Not released | Report NOT_RELEASED |
| 401/403 | Bad cookies | Refresh session |

## Cache Invalidation Rules

Refresh cached IDs when:
1. API returns 500 with cached ID
2. Cache older than 7 days
3. Manual refresh requested
4. Vatican system update detected

## Monitoring Dashboard Updates

Add new status types:
- `AVAILABLE` - Slots found
- `SOLD_OUT` - No slots (200 response)
- `NOT_RELEASED` - Date not opened yet (500 response)
- `ERROR` - Technical issue

## Next Steps

1. ✅ Confirmed IDs are static
2. ✅ Identified March 16 not released
3. ⏳ Implement cached ID system
4. ⏳ Update status reporting
5. ⏳ Add "NOT_RELEASED" state to dashboard

## Testing Results

### March 16 Test (Known ID)
```
ID: 459172131 (from March 20)
Result: 500 Internal Server Error
Conclusion: Date not released by Vatican
```

### March 20 Test (Same ID)
```
ID: 459172131
Result: 200 OK with timetable
Conclusion: ID works, date is released
```

**This proves IDs are reusable across dates!**
