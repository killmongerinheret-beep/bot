# System Integration Summary

## 🎯 Complete System Overview

This document provides a high-level overview of how all components work together to create a fully automated Vatican ticket booking system.

---

## 📊 System Components

### 1. **Telegram Bot** (User Interface)
- **Purpose**: User creates monitoring tasks
- **Technology**: Python Telegram Bot
- **Location**: `telegram_bot/`
- **Key Features**:
  - `/start` - Start bot
  - `/monitor` - Create monitoring task
  - `/list` - View active tasks
  - `/stop` - Stop monitoring task
  - Receives notifications when tickets found

### 2. **Backend API** (Data Management)
- **Purpose**: Store tasks, manage data, expose APIs
- **Technology**: Django REST Framework
- **Location**: `backend/`
- **Key Features**:
  - Store monitoring tasks
  - Manage agencies and users
  - Expose REST APIs for extension
  - Read participant data from Google Sheets
  - Integrate with Bokun API

### 3. **Worker Vatican** (Monitoring Engine)
- **Purpose**: Monitor Vatican website for availability
- **Technology**: Celery + Playwright
- **Location**: `worker_vatican/`
- **Key Features**:
  - Check Vatican Search API every 5 seconds
  - Use fresh ticket IDs (never hardcoded)
  - Create HeldSlot when availability found
  - Send Telegram notifications

### 4. **Google Sheets** (Participant Data)
- **Purpose**: Store participant information
- **Technology**: Google Sheets API
- **Location**: `backend/services/google_sheets_service.py`
- **Key Features**:
  - Read participant data (name, email, phone, etc.)
  - Auto-sync every hour
  - Manual sync via API
  - Support multiple participants per booking

### 5. **Browser Extension** (Auto-Booking)
- **Purpose**: Automatically book tickets when found
- **Technology**: Chrome/Firefox Extension
- **Location**: `browser-extension/`
- **Key Features**:
  - Poll backend API every 10 seconds
  - Open incognito windows for parallel booking
  - Auto-fill forms with participant data
  - Complete entire booking flow
  - Support up to 10 concurrent bookings

### 6. **Bokun API** (Optional Integration)
- **Purpose**: Additional booking data source
- **Technology**: REST API
- **Location**: Configuration in `.env`
- **Key Features**:
  - Fetch booking information
  - Sync with backend
  - Provide additional participant data

---

## 🔄 Complete Data Flow

### Phase 1: Task Creation (Telegram → Backend)

```
USER
  ↓ /monitor command
TELEGRAM BOT
  ↓ Creates MonitorTask
BACKEND DATABASE
  ↓ Task stored with:
    - date: 28/03/2026
    - visitors: 2
    - ticket_type: 0 (standard)
    - agency_id: 1
    - is_active: true
```

### Phase 2: Monitoring (Worker → Vatican API)

```
WORKER VATICAN (Celery)
  ↓ Every 5 seconds
VATICAN SEARCH API
  ↓ GET /api/search/resultPerTag
    - date: 28/03/2026
    - visitors: 2
    - tag: MV-Biglietti
  ↓ Returns fresh ticket IDs
WORKER VATICAN
  ↓ Match ticket by name
  ↓ Call timeavail API
VATICAN TIMEAVAIL API
  ↓ GET /api/visit/timeavail
    - ticket_id: 2129030053 (fresh)
    - date: 28/03/2026
    - visitors: 2
  ↓ Returns available time slots
WORKER VATICAN
  ↓ If slots found
  ↓ Create HeldSlot
BACKEND DATABASE
  ↓ Slot stored with:
    - date: 28/03/2026
    - time: 10:00
    - ticket_id: 2129030053
    - status: held
```

### Phase 3: Participant Data (Google Sheets → Backend)

