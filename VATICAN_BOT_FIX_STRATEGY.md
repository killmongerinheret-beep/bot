# 🎯 Vatican Bot Fix Strategy

**Problem:** Bot waits for ticket elements to appear in HTML, but they never do because Vatican uses API calls to load tickets dynamically.

**Solution:** Don't wait for HTML elements. Just get cookies and call the API directly.

---

## Current (Broken) Flow

```
1. Navigate to deep link
2. Wait for cookies ✅
3. Wait for [data-cy^='bookTicket_'] elements ❌ TIMEOUT (15 seconds)
4. Try to extract IDs from HTML ❌ FAILS (0 IDs found)
5. Fall back to stale database ID ❌ WRONG
6. API call with stale ID ❌ 500 ERROR
7. Report "CLOSED" ❌ WRONG INFO
```

---

## Fixed Flow

```
1. Navigate to deep link
2. Wait for cookies ✅
3. Call Vatican API to get ticket IDs ✅ (no HTML parsing needed)
4. Use fresh IDs from API ✅
5. Call time availability API ✅
6. Report correct status ✅
```

---

## The Key Insight

Vatican's website is an Angular SPA. The tickets are NOT in the initial HTML. They're loaded via API calls:

```
GET /api/search/resultPerTag?lang=it&visitorNum=1&visitDate=16/03/2026&volumeId=1&tag=MV-Biglietti
```

This API returns:
```json
{
  "visits": [
    {
      "id": "2092730005",
      "name": "Musei Vaticani - Biglietti d'ingresso",
      "availability": "AVAILABLE"
    },
    ...
  ]
}
```

---

## What Needs to Change

### In `worker_vatican/hydra_monitor.py`

**Current code (lines ~750-780):**
```python
# Wait for ticket elements to render
await page.wait_for_selector("[data-cy^='bookTicket_']", state="visible", timeout=15000)
await page.wait_for_selector(".muvaTicketTitle", state="visible", timeout=5000)

# Extract IDs from HTML
ids = await page.evaluate('''() => {
    // Complex DOM parsing...
}''')
```

**Fixed code:**
```python
# Just wait for page to load and get cookies
await page.wait_for_load_state("networkidle")
await page.wait_for_timeout(2000)  # Let cookies settle

# Get cookies
cookies = await page.context.cookies()
jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)

# Call API directly to get ticket IDs
api_url = "https://tickets.museivaticani.va/api/search/resultPerTag"
params = {
    'lang': 'it',
    'visitorNum': visitors,
    'visitDate': target_date,
    'volumeId': 1,
    'tag': 'MV-Biglietti' if ticket_type == 0 else 'MV-Visite-Guidate'
}

# Use page.evaluate to call API with browser's cookies
ids = await page.evaluate(f'''
async () => {{
    const response = await fetch('{api_url}?' + new URLSearchParams({json.dumps(params)}));
    const data = await response.json();
    return data.visits.map(v => ({{
        id: v.id.toString(),
        name: v.name
    }}));
}}
''')
```

---

## Benefits

1. **No more timeouts** - Don't wait for HTML elements that never appear
2. **Always get fresh IDs** - API returns current ticket IDs
3. **Faster** - No need to wait 15+ seconds for timeouts
4. **More reliable** - API is the source of truth, not HTML
5. **Simpler code** - No complex DOM parsing

---

## Implementation Steps

1. Remove `wait_for_selector` for ticket elements
2. Add API call using `page.evaluate` with `fetch()`
3. Parse API response to get ticket IDs
4. Continue with existing flow (match by name, call time availability API)

---

## Why This Works

- The deep link navigation establishes the session and sets cookies
- The cookies are automatically included in `fetch()` calls from `page.evaluate()`
- The API returns the same data the Angular app uses
- No need to parse complex Angular-generated HTML

---

**Status:** Ready to implement
**Impact:** Fixes all "0 IDs found" issues
**Complexity:** Low - just replace HTML parsing with API call
