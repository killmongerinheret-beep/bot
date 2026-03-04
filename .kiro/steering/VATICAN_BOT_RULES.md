---
inclusion: always
priority: critical
---

# VATICAN BOT MANDATORY RULES
**CRITICAL: These rules MUST be followed for ALL Vatican ticket monitoring code**

---

## 🎯 CORE PRINCIPLE: ALWAYS USE DYNAMIC IDs

**NEVER use hardcoded ticket IDs.** Vatican changes IDs frequently (daily/weekly).

**ALWAYS:**
1. Navigate to deep link to get fresh JSESSIONID cookies
2. Extract dynamic ticket IDs from the page
3. Use those fresh IDs for API calls

---

## 📋 MANDATORY FLOW (3 STEPS)

### STEP 1: Navigate to Deep Link (Get Cookies + IDs)

**URL Pattern:**
```
https://tickets.museivaticani.va/home/fromtag/{visitors}/{timestamp_ms}/{slug}/1
```

**Parameters:**
- `{visitors}` = Number of visitors (1, 2, 3, etc.) - MUST match task.visitors
- `{timestamp_ms}` = Target date at midnight Rome time in milliseconds
- `{slug}` = "MV-Biglietti" (standard) OR "MV-Visite-Guidate" (guided tours)
- Last `/1` = Volume ID (always 1)

**Example:**
```
# For 2 visitors on March 28, 2026 (standard ticket):
https://tickets.museivaticani.va/home/fromtag/2/1774652400000/MV-Biglietti/1

# For 1 visitor on March 28, 2026 (guided tour):
https://tickets.museivaticani.va/home/fromtag/1/1774652400000/MV-Visite-Guidate/1
```

**Timestamp Calculation (Rome Timezone):**
```python
from zoneinfo import ZoneInfo
from datetime import datetime

# Parse date (DD/MM/YYYY or YYYY-MM-DD)
if "/" in date_str:
    day, month, year = date_str.split('/')
else:
    year, month, day = date_str.split('-')

# Create midnight Rome time
rome = ZoneInfo("Europe/Rome")
dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
timestamp_ms = int(dt.timestamp() * 1000)
```

**What to Extract:**
1. **JSESSIONID cookie** - Required for API authentication
2. **Dynamic Ticket IDs** - From `data-cy="bookTicket_{ID}"` attributes
3. **Ticket Names** - From card titles (h1, h2, .muvaTicketTitle)

**JavaScript Extraction:**
```javascript
// Extract all ticket IDs and names
const tickets = [];
const buttons = document.querySelectorAll("[data-cy^='bookTicket_']");
buttons.forEach(btn => {
    const id = btn.getAttribute("data-cy").split("_")[1];
    const container = btn.closest('div.card') || btn.closest('div.row');
    let name = "Unknown";
    if (container) {
        const titleEl = container.querySelector('h1, h2, h3, h4, .card-title, .muvaTicketTitle');
        if (titleEl) name = titleEl.innerText.trim();
    }
    tickets.push({id: id, name: name});
});
return tickets;
```

---

### STEP 2: Match Ticket by Name (NOT by ID)

**CRITICAL:** Database ticket_id values are STALE. Always resolve fresh IDs.

**Matching Strategy (3-tier):**

1. **Exact Match** - Check if ticket_name substring matches
2. **Keyword Match** - Score by relevant keywords
3. **Smart Fallback** - Use first standard admission ticket

**Keywords for Standard Tickets:**
- musei, museum, palazzo, specola
- biglietti, ingresso, admission
- Exclude: lunch, pranzo, pellegrinaggi, gruppi

**Keywords for Guided Tours:**
- visita, guidata, guided, tour
- Exclude: lunch, pranzo

