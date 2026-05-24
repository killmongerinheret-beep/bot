# System Flow Diagram - Google Sheets to Auto-Booking

**Visual Guide to Complete Workflow**

---

## 🎯 Overview

```
Google Sheets → Backend → Database → Worker → Extension → Booking Complete
```

---

## 📊 Detailed Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SETUP PHASE                                  │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Google Sheets   │  ← User creates sheet with participant names
│  Vatican_        │     (Mario Rossi, Luigi Verdi, etc.)
│  Participants    │
└────────┬─────────┘
         │
         │ Admin runs: python manage.py import_participants --agency=WOR
         ↓
┌──────────────────┐
│  Google Sheets   │  ← Service reads sheet via gspread API
│     Service      │     Parses names, emails, phones
└────────┬─────────┘
         │
         │ Stores as JSON
         ↓
┌──────────────────┐
│    Database      │  ← BuyerProfile.participants_json = [
│  BuyerProfile    │       {"first_name": "Mario", "last_name": "Rossi"},
│ participants_json│       {"first_name": "Luigi", "last_name": "Verdi"}
└──────────────────┘     ]


┌─────────────────────────────────────────────────────────────────────┐
│                      MONITORING PHASE                                │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Telegram Bot    │  ← User: /start → Create Monitor
│  User creates    │     Date: 2026-06-15
│  monitor task    │     Visitors: 2
└────────┬─────────┘     Time: 10:00
         │
         │ Creates MonitorTask in database
         ↓
┌──────────────────┐
│    Database      │  ← MonitorTask stored with:
│   MonitorTask    │     - dates: ["2026-06-15"]
│   (Active)       │     - preferred_times: ["10:00"]
└────────┬─────────┘     - visitors: 2
         │
         │ Worker picks up task (every 10 seconds)
         ↓
┌──────────────────┐
│  Vatican Worker  │  ← Calls Vatican Search API
│  Search API      │     GET /api/search/resultPerTag
│  Monitor         │     - Gets fresh ticket IDs
└────────┬─────────┘     - Checks timeavail API
         │
         │ Slot found!
         ↓
┌──────────────────┐
│    Database      │  ← HeldSlot created:
│    HeldSlot      │     - date: "15/06/2026"
│   (Available)    │     - slot_time: "10:00"
└────────┬─────────┘     - status: "held"
         │
         │ Telegram notification sent
         ↓
┌──────────────────┐
│  Telegram Bot    │  ← User receives: "🎉 Slot available!"
│  Notification    │     Date: 15/06/2026 10:00
└──────────────────┘     Click to book


┌─────────────────────────────────────────────────────────────────────┐
│                      EXTENSION PHASE                                 │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ Browser Extension│  ← Polls backend every 10 seconds
│  Backend Listener│     GET /api/v1/available-slots/
│      Mode        │
└────────┬─────────┘
         │
         │ Polls every 10 seconds
         ↓
┌──────────────────┐
│  Backend API     │  ← Returns available slots with:
│ GET /available-  │     - Slot details (date, time)
│     slots/       │     - Profile data (name, email)
└────────┬─────────┘     - Participants (from Google Sheets!)
         │                - Card data (for auto-pay)
         │
         │ Response: {"slots": [{...}], "count": 1}
         ↓
┌──────────────────┐
│ Browser Extension│  ← Detects slot available!
│  Slot Detected   │     Opens incognito window
└────────┬─────────┘
         │
         │ Opens new incognito window
         ↓
┌──────────────────┐
│  Incognito       │  ← Loads Vatican booking page
│   Window         │     https://tickets.museivaticani.va/
│  (Isolated)      │
└────────┬─────────┘
         │
         │ Content script injected
         ↓
┌──────────────────┐
│  Content Script  │  ← Auto-fills form:
│  Auto-Booking    │     Step 1: Select ticket
│     Flow         │     Step 2: Set quantity (2)
└────────┬─────────┘     Step 3: Select time (10:00)
         │                Step 4: Click PROCEDI
         │
         │ Fills checkout form
         ↓
┌──────────────────┐
│  Checkout Form   │  ← Auto-fills with participants:
│  Auto-Fill       │     Adult 1: Mario Rossi
│                  │     Adult 2: Luigi Verdi
└────────┬─────────┘     Email: mario@example.com
         │                Phone: 3401234567
         │
         │ Solves Turnstile
         ↓
┌──────────────────┐
│   Turnstile      │  ← Waits for Turnstile to solve
│   Challenge      │     (2captcha or manual)
└────────┬─────────┘
         │
         │ Clicks BUY button
         ↓
┌──────────────────┐
│  Payment Page    │  ← Auto-fills card details:
│  Auto-Fill       │     Number: 4111...
│                  │     Expiry: 12/2026
└────────┬─────────┘     CVV: 123
         │                Holder: Mario Rossi
         │
         │ Clicks PAY button (if auto-pay enabled)
         ↓
┌──────────────────┐
│  Booking         │  ← Payment submitted!
│  Complete        │     Reference: VAT-2026-123456
└────────┬─────────┘
         │
         │ Extension calls backend
         ↓
┌──────────────────┐
│  Backend API     │  ← POST /api/v1/slots/{id}/mark-booked/
│ POST /slots/     │     Body: {"reference": "VAT-2026-123456"}
│  mark-booked/    │
└────────┬─────────┘
         │
         │ Updates database
         ↓
