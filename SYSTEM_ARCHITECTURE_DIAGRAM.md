# System Architecture Diagram

## 🏗️ Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VATICAN TICKET BOT SYSTEM                        │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE LAYER                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐         ┌──────────────────┐                       │
│  │  Telegram Bot   │         │ Browser Extension│                       │
│  │                 │         │                  │                       │
│  │  /start         │         │  Backend Listener│                       │
│  │  /monitor       │         │  Auto-Booking    │                       │
│  │  /list          │         │  Hold Mode       │                       │
│  │  /stop          │         │  Parallel Booking│                       │
│  └────────┬────────┘         └────────┬─────────┘                       │
│           │                           │                                  │
└───────────┼───────────────────────────┼──────────────────────────────────┘
            │                           │
            │ HTTP REST API             │ HTTP REST API
            │                           │
┌───────────▼───────────────────────────▼──────────────────────────────────┐
│                          BACKEND API LAYER                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Django REST Framework                         │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │    │
│  │  │   Monitor    │  │   Agency     │  │  Held Slot   │         │    │
│  │  │   Tasks      │  │   Management │  │  Management  │         │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │    │
│  │  │   Buyer      │  │   Google     │  │    Bokun     │         │    │
│  │  │   Profiles   │  │   Sheets     │  │    API       │         │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────┬─┘    │
│                                                                   │      │
└───────────────────────────────────────────────────────────────────┼──────┘
                                                                    │
                                                                    │
┌───────────────────────────────────────────────────────────────────▼──────┐
│                          DATA STORAGE LAYER                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐         ┌──────────────────┐                      │
│  │   PostgreSQL     │         │      Redis       │                      │
│  │                  │         │                  │                      │
│  │  - MonitorTask   │         │  - Sessions      │                      │
│  │  - HeldSlot      │         │  - Cache         │                      │
│  │  - Agency        │         │  - Celery Queue  │                      │
│  │  - BuyerProfile  │         │                  │                      │
│  └──────────────────┘         └──────────────────┘                      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │
                                    │ Read/Write
                                    │
┌───────────────────────────────────┴───────────────────────────────────────┐
│                        MONITORING & WORKER LAYER                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Celery Worker (Vatican)                       │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │  Vatican Monitoring Loop (Every 5 seconds)               │  │    │
│  │  │                                                           │  │    │
│  │  │  1. Get active MonitorTasks from database               │  │    │
│  │  │  2. For each task:                                       │  │    │
│  │  │     a. Call Vatican Search API (get fresh ticket IDs)   │  │    │
│  │  │     b. Match ticket by NAME (not ID)                    │  │    │
│  │  │     c. Call Vatican timeavail API (check time slots)    │  │    │
│  │  │     d. If slots found → Create HeldSlot                 │  │    │
│  │  │     e. Send Telegram notification                       │  │    │
│  │  │  3. Sleep 5 seconds                                      │  │    │
│  │  │  4. Repeat                                               │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────┬─┘    │
│                                                                   │      │
└───────────────────────────────────────────────────────────────────┼──────┘
                                                                    │
                                                                    │ HTTP API
                                                                    │
┌───────────────────────────────────────────────────────────────────▼──────┐
│                        EXTERNAL SERVICES LAYER                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  Vatican API     │  │  Google Sheets   │  │   Bokun API      │      │
│  │                  │  │                  │  │                  │      │
│  │  /search/        │  │  Participant     │  │  Bookings        │      │
│  │  resultPerTag    │  │  Data            │  │  Participants    │      │
│  │                  │  │                  │  │  Payments        │      │
│  │  /visit/         │  │  Auto-sync       │  │  Webhooks        │      │
│  │  timeavail       │  │  Every hour      │  │                  │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

PHASE 1: TASK CREATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    USER
     │
     │ /monitor command
     │ Date: 28/03/2026
     │ Visitors: 2
     ▼
  TELEGRAM BOT
     │
     │ POST /api/v1/monitor-tasks/
     │ {date, visitors, ticket_type, agency_id}
     ▼
  BACKEND API
     │
     │ Create MonitorTask
     │ is_active = true
     ▼
  DATABASE
     │
     │ Task stored
     └─────────────────────────────────────────────────────────────────────