```
GOOGLE SHEETS
  ↓ Contains participant data:
    - First Name
    - Last Name
    - Email
    - Phone
    - Birth Date
  ↓
BACKEND (Auto-sync every hour)
  ↓ Reads sheet via Google Sheets API
  ↓ Creates/updates BuyerProfile
  ↓ Stores participants_json
BACKEND DATABASE
  ↓ Profile stored with:
    - first_name: John
    - last_name: Doe
    - email: john@example.com
    - phone: +39 123456789
    - participants_json: [...]
```

### Phase 4: Extension Detection (Extension → Backend API)

```
BROWSER EXTENSION (Background)
  ↓ Every 10 seconds
BACKEND API
  ↓ GET /api/v1/available-slots/
  ↓ Returns:
    {
      "slots": [
        {
          "id": 123,
          "date": "28/03/2026",
          "time": "10:00",
          "ticket_id": "2129030053",
          "visitors": 2,
          "profile": {...},
          "participants": [...],
          "card": {...}
        }
      ]
    }
  ↓
BROWSER EXTENSION
  ↓ Detects available slot
  ↓ Opens incognito window
```

### Phase 5: Auto-Booking (Extension → Vatican Website)

```
BROWSER EXTENSION (Content Script)
  ↓ Navigate to Vatican
VATICAN WEBSITE
  ↓ Load ticket selection page
EXTENSION
  ↓ Click ticket button (using ticket_id)
  ↓ Select quantity (2 visitors)
  ↓ Select time slot (10:00 - STRICT)
  ↓ Click PROCEDI
VATICAN CHECKOUT PAGE
  ↓ Load checkout form
EXTENSION
  ↓ Fill form with participants:
    - Manager: John Doe
    - Participant 1: John Doe
    - Participant 2: Jane Doe
  ↓ Wait for Turnstile
  ↓ Click BUY button
VATICAN PAYMENT PAGE
  ↓ Redirect to epay
EXTENSION
  ↓ Fill payment form (if card data)
  ↓ Click PAY (if auto-pay enabled)
VATICAN CONFIRMATION
  ↓ Booking completed
EXTENSION
  ↓ POST /api/v1/slots/123/mark-booked/
BACKEND
  ↓ Update slot status to 'paid'
TELEGRAM BOT
  ↓ Send confirmation to user
```

---

## 🔑 Key Integration Points

### 1. **Telegram ↔ Backend**

**Communication**: HTTP REST API

**Endpoints**:
- `POST /api/v1/monitor-tasks/` - Create task
- `GET /api/v1/monitor-tasks/` - List tasks
- `DELETE /api/v1/monitor-tasks/{id}/` - Delete task

**Data Flow**:
```python
# Telegram bot creates task
task = {
    'agency_id': 1,
    'date': '28/03/2026',
    'visitors': 2,
    'ticket_type': 0,
    'is_active': True
}
response = requests.post('http://backend:8000/api/v1/monitor-tasks/', json=task)
```

### 2. **Worker ↔ Vatican API**

**Communication**: HTTP REST API (Vatican Search API)

**Endpoints**:
- `GET /api/search/resultPerTag` - Get fresh ticket IDs
- `GET /api/visit/timeavail` - Get available time slots

**Data Flow**:
```python
# Worker checks Vatican
# Step 1: Get fresh ticket IDs
response = requests.get('https://tickets.museivaticani.va/api/search/resultPerTag', params={
    'date': '28/03/2026',
    'visitors': 2,
    'tag': 'MV-Biglietti'
})
tickets = response.json()['visits']

# Step 2: Check time slots
response = requests.get('https://tickets.museivaticani.va/api/visit/timeavail', params={
    'ticket_id': tickets[0]['id'],
    'date': '28/03/2026',
    'visitors': 2
})
slots = response.json()['timetable']
```

### 3. **Backend ↔ Google Sheets**

**Communication**: Google Sheets API

**Authentication**: Service Account JSON

**Data Flow**:
```python
# Backend reads Google Sheets
from google.oauth2 import service_account
from googleapiclient.discovery import build

credentials = service_account.Credentials.from_service_account_file('credentials.json')
service = build('sheets', 'v4', credentials=credentials)

# Read participant data
result = service.spreadsheets().values().get(
    spreadsheetId='sheet_id',
    range='Sheet1!A2:E100'
).execute()

participants = result.get('values', [])
```

