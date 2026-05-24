# Complete Workflow Guide - Telegram Bot + Browser Extension

**Date:** May 14, 2026  
**Status:** Comprehensive Documentation

---

## 🎯 System Overview

Your Vatican ticket booking system has **TWO MAIN WORKFLOWS**:

1. **Telegram Bot Workflow** - Create monitors and manage tasks
2. **Browser Extension Workflow** - Auto-complete bookings

Both work together but can also work independently.

---

## 📱 TELEGRAM BOT WORKFLOW

### Step-by-Step User Journey

#### 1. **User Starts Bot** (`/start`)

```
User → Telegram → /start
  ↓
Bot checks if chat is linked to agency
  ↓
If linked → Show main menu
If not linked → Show error + chat ID
```

**Main Menu Options:**
- 🎫 Create Monitor
- 📊 View Status  
- 👤 Set Profile
- ℹ️ Help

---

#### 2. **Create Monitor Flow** (Click "🎫 Create Monitor")

**Step 2.1: Select Date**
```
Bot → Shows calendar keyboard
User → Clicks date (e.g., June 15, 2026)
  ↓
Stored in context: ud['date'] = '2026-06-15'
```

**Step 2.2: Select Adults**
```
Bot → Shows number buttons (1-10)
User → Clicks number (e.g., 2 adults)
  ↓
Stored: ud['adult_count'] = 2
```

**Step 2.3: Select Children**
```
Bot → Shows number buttons (0-10)
User → Clicks number (e.g., 0 children)
  ↓
Stored: ud['child_count'] = 0
Total visitors: ud['visitors'] = 2
```

**Step 2.4: Select Ticket Type**
```
Bot → Shows options:
  - 🎫 Standard Entry
  - 👥 Guided Tour
  
User → Clicks "Standard Entry"
  ↓
Stored: 
  ud['ticket_type'] = 0
  ud['ticket_name'] = "Musei Vaticani - Biglietti d'ingresso"
  ud['ticket_label'] = 'Standard Entry'
```

**If Guided Tour selected:**
```
Bot → Shows language options:
  - 🇬🇧 English
  - 🇮🇹 Italiano
  - 🇫🇷 Français
  - 🇩🇪 Deutsch
  - 🇪🇸 Español
  
User → Clicks language
  ↓
Stored: ud['language'] = 'ENG'
```

**Step 2.5: Select Mode**
```
Bot → Shows tier options:
  - 🔔 Notify Only (all plans)
  - ⚡ Snipe (agency plan only)
  
User → Clicks "⚡ Snipe"
  ↓
Stored: ud['tier'] = 'snipe'
```

**Step 2.6: Enter Participant Names** (if Snipe mode)
```
Bot → "Enter name of Adult 1/2"
User → Types "Mario Rossi"
  ↓
Bot → "Enter name of Adult 2/2"
User → Types "Luigi Verdi"
  ↓
Stored: ud['snipe_participants'] = [
  {first_name: 'Mario', last_name: 'Rossi'},
  {first_name: 'Luigi', last_name: 'Verdi'}
]
```

**Step 2.7: Select Time Slots**
```
Bot → Shows time slot grid (08:00 - 17:30)
User → Taps times to toggle selection
User → Clicks "✅ Done (3 selected)"
  ↓
Stored: ud['preferred_times'] = ['09:00', '10:00', '14:00']
```

**Step 2.8: Confirm**
```
Bot → Shows summary:
  📅 Date: 2026-06-15
  👥 Visitors: 2 (2 Adults, 0 Children)
  🎫 Ticket: Standard Entry
  🎯 Mode: ⚡ Snipe
  👤 Participants: Mario Rossi, Luigi Verdi
  ⏰ Time: 09:00, 10:00, 14:00
  
User → Clicks "✅ Confirm"
```

---

#### 3. **Task Creation** (Backend Processing)

```python
# In telegram_bot.py - on_callback() function

# Create MonitorTask in database
task = MonitorTask.objects.create(
    agency_id=ud['agency_id'],
    site='vatican',
    area_name='Musei Vaticani',
    dates=[ud['date']],  # JSON array
    preferred_times=ud['preferred_times'],  # JSON array
    visitors=ud['visitors'],
    adult_count=ud['adult_count'],
    child_count=ud['child_count'],
    ticket_type=ud['ticket_type'],
    ticket_name=ud['ticket_name'],
    language=ud.get('language'),
    tier=ud['tier'],  # 'notify' or 'snipe'
    participants_json=json.dumps(ud.get('snipe_participants', [])),
    match_strategy='exact',
    notification_mode='telegram',
    is_active=True,
    last_status='pending',
    check_interval=5  # seconds
)
```