PHASE 2: MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  WORKER VATICAN (Every 5 seconds)
     │
     │ Query active tasks
     ▼
  DATABASE
     │
     │ Return MonitorTask(date=28/03/2026, visitors=2)
     ▼
  WORKER VATICAN
     │
     │ GET /api/search/resultPerTag
     │ ?date=28/03/2026&visitors=2&tag=MV-Biglietti
     ▼
  VATICAN SEARCH API
     │
     │ Return fresh ticket IDs + names
     │ [{id: "2129030053", name: "Musei Vaticani - Biglietti d'ingresso"}]
     ▼
  WORKER VATICAN
     │
     │ Match ticket by NAME (not ID)
     │ Found: "Musei Vaticani - Biglietti d'ingresso"
     │
     │ GET /api/visit/timeavail
     │ ?ticket_id=2129030053&date=28/03/2026&visitors=2&visitLang=
     ▼
  VATICAN TIMEAVAIL API
     │
     │ Return time slots
     │ [{time: "10:00", availability: "AVAILABLE"}]
     ▼
  WORKER VATICAN
     │
     │ Slots found! Create HeldSlot
     ▼
  DATABASE
     │
     │ HeldSlot created
     │ (date=28/03/2026, time=10:00, status=held)
     │
     │ Send notification
     ▼
  TELEGRAM BOT
     │
     │ "✅ Tickets Available! 28/03/2026 10:00"
     └─────────────────────────────────────────────────────────────────────


PHASE 3: PARTICIPANT DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  CELERY BEAT (Every hour)
     │
     │ Trigger sync_participants_from_sheets
     ▼
  BACKEND
     │
     │ For each agency with google_sheet_url
     ▼
  GOOGLE SHEETS API
     │
     │ Read participant data
     │ [
     │   {first_name: "John", last_name: "Doe", email: "john@example.com"},
     │   {first_name: "Jane", last_name: "Doe", email: "jane@example.com"}
     │ ]
     ▼
  BACKEND
     │
     │ Create/Update BuyerProfile
     │ Store participants_json
     ▼
  DATABASE
     │
     │ BuyerProfile saved
     │ participants_json = [...]
     └─────────────────────────────────────────────────────────────────────


PHASE 4: EXTENSION DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  EXTENSION BACKGROUND (Every 10 seconds)
     │
     │ GET /api/v1/available-slots/?status=held&limit=10
     ▼
  BACKEND API
     │
     │ Query HeldSlot + BuyerProfile + Participants
     │
     │ Return:
     │ {
     │   slots: [{
     │     id: 123,
     │     date: "28/03/2026",
     │     time: "10:00",
     │     ticket_id: "2129030053",
     │     visitors: 2,
     │     profile: {first_name, last_name, email, phone, ...},
     │     participants: [{first_name, last_name}, ...],
     │     card: {number, expiry, cvv, holder}
     │   }]
     │ }
     ▼
  EXTENSION BACKGROUND
     │
     │ Slots found! Open incognito windows
     │
     │ For each slot:
     │   chrome.windows.create({
     │     url: "https://tickets.museivaticani.va/home",
     │     incognito: true
     │   })
     └─────────────────────────────────────────────────────────────────────


PHASE 5: AUTO-BOOKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  EXTENSION CONTENT SCRIPT (In incognito window)
     │
     │ Navigate to Vatican website
     ▼
  VATICAN WEBSITE
     │
     │ Load ticket selection page
     ▼
  EXTENSION
     │
     │ Step 1: Click ticket button
     │ document.querySelector(`[data-cy='bookTicket_2129030053']`).click()
     │
     │ Step 2: Select quantity
     │ document.querySelector("[data-cy='ticketQuantity']").value = 2
     │
     │ Step 3: Select time slot (STRICT)
     │ Find exact time "10:00" → click
     │ If not found → CANCEL booking
     │
     │ Step 4: Click PROCEDI
     │ document.querySelector("[data-cy='bookVisit']").click()
     ▼
  VATICAN CHECKOUT PAGE
     │
     │ Load checkout form
     ▼
  EXTENSION
     │
     │ Step 5: Fill form with participants
     │ Manager: John Doe (john@example.com, +39 123456789)
     │ Participant 1: John Doe
     │ Participant 2: Jane Doe
     │ GDPR checkboxes: checked
     │
     │ Step 6: Wait for Turnstile (Cloudflare captcha)
     │ Check if BUY button enabled
     │
     │ Step 7: Click BUY button
     │ document.querySelector("[data-cy='buyButton']").click()
     ▼
  VATICAN PAYMENT PAGE
     │
     │ Redirect to epay.vatican.va
     ▼
  EXTENSION
     │
     │ Step 8: Fill payment form (if card data available)
     │ Name: John Doe
     │ Email: john@example.com
     │ Card: 4111111111111111
     │ Expiry: 12/25
     │ CVV: 123
     │
     │ Step 9: Click PAY (if auto-pay enabled)
     │ document.querySelector("#form-submit").click()
     ▼
  VATICAN CONFIRMATION
     │
     │ Booking completed
     │ Reference: VAT-2026-001
     ▼
  EXTENSION
     │
     │ POST /api/v1/slots/123/mark-booked/
     │ {reference: "VAT-2026-001", epay_url: "..."}
     ▼
  BACKEND API
     │
     │ Update HeldSlot
     │ status = "paid"
     │ payment_url = "..."
     ▼
  DATABASE
     │
     │ Slot updated
     │
     │ Send notification
     ▼
  TELEGRAM BOT
     │
     │ "✅ Booking Completed! Reference: VAT-2026-001"
     └─────────────────────────────────────────────────────────────────────
