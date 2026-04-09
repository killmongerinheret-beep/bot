---
inclusion: always
priority: critical
---

# VATICAN BOT MANDATORY RULES
**CRITICAL: These rules MUST be followed for ALL Vatican ticket monitoring code**

---

## 🎯 CORE PRINCIPLE: ALWAYS USE SEARCH API

**NEVER use hardcoded ticket IDs.** Vatican changes IDs frequently (daily/weekly).

**ALWAYS use the Search API approach:**
1. Call search API to get fresh ticket IDs and JSESSIONID
2. Match tickets by name (not by ID)
3. Use fresh IDs for timeavail API calls

**WHY SEARCH API:**
- ✅ Works for ALL days (including Mondays)
- ✅ 10x faster than browser automation
- ✅ More reliable (no page rendering issues)
- ✅ Simpler code (no HTML parsing)
- ✅ Lower resource usage

---

## 📋 MANDATORY FLOW (2 STEPS - SIMPLIFIED)

### STEP 1: Call Search API (Get Ticket IDs + Session)

**URL:**
```
https://tickets.museivaticani.va/api/search/resultPerTag
```

**Parameters:**
- `lang` = API language (it, en, fr, de, es) - Usually "it"
- `visitorNum` = Number of visitors (MUST match task.visitors)
- `visitDate` = Date in DD/MM/YYYY format
- `area` = "1" (always 1)
- `who` = "" (empty string)
- `page` = "0" (first page)
- `tag` = "MV-Biglietti" (standard) OR "MV-Visite-Guidate" (guided tours)

**Example:**
```python
import requests

url = "https://tickets.museivaticani.va/api/search/resultPerTag"
params = {
    'lang': 'it',
    'visitorNum': '2',
    'visitDate': '28/03/2026',
    'area': '1',
    'who': '',
    'page': '0',
    'tag': 'MV-Biglietti'
}

headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://tickets.museivaticani.va/'
}

response = requests.get(url, params=params, headers=headers)
data = response.json()

# Extract tickets
tickets = []
for ticket in data.get('visits', []):
    tickets.append({
        'id': str(ticket['id']),
        'name': ticket.get('name', 'Unknown'),
        'availability': ticket.get('availability', 'UNKNOWN')
    })

# Extract JSESSIONID from cookies
jsessionid = response.cookies.get('JSESSIONID')
```

**What You Get:**
1. **JSESSIONID cookie** - Required for timeavail API
2. **Dynamic Ticket IDs** - Fresh IDs for the date/visitor combination
3. **Ticket Names** - Human-readable names for matching
4. **Availability Status** - AVAILABLE, SOLD_OUT, or NOT_ALLOWED

---

### STEP 2: Call Time Availability API

**URL:**
```
https://tickets.museivaticani.va/api/visit/timeavail
```

**Parameters:**
- `lang` = API language (it, en, fr, de, es) - Usually "it"
- `visitLang` = Tour language
  - **Standard tickets:** Empty string `""` (results in `&visitLang=`)
  - **Guided tours:** Language code (ENG, ITA, FRA, DEU, SPA)
- `visitTypeId` = Fresh ticket ID from Step 1
- `visitorNum` = Number of visitors (MUST match Step 1)
- `visitDate` = Date in DD/MM/YYYY format

**Required Headers:**
```python
headers = {
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://tickets.museivaticani.va/',
    'Cookie': f'JSESSIONID={jsessionid_from_step1}'
}
```

**Examples:**
```python
# Standard ticket (visitLang with EMPTY value)
url = "https://tickets.museivaticani.va/api/visit/timeavail"
params = {
    'lang': 'it',
    'visitLang': '',  # Empty for standard tickets
    'visitTypeId': '2085325042',
    'visitorNum': '1',
    'visitDate': '28/03/2026'
}

# Guided tour (visitLang with language code)
params = {
    'lang': 'it',
    'visitLang': 'ENG',  # Language code for guided tours
    'visitTypeId': '1594188966',
    'visitorNum': '1',
    'visitDate': '28/03/2026'
}

# Use session from Step 1 to maintain cookies
response = session.get(url, params=params, headers=headers)
data = response.json()

# Extract available slots
available_slots = [
    slot['time'] for slot in data['timetable'] 
    if slot.get('availability') != 'SOLD_OUT'
]
```

**Response Format:**
```json
{
  "timetable": [
    {"time": "09:00", "availability": "AVAILABLE"},
    {"time": "09:30", "availability": "SOLD_OUT"},
    {"time": "10:00", "availability": "AVAILABLE"}
  ]
}
```

