# Workflow Quick Reference

## 📱 TELEGRAM BOT - 8 Steps

```
1. /start → Main Menu
2. 🎫 Create Monitor → Calendar
3. Select Date → Select Adults → Select Children
4. Select Ticket Type → (Language if guided)
5. Select Mode (Notify/Snipe) → (Enter names if Snipe)
6. Select Time Slots → Confirm
7. Task Created in Database ✅
8. Worker Starts Monitoring ✅
```

**Result:** Task is now being monitored every 10 seconds by backend worker

---

## 🌐 BROWSER EXTENSION - 3 Modes

### Mode A: Manual Monitoring (API)
```
1. Open Extension → Configure (date, visitors, ticket)
2. Click "Start Monitoring"
3. Extension checks Vatican API every X seconds
4. When found → Desktop notification
5. User clicks "Book Now" → Opens Vatican website
6. User completes booking manually
```

### Mode B: Tab Reload (Visual Check)
```
1. Open Extension → Select "Tab Reload" mode
2. Click "Start Monitoring"
3. Extension opens Vatican tab
4. Tab reloads every X seconds
5. Content script checks page visually
6. When found → Highlights available slots
7. User clicks slot → Completes booking
```

### Mode C: Backend Listener (Designed - Not Fully Integrated)
```
1. Open Extension → Select "Backend Listener"
2. Enter Backend URL + API Key
3. Click "Start Monitoring"
4. Extension polls backend every 10 seconds
5. When backend finds slot → Extension opens incognito window
6. Content script auto-fills form
7. Booking completed automatically
```

---

## 🔄 INTEGRATED FLOW (Designed)

```
┌─────────────────┐
│  TELEGRAM BOT   │
│  User creates   │
│  monitor task   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DATABASE     │
│  MonitorTask    │
│  stored         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  BACKEND WORKER │
│  Checks Vatican │
│  API every 10s  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SLOTS FOUND!   │
│  HeldSlot       │
│  created        │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│  TELEGRAM       │  │  EXTENSION      │
│  Notification   │  │  Polls backend  │
│  sent           │  │  API            │
└─────────────────┘  └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  INCOGNITO      │
                     │  Window opens   │
                     │  Auto-booking   │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  BOOKING        │
                     │  COMPLETED!     │
                     └─────────────────┘
```

---

## 🎯 CURRENT STATUS

### ✅ Working Right Now

**Telegram Bot:**
- ✅ Create monitors
- ✅ Set buyer profiles
- ✅ View status
- ✅ Receive notifications

**Backend Worker:**
- ✅ Monitor Vatican API
- ✅ Use Search API (fresh IDs)
- ✅ Create HeldSlots
- ✅ Send Telegram alerts

**Browser Extension:**
- ✅ Manual monitoring (API mode)
- ✅ Tab reload mode
- ✅ Auto-booking flow
- ✅ Form auto-fill

### ❌ Missing Integration

**Backend API:**
- ❌ `/api/v1/available-slots/` endpoint
- ❌ Returns HeldSlots for extension

**Extension:**
- ❌ Backend polling not connected
- ❌ Profile sync from database
- ❌ Participant names from database
- ❌ Automatic incognito windows

---

## 📊 Data Flow

### Telegram Bot → Database
```python
MonitorTask {
    agency_id: 14,
    dates: ['2026-06-15'],
    visitors: 2,
    adult_count: 2,
    child_count: 0,
    ticket_type: 0,
    ticket_name: 'Musei Vaticani - Biglietti d\'ingresso',
    language: null,
    tier: 'snipe',
    participants_json: '[{"first_name":"Mario","last_name":"Rossi"}]',
    preferred_times: ['09:00', '10:00', '14:00'],
    is_active: true
}
```

### Worker → Database (When Slots Found)
```python
HeldSlot {
    task_id: 422,
    date: '15/06/2026',
    slot_time: '09:00',
    slot_id: 'abc123',
    ticket_id: '2129030053',
    ticket_name: 'Musei Vaticani - Biglietti d\'ingresso',
    visitors: 2,
    adult_count: 2,
    child_count: 0,
    status: 'held',
    payment_ready: false,
    jsessionid: 'XYZ...',
    hold_started_at: '2026-06-15 08:00:00'
}
```

### Extension → Backend (Designed)
```javascript
// Extension polls this endpoint
GET /api/v1/available-slots/

// Backend returns
{
    "slots": [
        {
            "id": 12345,
            "date": "15/06/2026",
            "time": "09:00",
            "ticket_id": "2129030053",
            "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
            "visitors": 2,
            "profile": {
                "firstName": "Mario",
                "lastName": "Rossi",
                "email": "mario@example.com",
                "phone": "3401234567"
            },
            "participants": [
                {"first_name": "Mario", "last_name": "Rossi"},
                {"first_name": "Luigi", "last_name": "Verdi"}
            ]
        }
    ]
}
```

---

## 🚀 Quick Start

### For Telegram Bot:
```
1. Open Telegram
2. Send /start to bot
3. Click "🎫 Create Monitor"
4. Follow the steps
5. Wait for notification
```

### For Extension (Manual):
```
1. Click extension icon
2. Select date, visitors, ticket type
3. Choose "API Only" mode
4. Click "Start Monitoring"
5. Wait for desktop notification
```

### For Extension (Backend Listener - When Implemented):
```
1. Click extension icon
2. Select "Backend Listener" mode
3. Enter: http://localhost:8000
4. Click "Start Monitoring"
5. Extension will auto-book when slots found
```

---

## 📞 Support

**Check if monitoring is working:**
```bash
# Telegram bot
docker-compose logs telegram_bot --tail=20

# Worker
docker-compose logs worker_vatican --tail=50 | grep "ORCHESTRATOR"

# Extension
Open extension → Check "Recent Results" section
```

**Check database:**
```bash
# Active tasks
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT COUNT(*) FROM monitors_monitortask WHERE is_active = true;"

# Held slots
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT COUNT(*) FROM held_slots WHERE status = 'held';"
```

---

**Last Updated:** May 14, 2026  
**Version:** 1.0
