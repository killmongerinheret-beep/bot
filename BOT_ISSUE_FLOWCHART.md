# 🔄 BOT ISSUE FLOWCHART

## CURRENT BROKEN FLOW (Why Bot Gives Wrong Info)

```
┌─────────────────────────────────────────────────────────────┐
│ USER ASKS: "Are tickets available for March 16?"           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "Let me check Vatican website..."                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "I need a proxy to connect..."                        │
│ DATABASE: "Sorry, 0 proxies available"                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ❌ CONNECTION FAILS
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ERROR: ERR_TUNNEL_CONNECTION_FAILED                         │
│ BOT: "Can't load Vatican page, can't extract fresh IDs"    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "I'll use the ticket ID from database..."             │
│ DATABASE: "Here's ID 1750097398 (from 3 weeks ago)"        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "Calling Vatican API with ID 1750097398..."           │
│ VATICAN API: "500 Error - That ID doesn't exist anymore"   │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ❌ API RETURNS 500
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT LOGIC: "API error = No tickets available"              │
│ BOT REPORTS: "CLOSED (0 slots)"                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ USER SEES: "No tickets available for March 16" ❌ WRONG!   │
│ REALITY: Tickets ARE available (14 slots) ✅               │
└─────────────────────────────────────────────────────────────┘
```

---

## CORRECT FLOW (After Fix)

```
┌─────────────────────────────────────────────────────────────┐
│ USER ASKS: "Are tickets available for March 16?"           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "Let me check Vatican website..."                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "I need a proxy to connect..."                        │
│ DATABASE: "Here are 14 Oxylabs proxies"                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ✅ CONNECTION SUCCESS
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "Loading Vatican page..."                             │
│ VATICAN: "Here's the page with current tickets"            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "Extracting fresh ticket IDs from page..."            │
│ FOUND: 10 tickets with fresh IDs                           │
│ - ID 2092730005: "Musei Vaticani - Biglietti d'ingresso"   │
│ - ID 1594188966: "Specola Vaticana - Visita Guidata"       │
│ - ... (8 more)                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "Matching ticket by name..."                          │
│ MATCH: "Musei Vaticani" → ID 2092730005 (FRESH!)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "Calling Vatican API with FRESH ID 2092730005..."     │
│ VATICAN API: "200 OK - Here's the availability"            │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ✅ API RETURNS 200
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ API RESPONSE:                                               │
│ {                                                           │
│   "timetable": [                                            │
│     {"time": "09:00", "availability": "AVAILABLE"},        │
│     {"time": "09:30", "availability": "AVAILABLE"},        │
│     {"time": "10:00", "availability": "SOLD_OUT"},         │
│     ... (14 available slots total)                         │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT: "Filtering available slots..."                        │
│ FOUND: 14 available time slots                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BOT REPORTS: "AVAILABLE (14 slots)"                        │
│ STATE CHANGE: CLOSED → OPEN                                │
│ TELEGRAM ALERT: "🎉 Tickets now available!"                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ USER SEES: "Tickets available! 14 slots" ✅ CORRECT!       │
│ REALITY: Tickets ARE available (14 slots) ✅               │
└─────────────────────────────────────────────────────────────┘
```

---

## KEY DIFFERENCES

| Step | Broken Flow | Fixed Flow |
|------|-------------|------------|
| Proxies | 0 proxies | 14 proxies |
| Connection | ❌ FAILED | ✅ SUCCESS |
| Page Load | ❌ Can't load | ✅ Loaded |
| ID Extraction | ❌ No IDs | ✅ 10 fresh IDs |
| Ticket ID | 1750097398 (stale) | 2092730005 (fresh) |
| API Call | ❌ 500 error | ✅ 200 success |
| Result | "CLOSED" (wrong) | "AVAILABLE" (correct) |
| User Experience | Frustrated | Happy |

---

## THE FIX

```bash
# Add proxies to database
docker exec travelagenntbot-backend-1 python /app/backend/manage.py seed_proxies

# Clear stale IDs
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c \
  "from monitors.models import MonitorTask; \
   MonitorTask.objects.filter(site='vatican').update(ticket_id=None)"

# Restart worker
docker-compose restart worker_vatican
```

**Result:** Bot now follows the CORRECT FLOW and gives accurate information!

---

## VERIFICATION

### Before Fix
```
[ERROR] ERR_TUNNEL_CONNECTION_FAILED
[WARNING] Falling back to stale ID 1750097398
[WARNING] API call failed: Status 500
[INFO] Musei Vaticani is CLOSED (0 slots)  ← WRONG
```

### After Fix
```
[INFO] Loaded 14 Oxylabs proxies
[INFO] Session Cookies: 3 cookies set
[INFO] Resolved 10 Dynamic IDs from Page
[INFO] Exact Match: 'Musei Vaticani' -> ID 2092730005
[INFO] API Response: 200
[INFO] Found 14 available slots  ← CORRECT
[INFO] STATE CHANGE: CLOSED → OPEN!
[INFO] TELEGRAM ALERT sent
```

---

**BOTTOM LINE:** No proxies = Can't connect = Can't get fresh IDs = API fails = Wrong information

**FIX:** Add proxies → Everything works → Correct information