---

## 🚫 COMMON MISTAKES TO AVOID

### ❌ WRONG: Using Stale Database IDs
```python
# BAD - ID from database is stale
ticket_id = task.ticket_id  # 1594188966 (old)
api_url = f"...visitTypeId={ticket_id}..."
# Result: API returns 500 error
```

### ✅ CORRECT: Always Resolve Fresh IDs via Search API
```python
# GOOD - Get fresh ID from search API
tickets = resolve_via_search_api(date, visitors, ticket_type)
fresh_id = match_ticket_by_name(tickets, task.ticket_name)
api_url = f"...visitTypeId={fresh_id}..."
# Result: API returns 200 with slots
```

---

### ❌ WRONG: Mismatched Visitor Count
```python
# BAD - Deep link uses 1 visitor, API uses 2
deep_url = f".../fromtag/1/{ts}/MV-Biglietti/1"
api_url = f"...visitorNum=2&visitDate=..."
# Result: Session mismatch, wrong availability
```

### ✅ CORRECT: Consistent Visitor Count
```python
# GOOD - Same visitor count everywhere
visitors = task.visitors  # e.g., 2
deep_url = f".../fromtag/{visitors}/{ts}/MV-Biglietti/1"
api_url = f"...visitorNum={visitors}&visitDate=..."
# Result: Accurate availability
```

---

### ❌ WRONG: Missing visitLang Parameter
```python
# BAD - Standard ticket without visitLang parameter
api_url = "...lang=it&visitTypeId=2129030053&visitorNum=2..."
# Result: May not work correctly - visitLang should always be included
```

### ✅ CORRECT: Always Include visitLang


```python
# GOOD - Standard ticket with empty visitLang
api_url = "...lang=it&visitLang=&visitTypeId=2129030053&visitorNum=2..."
# Result: Works correctly

# GOOD - Guided tour with visitLang value
api_url = "...lang=it&visitLang=ENG&visitTypeId=1594188966&visitorNum=1..."
# Result: Works correctly
```

### ✅ CORRECT: visitLang Always Included
```python
# GOOD - Standard ticket (visitLang with empty value)
if ticket_type == 0:
    visit_lang = ""
    api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang={visit_lang}&visitTypeId={id}&visitorNum={v}&visitDate={date}"

# GOOD - Guided tour (visitLang with language code)
if ticket_type == 1:
    visit_lang = language  # e.g., "ENG"
    api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang={visit_lang}&visitTypeId={id}&visitorNum={v}&visitDate={date}"

# GOOD - Simplified (works for both)
visit_lang = language if language else ""  # Empty string for standard, language code for guided
api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang={visit_lang}&visitTypeId={id}&visitorNum={v}&visitDate={date}"
```

---

### ❌ WRONG: Incorrect Timestamp Calculation
```python
# BAD - Using UTC instead of Rome timezone
dt = datetime(2026, 3, 28, 0, 0, 0)  # No timezone
ts = int(dt.timestamp() * 1000)
# Result: Off by 1-2 hours, wrong date
```

### ✅ CORRECT: Rome Timezone
```python
# GOOD - Explicit Rome timezone
from zoneinfo import ZoneInfo
rome = ZoneInfo("Europe/Rome")
dt = datetime(2026, 3, 28, 0, 0, 0, tzinfo=rome)
ts = int(dt.timestamp() * 1000)
# Result: Correct midnight Rome time
```

---

## 📝 SESSION CACHING RULES

**Cache Structure:**
```json
{
  "cookies": [
    {"name": "JSESSIONID", "value": "ABC123...", "domain": ".museivaticani.va"}
  ],
  "ids_cache": {
    "28/03/2026": [
      {"id": "2129030053", "name": "Palazzo Papale - Biglietti d'ingresso"},
      {"id": "1594188966", "name": "Specola Vaticana - Visita Guidata"}
    ]
  },
  "last_updated": "2026-02-28T14:30:00"
}
```

**Cache Validation:**
1. Check if JSESSIONID exists
2. Check if IDs exist for target date
3. Verify cache age < 12 hours
4. Test with lightweight API call

**When to Refresh:**
- No cached session
- JSESSIONID expired (API returns 401/403)
- No IDs for target date
- Cache older than 12 hours
- API returns 500 error (stale ID)

---

## 🔧 IMPLEMENTATION CHECKLIST