```

---

## 🔌 Integration Points

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INTEGRATION POINTS                                │
└─────────────────────────────────────────────────────────────────────────┘

1. TELEGRAM ↔ BACKEND
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Protocol: HTTP REST API
   Endpoints:
     - POST /api/v1/monitor-tasks/        (Create task)
     - GET  /api/v1/monitor-tasks/        (List tasks)
     - DELETE /api/v1/monitor-tasks/{id}/ (Delete task)
   Data Format: JSON


2. WORKER ↔ VATICAN API
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Protocol: HTTP REST API
   Endpoints:
     - GET /api/search/resultPerTag       (Get fresh ticket IDs)
     - GET /api/visit/timeavail            (Get time slots)
   Data Format: JSON
   Frequency: Every 5 seconds


3. BACKEND ↔ GOOGLE SHEETS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Protocol: Google Sheets API v4
   Authentication: Service Account
   Operations:
     - Read participant data
     - Auto-sync every hour
   Data Format: Spreadsheet rows


4. EXTENSION ↔ BACKEND API
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Protocol: HTTP REST API
   Endpoints:
     - GET  /api/v1/available-slots/      (Get held slots)
     - POST /api/v1/slots/{id}/mark-booked/ (Mark booked)
     - POST /api/v1/google-sheets/sync/   (Sync sheets)
   Data Format: JSON
   Frequency: Every 10 seconds


5. EXTENSION ↔ VATICAN WEBSITE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Protocol: DOM Manipulation
   Technology: Content Script (JavaScript)
   Operations:
     - Click buttons
     - Fill forms
     - Submit data
   Isolation: Incognito windows


6. BACKEND ↔ BOKUN API (Optional)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Protocol: HTTP REST API
   Authentication: API Key
   Endpoints:
     - GET  /bookings                      (List bookings)
     - GET  /bookings/{id}/participants    (Get participants)
     - PATCH /bookings/{id}                (Update booking)
   Data Format: JSON
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                                   │
└─────────────────────────────────────────────────────────────────────────┘

LAYER 1: AUTHENTICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ┌─────────────────┐
  │  Telegram Bot   │ → Bot Token (Environment Variable)
  └─────────────────┘

  ┌─────────────────┐
  │  Backend API    │ → Session Token (Redis, 7 days)
  └─────────────────┘

  ┌─────────────────┐
  │  Google Sheets  │ → Service Account (JSON Credentials)
  └─────────────────┘

  ┌─────────────────┐
  │  Bokun API      │ → API Key (Environment Variable)
  └─────────────────┘


LAYER 2: DATA ENCRYPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ┌─────────────────┐
  │  Database       │ → Encrypted at rest (PostgreSQL)
  └─────────────────┘

  ┌─────────────────┐
  │  Redis Cache    │ → Encrypted connections (TLS)
  └─────────────────┘

  ┌─────────────────┐
  │  API Calls      │ → HTTPS only (Production)
  └─────────────────┘


LAYER 3: ISOLATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ┌─────────────────┐
  │  Extension      │ → Incognito windows (isolated sessions)
  └─────────────────┘

  ┌─────────────────┐
  │  Docker         │ → Container isolation
  └─────────────────┘

  ┌─────────────────┐
  │  Database       │ → Network isolation (internal only)
  └─────────────────┘


LAYER 4: ACCESS CONTROL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ┌─────────────────┐
  │  Agency         │ → Each agency sees only their data
  └─────────────────┘

  ┌─────────────────┐
  │  Super Admin    │ → Can see all agencies
  └─────────────────┘

  ┌─────────────────┐
  │  API Keys       │ → Rate limiting per key
  └─────────────────┘
```

---

## 📊 Performance Metrics

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PERFORMANCE TARGETS                               │
└─────────────────────────────────────────────────────────────────────────┘

VATICAN MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Check Frequency:     5 seconds
  API Response Time:   < 2 seconds
  Tasks per Check:     Up to 1000
  Total Check Time:    < 10 seconds


EXTENSION POLLING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Poll Frequency:      10 seconds
  API Response Time:   < 1 second
  Concurrent Bookings: Up to 10
  Booking Time:        2-3 minutes


DATABASE QUERIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Query Time:          < 100ms
  Connection Pool:     20 connections
  Cache Hit Rate:      > 80%


GOOGLE SHEETS SYNC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Sync Frequency:      Every hour
  Sync Time:           < 30 seconds
  Participants:        Up to 1000
```

---

**Last Updated**: May 22, 2026  
**Version**: 1.0