┌──────────────────┐
│    Database      │  ← HeldSlot updated:
│    HeldSlot      │     - status: "paying"
│   (Booked)       │     - payment_ready: true
└────────┬─────────┘
         │
         │ Confirmation email sent by Vatican
         ↓
┌──────────────────┐
│  User Email      │  ← Booking confirmation received!
│  Confirmation    │     Date: 15/06/2026 10:00
└──────────────────┘     Visitors: 2 (Mario Rossi, Luigi Verdi)


┌─────────────────────────────────────────────────────────────────────┐
│                         SUCCESS! ✅                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. Participant Data Flow

```
Google Sheets
    ↓
[First Name | Last Name | Email | Phone]
    ↓
Google Sheets Service (gspread)
    ↓
JSON Array: [{"first_name": "Mario", "last_name": "Rossi"}, ...]
    ↓
BuyerProfile.participants_json (Database)
    ↓
GET /api/v1/available-slots/ (API Response)
    ↓
Extension receives participants
    ↓
Content script auto-fills form
    ↓
Booking completed with correct names!
```

---

### 2. Slot Availability Flow

```
Vatican Website
    ↓
Search API: /api/search/resultPerTag
    ↓
Fresh Ticket IDs: [{"id": "2129030053", "name": "Musei Vaticani"}]
    ↓
Timeavail API: /api/visit/timeavail
    ↓
Available Slots: [{"time": "10:00", "availability": "AVAILABLE"}]
    ↓
HeldSlot created in database
    ↓
Extension polls: GET /api/v1/available-slots/
    ↓
Extension detects slot
    ↓
Auto-booking triggered!
```

---

### 3. Booking Status Flow

```
HeldSlot created
    ↓
status: "held"
payment_ready: false
    ↓
Extension starts booking
    ↓
status: "held" (still)
payment_ready: false
    ↓
Booking completed
    ↓
Extension calls: POST /slots/{id}/mark-booked/
    ↓
status: "paying"
payment_ready: true
    ↓
Payment confirmed
    ↓
status: "paid"
payment_ready: true
```

---

## 🎯 Key Components

### Backend Components
1. **Google Sheets Service** - Reads participant data
2. **Import Command** - Stores participants in database
3. **Vatican Worker** - Monitors for available slots
4. **API Endpoints** - Provides data to extension

### Extension Components
1. **Background Script** - Polls backend API
2. **Content Script** - Auto-fills forms
3. **Popup UI** - Configuration interface

### Database Tables
1. **Agency** - Stores google_sheet_url
2. **BuyerProfile** - Stores participants_json
3. **MonitorTask** - Stores monitoring configuration
4. **HeldSlot** - Stores available slots

---

## 📊 Timing Diagram

```
Time    | Backend Worker | Extension | Vatican
--------|----------------|-----------|----------
00:00   | Check API      |           |
00:10   | Check API      | Poll      |
00:20   | Check API      |           |
00:30   | Check API      | Poll      |
00:40   | SLOT FOUND!    |           |
00:41   | Create HeldSlot|           |
00:42   | Send Telegram  |           |
00:50   |                | Poll      | ← Detects slot!
00:51   |                | Open tab  |
00:52   |                | Auto-fill | ← Form filled
00:53   |                | Turnstile | ← Solving...
00:54   |                | Click BUY | ← Booking!
00:55   |                | Mark done | ← Complete!
00:56   |                |           | ← Email sent
```

---

## 🔐 Security Flow

```
┌──────────────────┐
│  Google Sheets   │  ← Public sheet OR service account
│  (Read-only)     │     No write access needed
└────────┬─────────┘
         │
         │ HTTPS connection
         ↓
┌──────────────────┐
│  Backend API     │  ← Optional: API key authentication
│  (Protected)     │     Rate limiting enabled
└────────┬─────────┘
         │
         │ Internal network
         ↓
┌──────────────────┐
│    Database      │  ← Encrypted at rest
│  (PostgreSQL)    │     Sensitive data protected
└────────┬─────────┘
         │
         │ HTTPS API
         ↓
┌──────────────────┐
│ Browser Extension│  ← Runs in isolated context
│  (Incognito)     │     Each booking = new session
└──────────────────┘
```

---

## 🎉 Success Indicators

### Backend
- ✅ Import command shows "✅ Saved X participants"
- ✅ API returns 200 OK with slots array
- ✅ Database has participants_json populated

### Extension
- ✅ Extension shows "Monitoring active"
- ✅ Console logs "Polling backend..."
- ✅ Incognito window opens automatically
- ✅ Form fields auto-filled correctly
- ✅ Booking completes without errors

### User Experience
- ✅ Telegram notification received
- ✅ Booking completed automatically
- ✅ Confirmation email received
- ✅ Correct participant names in booking

---

## 📝 Summary

**The system connects 5 major components:**

1. **Google Sheets** - Source of truth for participant names
2. **Backend** - Imports, stores, and serves data
3. **Worker** - Monitors Vatican API for slots
4. **Extension** - Auto-completes bookings
5. **Vatican** - Final booking destination

**Data flows from Google Sheets → Database → Extension → Vatican**

**The entire process is automated from start to finish!** 🚀