When writing/modifying Vatican bot code, verify:

- [ ] Deep link uses correct visitor count from task.visitors
- [ ] Timestamp calculated in Rome timezone
- [ ] Correct slug (MV-Biglietti vs MV-Visite-Guidate)
- [ ] Dynamic IDs extracted from page (not database)
- [ ] Ticket matched by NAME (3-tier strategy)
- [ ] Fresh ID used in API call
- [ ] visitLang parameter ALWAYS included in API URL
- [ ] visitLang is empty string for standard tickets (ticket_type == 0)
- [ ] visitLang has language code for guided tours (ticket_type == 1)
- [ ] Visitor count consistent (deep link == API call)
- [ ] Date format correct (DD/MM/YYYY for API)
- [ ] JSESSIONID cookie included in API request
- [ ] Available slots filtered (availability != 'SOLD_OUT')

---

## 🎯 FILE-SPECIFIC RULES

### backend/monitors/tasks.py
- `run_smart_vatican_monitor()` - MUST use HydraBot for dynamic ID resolution
- `run_god_tier_vatican_monitor()` - MUST validate session before API calls
- `orchestrate_all_tasks()` - MUST pass task.visitors to monitor functions

### worker_vatican/hydra_monitor.py
- `resolve_all_dynamic_ids()` - MUST navigate to deep link with correct visitors
- `check_via_click()` - MUST use fresh IDs from resolve_all_dynamic_ids()
- NEVER use GUIDED_TOUR_ID or STANDARD_TICKET_ID constants

### worker_vatican/god_tier_monitor.py
- `refresh_session_with_browser()` - MUST accept visitors parameter
- `check_availability_headless()` - MUST use visitors from function parameter
- `_rate_limited_request()` - MUST include JSESSIONID in cookies

---

## 🚨 ERROR HANDLING

### API Returns 500 Error
**Cause:** Stale ticket ID  
**Fix:** Clear ticket_id in database, force fresh resolution

### API Returns 401/403
**Cause:** Expired JSESSIONID  
**Fix:** Refresh session with browser

### No Slots Found (but should exist)
**Cause:** Wrong visitor count or date format  
**Fix:** Verify deep link matches API call parameters

### Name Matching Fails
**Cause:** Vatican changed ticket names  
**Fix:** Use keyword matching (Strategy 2) or fallback (Strategy 3)

---

## 📊 MONITORING & VALIDATION

**Success Indicators:**
- ✅ "Dynamic Match" or "Keyword Match" in logs
- ✅ API returns 200 status
- ✅ Slots found for available dates
- ✅ No "Falling back to stale ID" warnings

**Failure Indicators:**
- ❌ "No name match" warnings
- ❌ API returns 500 errors
- ❌ "Falling back to stale ID (Risky)"
- ❌ 0 slots found when availability exists

**Quick Validation:**
```bash
# Check recent logs for success
docker-compose logs worker_vatican | grep "Keyword Match\|Exact Match"

# Check for errors
docker-compose logs worker_vatican | grep "500\|No name match\|stale ID"
```

---

## 🔄 WHEN VATICAN CHANGES STRUCTURE

If Vatican changes their website structure:

1. **Update Deep Link Pattern** - Check if URL format changed
2. **Update ID Extraction** - Check if data-cy attributes changed
3. **Update API Endpoint** - Check if /api/visit/timeavail moved
4. **Update Ticket Names** - Add new keywords to matching logic
5. **Test with Browser** - Manually verify flow works
6. **Update This Document** - Keep rules current

---

## 📚 REFERENCE IMPLEMENTATIONS

**Correct Implementation Example:**
See `backend/monitors/tasks.py` lines 220-270 (3-tier matching)
See `worker_vatican/hydra_monitor.py` resolve_all_dynamic_ids()

**Test Command:**
```python
# Test fresh ID resolution
from worker_vatican.hydra_monitor import HydraBot
import asyncio

async def test():
    bot = HydraBot(use_proxies=True)
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        ids = await bot.resolve_all_dynamic_ids(
            page, 
            ticket_type=0, 
            target_date="28/03/2026",
            visitors=2
        )
        print(f"Found {len(ids)} tickets:")
        for item in ids:
            print(f"  {item['id']}: {item['name']}")

asyncio.run(test())
```

---

**LAST UPDATED:** February 28, 2026  
**VERSION:** 2.0  
**STATUS:** MANDATORY - DO NOT DEVIATE FROM THESE RULES