**Task is now in database and will be picked up by worker!**

---

#### 4. **Worker Monitoring** (Automatic)

```python
# In backend/monitors/tasks_search_api.py

@shared_task
def instant_sniper_scan():
    """Orchestrator - runs every 10 seconds"""
    
    # Get all active tasks
    tasks = MonitorTask.objects.filter(is_active=True)
    
    # For each task, dispatch a check
    for task in tasks:
        for date in task.dates:
            run_search_api_vatican_monitor.delay(
                task_id=task.id,
                date=date,
                visitors=task.visitors,
                ticket_type=task.ticket_type,
                language=task.language
            )
```

**Worker checks Vatican API:**
```python
# In worker_vatican/search_api_monitor.py

def check_availability(task_id, date, visitors, ticket_type, language):
    # Step 1: Search API - Get fresh ticket IDs
    search_url = f"{BASE}/api/search/resultPerTag"
    params = {
        'lang': 'it',
        'visitorNum': visitors,
        'visitDate': date,  # DD/MM/YYYY
        'area': '1',
        'who': '',
        'page': '0',
        'tag': 'MV-Biglietti' if ticket_type == 0 else 'MV-Visite-Guidate'
    }
    
    response = requests.get(search_url, params=params)
    data = response.json()
    
    # Step 2: Match ticket by name
    ticket = find_ticket_by_name(data['visits'], ticket_type)
    
    if not ticket:
        return  # No matching ticket
    
    # Step 3: Check if search API says SOLD_OUT
    if ticket['availability'] == 'SOLD_OUT':
        return  # Skip timeavail call
    
    # Step 4: Timeavail API - Get available slots
    timeavail_url = f"{BASE}/api/visit/timeavail"
    params = {
        'lang': 'it',
        'visitLang': language or '',  # Empty for standard
        'visitTypeId': ticket['id'],  # Fresh ID!
        'visitorNum': visitors,
        'visitDate': date
    }
    
    response = requests.get(timeavail_url, params=params)
    data = response.json()
    
    # Step 5: Filter available slots
    available_slots = [
        slot for slot in data['timetable']
        if slot['availability'] == 'AVAILABLE'
    ]
    
    if available_slots:
        # SLOTS FOUND!
        handle_slots_found(task, date, available_slots)
```

---

#### 5. **When Slots Found** (Notification + Hold)

```python
def handle_slots_found(task, date, slots):
    # Create HeldSlot records
    for slot in slots:
        HeldSlot.objects.create(
            task=task,
            date=date,
            slot_time=slot['time'],
            slot_id=slot['id'],
            ticket_id=task.ticket_id,
            ticket_name=task.ticket_name,
            visitors=task.visitors,
            adult_count=task.adult_count,
            child_count=task.child_count,
            status='held',
            payment_ready=False,
            hold_started_at=timezone.now()
        )
    
    # Send Telegram notification
    send_telegram_notification(
        chat_id=task.agency.telegram_chat_id,
        message=f"🎉 {len(slots)} slots available!\n"
                f"Date: {date}\n"
                f"Times: {', '.join(s['time'] for s in slots)}\n"
                f"Ticket: {task.ticket_name}"
    )
```

**User receives Telegram message:**
```
🎉 3 slots available!
Date: 15/06/2026
Times: 09:00, 10:00, 14:00
Ticket: Musei Vaticani - Biglietti d'ingresso

[Book Now]
```

---

## 🌐 BROWSER EXTENSION WORKFLOW

### Mode 1: Manual Monitoring (Current Implementation)

#### 1. **User Opens Extension Popup**

```
User → Clicks extension icon
  ↓
Popup shows:
  - Date selector
  - Visitors input
  - Ticket type dropdown
  - Check interval slider
  - Monitor mode selector
  - Start/Stop buttons
```

#### 2. **User Configures Monitoring**

```
User fills in:
  Date: 2026-06-15
  Visitors: 2
  Ticket Type: Standard Entry
  Check Interval: 10 seconds
  Monitor Mode: API Only (or Tab Reload)
  
User → Clicks "Start Monitoring"
```

#### 3. **Extension Starts Checking**