### 4. **Extension ↔ Backend API**

**Communication**: HTTP REST API

**Endpoints**:
- `GET /api/v1/available-slots/` - Get available slots
- `POST /api/v1/slots/{id}/mark-booked/` - Mark slot as booked
- `POST /api/v1/google-sheets/sync/` - Sync Google Sheets

**Data Flow**:
```javascript
// Extension polls backend
const response = await fetch('http://localhost:8000/api/v1/available-slots/', {
  headers: {
    'Authorization': 'Bearer api_key',
    'Content-Type': 'application/json'
  }
});

const data = await response.json();

if (data.slots.length > 0) {
  // Open incognito windows
  for (const slot of data.slots) {
    await openIncognitoWindow(slot);
  }
}
```

### 5. **Extension ↔ Vatican Website**

**Communication**: DOM Manipulation + Form Filling

**Technology**: Content Script (JavaScript)

**Data Flow**:
```javascript
// Extension fills Vatican form
// 1. Select ticket
document.querySelector(`[data-cy='bookTicket_${ticketId}']`).click();

// 2. Select quantity
document.querySelector("[data-cy='ticketQuantity']").value = visitors;

// 3. Select time slot
document.querySelector(`[data-cy='time']`).click();

// 4. Fill checkout form
document.querySelector("[data-cy='managerName']").value = profile.first_name;
document.querySelector("[data-cy='managerSurname']").value = profile.last_name;
document.querySelector("[data-cy='managerEmail']").value = profile.email;

// 5. Submit
document.querySelector("[data-cy='buyButton']").click();
```

### 6. **Backend ↔ Bokun API** (Optional)

**Communication**: HTTP REST API

**Authentication**: API Key

**Data Flow**:
```python
# Backend fetches Bokun data
import requests

response = requests.get('https://api.bokun.io/bookings', headers={
    'Authorization': f'Bearer {BOKUN_API_KEY}',
    'Content-Type': 'application/json'
})

bookings = response.json()
```

---

## 🔐 Authentication & Security

### 1. **Telegram Bot**
- **Method**: Bot Token
- **Storage**: Environment variable `TELEGRAM_BOT_TOKEN`
- **Security**: Token never exposed to users

### 2. **Backend API**
- **Method**: Session Token (Bearer)
- **Storage**: Redis cache (7 days expiry)
- **Security**: HTTPS in production, CORS configured

### 3. **Google Sheets**
- **Method**: Service Account
- **Storage**: JSON credentials file
- **Security**: File permissions restricted, not in git

### 4. **Bokun API**
- **Method**: API Key
- **Storage**: Environment variable `BOKUN_API_KEY`
- **Security**: HTTPS only

### 5. **Extension**
- **Method**: API Key (optional)
- **Storage**: Chrome storage (encrypted)
- **Security**: Incognito windows for isolation

---

## 📈 Performance Optimization

### 1. **Vatican API Calls**
- **Frequency**: Every 5 seconds
- **Optimization**: Use Search API (10x faster than browser)
- **Caching**: Cache ticket IDs for 12 hours
- **Rate Limiting**: Respect Vatican rate limits

### 2. **Database Queries**
- **Indexing**: Index on date, agency_id, is_active
- **Caching**: Redis for session data
- **Optimization**: Select only needed fields

### 3. **Google Sheets Sync**
- **Frequency**: Every hour (auto-sync)
- **Optimization**: Only sync changed rows
- **Caching**: Cache participant data in database

### 4. **Extension Polling**
- **Frequency**: Every 10 seconds
- **Optimization**: Only fetch new slots
- **Deduplication**: Track processed slot IDs

### 5. **Parallel Booking**
- **Concurrency**: Up to 10 simultaneous bookings
- **Isolation**: Separate incognito windows
- **Resource Management**: Close windows after completion

---

## 🧪 Testing Strategy