**Example Matching Code:**
```python
# Strategy 1: Exact substring match
for item in resolved_ids:
    r_name = item.get('name', '').lower()
    t_name = ticket_name.lower()
    if t_name in r_name or r_name in t_name:
        if ticket_type == 0 and "lunch" in r_name:
            continue  # Skip lunch tickets
        fresh_id = item['id']
        break

# Strategy 2: Keyword scoring
if not fresh_id:
    keywords = ['musei', 'biglietti', 'ingresso']
    best_score = 0
    for item in resolved_ids:
        r_name = item.get('name', '').lower()
        score = sum(1 for kw in keywords if kw in r_name)
        if score > best_score and score >= 2:
            best_score = score
            fresh_id = item['id']

# Strategy 3: Fallback to first standard ticket
if not fresh_id and ticket_type == 0:
    for item in resolved_ids:
        r_name = item.get('name', '').lower()
        if 'biglietti' in r_name or 'ingresso' in r_name:
            if not any(x in r_name for x in ['lunch', 'pranzo', 'gruppi']):
                fresh_id = item['id']
                break
```

---

### STEP 3: Call Time Availability API

**URL Pattern:**
```
https://tickets.museivaticani.va/api/visit/timeavail?lang={lang}&visitLang={visitLang}&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={date}
```

**CRITICAL: visitLang Parameter - ALWAYS INCLUDE IT**

Based on actual working implementation, the `visitLang` parameter should **ALWAYS be included**:

- **Standard tickets (ticket_type == 0):** 
  - ✅ Include `&visitLang=` with EMPTY value
  - Example: `...&visitLang=&visitTypeId=...`
  
- **Guided tours (ticket_type == 1):**
  - ✅ Include `&visitLang=ENG` (or ITA, FRA, DEU, SPA)
  - Example: `...&visitLang=ENG&visitTypeId=...`

**Parameters:**
- `lang` = API language (it, en, fr, de, es) - Usually "it"
- `visitLang` = Tour language
  - **Standard tickets:** Empty string `""` (results in `&visitLang=`)
  - **Guided tours:** Language code (ENG, ITA, FRA, DEU, SPA)
- `visitTypeId` = Fresh ticket ID from Step 1
- `visitorNum` = Number of visitors (MUST match deep link)
- `visitDate` = Date in DD/MM/YYYY format

**Examples:**
```
# ✅ CORRECT - Standard ticket (1 visitor, March 28, 2026) - visitLang with EMPTY value:
https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId=2085325042&visitorNum=1&visitDate=28/03/2026

# ✅ CORRECT - Guided tour in English (1 visitor, March 28, 2026) - visitLang with value:
https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=ENG&visitTypeId=1594188966&visitorNum=1&visitDate=28/03/2026
```

**Implementation Pattern:**
```python
# Build URL with visitLang always included
if ticket_type == 0:  # Standard ticket
    # Include visitLang with empty value
    visit_lang = ""
else:  # Guided tour
    # Include visitLang with language code
    visit_lang = language  # e.g., "ENG"

url = (
    f"https://tickets.museivaticani.va/api/visit/timeavail"
    f"?lang=it&visitLang={visit_lang}&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={date}"
)

# Alternative: Conditional parameter
visit_lang_param = language if language else ""  # Empty string for standard tickets
url = (
    f"https://tickets.museivaticani.va/api/visit/timeavail"
    f"?lang=it&visitLang={visit_lang_param}&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={date}"
)
```

**Required Headers:**
```
Accept: application/json, text/plain, */*
X-Requested-With: XMLHttpRequest
Referer: https://tickets.museivaticani.va/
Cookie: JSESSIONID={value_from_step1}
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

**Extract Available Slots:**
```python
available_slots = [
    t['time'] for t in response['timetable'] 
    if t.get('availability') != 'SOLD_OUT'
]
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

### ✅ CORRECT: Always Resolve Fresh IDs
```python
# GOOD - Get fresh ID from page
resolved_ids = await resolve_all_dynamic_ids(page, ...)
fresh_id = match_ticket_by_name(resolved_ids, task.ticket_name)
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