**API Mode:**
```javascript
// In background.js

async function checkAvailability() {
    // Step 1: Search API
    const searchUrl = `${VATICAN_BASE}/api/search/resultPerTag`;
    const searchParams = {
        lang: 'it',
        visitorNum: config.visitors,
        visitDate: config.date,  // DD/MM/YYYY
        area: '1',
        who: '',
        page: '0',
        tag: 'MV-Biglietti'
    };
    
    const searchResponse = await fetch(searchUrl + '?' + new URLSearchParams(searchParams));
    const searchData = await searchResponse.json();
    
    // Step 2: Find ticket
    const ticket = findTicket(searchData.visits, config.ticketType);
    
    // Step 3: Check timeavail
    const timeavailUrl = `${VATICAN_BASE}/api/visit/timeavail`;
    const timeavailParams = {
        lang: 'it',
        visitLang: config.language || '',
        visitTypeId: ticket.id,
        visitorNum: config.visitors,
        visitDate: config.date
    };
    
    const timeavailResponse = await fetch(timeavailUrl + '?' + new URLSearchParams(timeavailParams));
    const timeavailData = await timeavailResponse.json();
    
    // Step 4: Filter available slots
    const availableSlots = timeavailData.timetable.filter(
        slot => slot.availability === 'AVAILABLE'
    );
    
    if (availableSlots.length > 0) {
        // FOUND!
        sendNotification('Vatican Tickets Available!', `${availableSlots.length} slots found`);
        
        // If auto-booking enabled, trigger it
        if (config.autoBooking) {
            triggerAutoBooking(config, availableSlots[0]);
        }
    }
}
```

**Tab Reload Mode:**
```javascript
// In background.js

async function startTabMonitoring(config) {
    // Open Vatican tab
    const url = `https://tickets.museivaticani.va/home/fromtag/${config.visitors}/${timestamp}/MV-Biglietti/1`;
    const tab = await chrome.tabs.create({ url });
    
    // Reload tab every X seconds
    setInterval(async () => {
        await chrome.tabs.reload(tab.id);
        
        // Content script checks page
        chrome.tabs.sendMessage(tab.id, {
            action: 'checkAvailabilityOnPage'
        });
    }, config.checkInterval * 1000);
}
```

---

### Mode 2: Backend Listener (Designed but Not Fully Integrated)

#### 1. **User Enables Backend Listener**

```
User → Opens extension popup
User → Selects "Backend Listener" mode
User → Enters:
  - Backend URL: http://localhost:8000
  - API Key: (optional)
  - Max Concurrent Bookings: 10
  
User → Clicks "Start Monitoring"
```

#### 2. **Extension Polls Backend**

```javascript
// In background.js

async function checkBackendForAvailableSlots(config) {
    // Poll backend API every 10 seconds
    const response = await fetch(`${config.backendUrl}/api/v1/available-slots/`, {
        headers: {
            'Authorization': `Bearer ${config.apiKey}`
        }
    });
    
    const data = await response.json();
    
    if (data.slots && data.slots.length > 0) {
        // SLOTS FOUND!
        console.log(`Found ${data.slots.length} available slots from backend`);
        
        // Open incognito windows for parallel booking
        await openIncognitoBookingWindows(data.slots, config);
    }
}
```

#### 3. **Extension Opens Incognito Windows**

```javascript
async function openIncognitoBookingWindows(slots, config) {
    for (const slot of slots) {
        // Open NEW incognito window for each slot
        const window = await chrome.windows.create({
            url: 'https://tickets.museivaticani.va/home',
            incognito: true,  // Isolated session!
            focused: false,
            type: 'normal',
            state: 'maximized'
        });
        
        // Wait for page to load
        setTimeout(async () => {
            const tabs = await chrome.tabs.query({ windowId: window.id });
            
            // Send auto-booking message to content script
            chrome.tabs.sendMessage(tabs[0].id, {
                action: 'startAutoBooking',
                config: {
                    date: slot.date,
                    time: slot.time,
                    visitors: slot.visitors,
                    ticketId: slot.ticket_id,
                    profile: slot.profile,
                    participants: slot.participants,
                    card: slot.card,
                    autoConfirm: true
                }
            });
        }, 5000);
    }
}
```

---

### Mode 3: Auto-Booking Flow (Content Script)

#### When Slots Found, Content Script Takes Over

```javascript
// In content.js