### 1. **Unit Tests**
```bash
# Backend tests
docker-compose exec backend python manage.py test

# Worker tests
docker-compose exec worker_vatican pytest
```

### 2. **Integration Tests**
```bash
# Test complete flow
docker-compose exec backend python manage.py test_complete_flow
```

### 3. **Extension Tests**
```javascript
// Test backend connection
chrome.runtime.sendMessage({action: 'testBackendConnection'});

// Test slot detection
chrome.runtime.sendMessage({action: 'testSlotDetection'});

// Test auto-booking
chrome.runtime.sendMessage({action: 'testAutoBooking'});
```

### 4. **End-to-End Tests**
```bash
# Create test task via Telegram
# Worker finds test slot
# Extension books test slot
# Verify booking completed
```

---

## 📊 Monitoring & Logging

### 1. **Backend Logs**
```bash
docker-compose logs -f backend

# Expected:
# [INFO] Task created: 28/03/2026, 2 visitors
# [INFO] Slot held: 28/03/2026 10:00
# [INFO] Slot booked: 28/03/2026 10:00
```

### 2. **Worker Logs**
```bash
docker-compose logs -f worker_vatican

# Expected:
# [INFO] Monitoring 73 tasks
# [INFO] Checking Vatican API...
# [INFO] Found 1 available slot
# [INFO] Created HeldSlot: 28/03/2026 10:00
```

### 3. **Extension Logs**
```javascript
// Browser console (F12)
// Expected:
// ✅ Backend listener started
// 🔄 Checking backend for slots...
// 🎉 Found 1 available slot
// 📦 Opening incognito window
// ✅ Booking completed
```

### 4. **Telegram Notifications**
```
✅ Tickets Available!
📅 28/03/2026 10:00
👥 2 visitors
🎫 Vatican Museums - Standard Entry

🔗 Booking in progress...

✅ Booking Completed!
🔖 Reference: VAT-2026-001
💳 Payment: €32.00
```

---

## 🚀 Deployment Checklist

### Development Environment
- [ ] Docker installed
- [ ] Git repository cloned
- [ ] `.env` file configured
- [ ] Telegram bot created
- [ ] Google Sheets credentials obtained
- [ ] Database migrated
- [ ] Services started
- [ ] Extension installed
- [ ] Test slot created
- [ ] Complete flow tested

### Production Environment
- [ ] Domain name configured
- [ ] HTTPS enabled (SSL certificate)
- [ ] Production database (PostgreSQL)
- [ ] Redis configured
- [ ] Environment variables set
- [ ] CORS configured
- [ ] Rate limiting enabled
- [ ] Monitoring enabled
- [ ] Backups configured
- [ ] Error tracking enabled (Sentry)

---

## 📚 Documentation Index

1. **PC_SETUP_GUIDE.md** - Complete setup instructions
2. **EXTENSION_COMPLETE_GUIDE.md** - Extension functionality and integration
3. **COMPLETE_SYSTEM_WORKFLOW.md** - System workflow explanation
4. **VATICAN_BOT_RULES.md** - Vatican API rules and best practices
5. **GOOGLE_SHEETS_AUTO_SYNC.md** - Google Sheets integration
6. **browser-extension/README.md** - Extension user guide

---

## 🎯 Quick Start Commands

```bash
# Start system
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Create test slot
docker-compose exec backend python /app/create_test_slot.py

# Import participants
docker-compose exec backend python manage.py import_participants --agency-id 1

# Sync Google Sheets
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{"agency_id": 1}'

# Check available slots
curl http://localhost:8000/api/v1/available-slots/

# Stop system
docker-compose down
```

---

## 🆘 Support

### Common Issues

1. **Docker not starting**: Restart Docker Desktop
2. **Database errors**: Run migrations
3. **Worker not monitoring**: Check task is active
4. **Extension not connecting**: Verify backend URL
5. **Google Sheets not syncing**: Check credentials

### Getting Help

1. Check logs first
2. Review documentation
3. Search GitHub issues
4. Ask in Telegram support group
5. Email support

---

**Last Updated**: May 22, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