async function startAutoBookingFlow(config) {
    // Step 1: Select ticket
    notifyProgress('🎫 Step 1/10: Selecting ticket...');
    await selectTicket(config);
    await sleep(2000);
    
    // Step 2: Set quantity
    notifyProgress('👥 Step 2/10: Setting quantity...');
    await selectQuantity(config.visitors);
    await sleep(1500);
    
    // Step 3: Select time slot (STRICT - exact time only)
    notifyProgress('⏰ Step 3/10: Selecting time slot...');
    const slotSelected = await selectTimeSlot(config.preferredTime);
    
    if (!slotSelected) {
        notifyProgress('❌ Exact time not available - cancelling');
        return;
    }
    await sleep(2000);
    
    // Step 4: Click PROCEDI
    notifyProgress('➡️ Step 4/10: Proceeding to checkout...');
    await clickProcedi();
    await sleep(5000);
    
    // Step 5: Fill form with participants
    notifyProgress('📝 Step 5/10: Filling form...');
    await fillCheckoutFormWithParticipants(
        config.profile,
        config.participants,
        config.visitors
    );
    await sleep(3000);
    
    // Step 6: Solve Turnstile
    notifyProgress('🔐 Step 6/10: Solving Turnstile...');
    await waitForTurnstile();
    await sleep(2000);
    
    // Step 7: Click BUY
    notifyProgress('💳 Step 7/10: Confirming purchase...');
    await clickBuyButton();
    await sleep(5000);
    
    // Step 8: Wait for epay redirect
    notifyProgress('⏳ Step 8/10: Waiting for payment page...');
    const epayUrl = await waitForEpayRedirect();
    
    // Step 9: Fill payment form (if card data available)
    if (config.card) {
        notifyProgress('💳 Step 9/10: Filling payment details...');
        await fillPaymentForm(config.card, config.profile);
        await sleep(3000);
        
        // Step 10: Click PAY (if auto-pay enabled)
        if (config.autoPay) {
            notifyProgress('💰 Step 10/10: Submitting payment...');
            await clickPayButton();
            
            notifyProgress('✅ Payment submitted!');
        } else {
            notifyProgress('✅ Card filled - review and click PAY manually');
        }
    } else {
        notifyProgress('✅ Booking completed! Complete payment manually.');
    }
}
```

---

## 🔄 COMPLETE INTEGRATED WORKFLOW

### Ideal Flow (When Fully Integrated)

```
1. USER CREATES MONITOR VIA TELEGRAM
   ↓
2. TASK SAVED IN DATABASE
   ↓
3. WORKER MONITORS VATICAN API (every 10s)
   ↓
4. WORKER FINDS AVAILABLE SLOT
   ↓
5. WORKER CREATES HELDSLOT IN DATABASE
   ↓
6. TELEGRAM NOTIFICATION SENT
   ↓
7. EXTENSION POLLS BACKEND API (every 10s)
   ↓
8. EXTENSION DETECTS NEW HELDSLOT
   ↓
9. EXTENSION OPENS INCOGNITO WINDOW
   ↓
10. CONTENT SCRIPT AUTO-FILLS FORM
    ↓
11. CONTENT SCRIPT COMPLETES BOOKING
    ↓
12. HELDSLOT MARKED AS payment_ready=true
    ↓
13. USER RECEIVES CONFIRMATION EMAIL
```

---

## 📊 Current Status vs Designed

### ✅ What's Working

| Component | Status |
|-----------|--------|
| Telegram bot accepting commands | ✅ Working |
| Creating monitor tasks | ✅ Working |
| Worker monitoring Vatican API | ✅ Working |
| Search API + timeavail checks | ✅ Working |
| Creating HeldSlot records | ✅ Working |
| Telegram notifications | ✅ Working |
| Extension manual monitoring | ✅ Working |
| Extension auto-booking flow | ✅ Working |

### ⚠️ What's Missing

| Component | Status |
|-----------|--------|
| Backend API endpoint `/api/v1/available-slots/` | ❌ Not implemented |
| Extension polling backend | ❌ Not connected |
| Extension fetching buyer profiles | ❌ Not synced |
| Extension fetching participant names | ❌ Not synced |
| Automatic incognito window opening | ❌ Not triggered |

---

## 🎯 Key Differences

### Telegram Bot
- **Purpose:** User interface for creating monitors
- **Runs:** On server (Docker container)
- **Stores:** Tasks in PostgreSQL database
- **Monitors:** Via backend workers with proxies
- **Notifies:** Via Telegram messages

### Browser Extension
- **Purpose:** Auto-complete bookings
- **Runs:** In user's browser
- **Stores:** Config in Chrome storage
- **Monitors:** Via direct API calls OR backend polling
- **Notifies:** Via desktop notifications

---

## 📝 Summary

**Telegram Bot Flow:**
1. User creates monitor → Task in database
2. Worker checks Vatican API → Finds slots
3. Worker creates HeldSlot → Sends notification
4. User receives Telegram alert

**Extension Flow (Current):**
1. User configures extension → Starts monitoring
2. Extension checks Vatican API → Finds slots
3. Extension shows notification → Opens booking page
4. User completes booking manually OR auto-booking

**Extension Flow (Designed):**
1. Extension polls backend → Detects HeldSlot
2. Extension opens incognito window → Loads Vatican
3. Content script auto-fills form → Completes booking
4. HeldSlot marked as booked → User gets confirmation

---

**The missing piece is the backend API endpoint that the extension can poll to get held slots!**

