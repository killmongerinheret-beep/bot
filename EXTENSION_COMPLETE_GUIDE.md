# Browser Extension - Complete Guide

## 📋 Overview

The Vatican Ticket Monitor browser extension is a powerful auto-booking tool that integrates with your backend system to automatically book Vatican tickets when they become available.

---

## 🎯 Key Features

### 1. **Backend Listener Mode** (Recommended)
- Polls backend API every 10 seconds for available slots
- Opens separate incognito windows for each booking (parallel booking)
- Auto-fills forms with participant data from Google Sheets
- Completes entire booking flow automatically
- Supports up to 10 concurrent bookings

### 2. **Tab Reload Mode**
- Monitors Vatican website by reloading a tab periodically
- Visual check for available tickets
- Useful for manual monitoring

### 3. **API-Only Mode**
- Background checks using Vatican Search API
- Lightweight and fast
- No browser tabs needed

### 4. **Hold Mode**
- Keeps a slot alive by refreshing checkout page every 4 minutes
- Vatican holds slots for ~55 minutes
- Allows manual review before payment

---

## 🔄 Complete Workflow

### Step-by-Step Flow

```
1. USER CREATES TASK
   ↓
   [Telegram Bot] → User sends /monitor command
   ↓
   [Backend] → Creates MonitorTask in database
   ↓
   [Worker Vatican] → Starts monitoring Vatican API

2. WORKER FINDS AVAILABILITY
   ↓
   [Worker Vatican] → Calls Vatican Search API every 5 seconds
   ↓
   [Vatican API] → Returns available tickets
   ↓
   [Worker Vatican] → Creates HeldSlot in database
   ↓
   [Backend] → Reads participant data from Google Sheets
   ↓
   [Backend API] → Exposes slot via /api/v1/available-slots/

3. EXTENSION DETECTS SLOT
   ↓
   [Extension Background] → Polls backend every 10 seconds
   ↓
   [Extension] → Finds available slot
   ↓
   [Extension] → Opens incognito window with Vatican URL

4. AUTO-BOOKING FLOW
   ↓
   [Content Script] → Navigates to Vatican website
   ↓
   [Content Script] → Selects ticket (using fresh ticket_id from backend)
   ↓
   [Content Script] → Selects quantity (from slot.visitors)
   ↓
   [Content Script] → Selects EXACT time slot (strict mode)
   ↓
   [Content Script] → Clicks PROCEDI
   ↓
   [Content Script] → Fills checkout form with participants
   ↓
   [Content Script] → Waits for Turnstile (Cloudflare captcha)
   ↓
   [Content Script] → Clicks BUY button
   ↓
   [Content Script] → Waits for epay redirect
   ↓
   [Content Script] → Fills payment form (if card data available)
   ↓
   [Content Script] → Clicks PAY (if auto-pay enabled)
   ↓
   [Extension] → Marks slot as booked via API

5. COMPLETION
   ↓
   [Backend] → Updates slot status to 'paid'
   ↓
   [Telegram Bot] → Sends confirmation to user
   ↓
   [Extension] → Closes incognito window
```

---

## 🔌 Backend Integration

### API Endpoints Used

#### 1. **GET /api/v1/available-slots/**

**Purpose**: Get list of available slots ready for booking

**Request**:
```http
GET /api/v1/available-slots/?status=held&limit=10
Authorization: Bearer <api_key>
```

**Response**:
```json
{
  "slots": [
    {
      "id": 123,
      "date": "28/03/2026",
      "time": "10:00",
      "ticket_id": "2129030053",
      "ticket_name": "Vatican Museums - Standard Entry",
      "visitors": 2,
      "adult_count": 2,
      "child_count": 0,
      "language": null,
      "status": "held",
      "profile": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+39 123456789",
        "city": "Roma",
        "country": "Italia",
        "birth_date": "1990-01-15",
        "gender": "M",
        "language": "ITA"
      },
      "participants": [
        {
          "first_name": "John",
          "last_name": "Doe"
        },
        {
          "first_name": "Jane",
          "last_name": "Doe"
        }
      ],
      "card": {
        "number": "4111111111111111",
        "expiry": "12/25",
        "cvv": "123",
        "holder": "JOHN DOE"
      }
    }
  ],
  "count": 1,
  "timestamp": "2026-05-22T10:30:00Z"
}
```

#### 2. **POST /api/v1/slots/{slot_id}/mark-booked/**

**Purpose**: Mark slot as booked after successful booking

**Request**:
```http
POST /api/v1/slots/123/mark-booked/
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "reference": "VAT-2026-001",
  "epay_url": "https://epay.vatican.va/payment/abc123"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Slot 123 marked as booked",
  "slot": {
    "id": 123,
    "date": "28/03/2026",
    "time": "10:00",
    "status": "paying"
  }
}
```

#### 3. **POST /api/v1/google-sheets/sync/**

**Purpose**: Manually trigger Google Sheets sync

**Request**:
```http
POST /api/v1/google-sheets/sync/
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "agency_id": 1
}
```

**Response**:
```json
{
  "success": true,
  "message": "Synced 5 participants",
  "participants_count": 5
}
```

---

## 🎨 Extension Architecture

### Files Structure

```
browser-extension/
├── manifest.json          # Extension configuration
├── background.js          # Service worker (backend listener, polling)
├── content.js            # Content script (auto-booking logic)
├── popup.html            # Extension popup UI
├── popup.js              # Popup logic
├── popup.css             # Popup styles
├── settings.html         # Settings page
├── settings.js           # Settings logic
├── options.html          # Options page
├── options.js            # Options logic
└── icons/                # Extension icons
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

### Key Components

#### **background.js** (Service Worker)

**Responsibilities**:
- Poll backend API every 10 seconds
- Detect available slots
- Open incognito windows for booking
- Track active booking windows
- Manage processed slots (avoid duplicates)
- Send notifications

**Key Functions**:
```javascript
// Start backend listener
startBackendListener(config)

// Check backend for slots
checkBackendForAvailableSlots(config)

// Open incognito windows
openIncognitoBookingWindows(slots, config)

// Mark slot as booked
markSlotAsBooked(slotId)
```

#### **content.js** (Content Script)

**Responsibilities**:
- Navigate Vatican website
- Select tickets and time slots
- Fill checkout forms
- Handle Turnstile (Cloudflare captcha)
- Fill payment forms
- Complete booking

**Key Functions**:
```javascript
// Main auto-booking flow
startAutoBookingFlow(config)

// Select ticket by ID
selectTicket(config)

// Select time slot (STRICT MODE)
selectTimeSlot(preferredTime)

// Fill checkout form with participants
fillCheckoutFormWithParticipants(profile, participants, visitors)

// Fill payment form
fillPaymentForm(card, profile)

// Hold mode (keep slot alive)
startHoldMode(config)
```

#### **popup.js** (UI)

**Responsibilities**:
- Display monitoring status
- Show available slots
- Configure backend settings
- Start/stop monitoring
- Test slot creation

---

## ⚙️ Configuration

### Extension Settings

#### **Backend Listener Mode**

```javascript
{
  backendUrl: 'http://localhost:8000',
  apiKey: '',  // Optional for local testing
  maxConcurrentBookings: 10,
  holdMode: false,  // true = hold only, false = auto-book
  autoPay: true     // Auto-submit payment
}
```

#### **Profile Data** (for auto-booking)

```javascript
{
  firstName: 'John',
  lastName: 'Doe',
  email: 'john@example.com',
  phone: '+39 123456789',
  city: 'Roma',
  autoConfirm: true,  // Auto-click BUY button
  birthDate: {
    year: '1990',
    month: 'GEN',
    day: '15'
  }
}
```

---

## 🔒 Security Features

### 1. **Incognito Windows**
- Each booking runs in isolated incognito window
- No cookie conflicts between bookings
- Clean session for each attempt

### 2. **Processed Slots Tracking**
- Tracks slot IDs already processed
- Prevents duplicate booking attempts
- Resets when all windows close

### 3. **Rate Limiting Detection**
- Detects Vatican rate limiting
- Stops monitoring if rate limited
- Shows warning to user

### 4. **Turnstile Handling**
- Waits for Cloudflare Turnstile to complete
- Checks if BUY button is enabled
- Timeout after 30 seconds

---

## 🎯 Strict Time Selection

### Why Strict Mode?

The extension uses **STRICT TIME SELECTION** to ensure you only book the exact time you want.

**Behavior**:
- ✅ Only selects the EXACT time specified in the slot
- ❌ Does NOT select alternative times
- ❌ Does NOT select "first available"
- ✅ Cancels booking if exact time not found

**Example**:
```javascript
// Slot specifies 10:00
// Available times: 09:00, 09:30, 10:30, 11:00

// ❌ Will NOT select 09:30 or 10:30
// ✅ Will ONLY select 10:00
// ❌ If 10:00 not available, booking is cancelled
```

**Why This Matters**:
- Users have specific time preferences
- Booking wrong time wastes money
- Better to wait for correct time than book wrong one

---

## 🧪 Testing

### Test 1: Backend Connection

1. Open extension popup
2. Enable "Backend Listener Mode"
3. Enter backend URL: `http://localhost:8000`
4. Click "Start Backend Listener"
5. Open browser console (F12)
6. Check for: `✅ Backend listener started - polling every 10 seconds`

### Test 2: Create Test Slot

1. Click "🧪 Create Test Slot" button in extension
2. Extension calls backend API
3. Backend checks Vatican for real availability
4. If found, creates slot in database
5. Extension detects slot within 10 seconds
6. Incognito window opens automatically

### Test 3: Auto-Booking Flow

1. Watch incognito window
2. Extension navigates to Vatican
3. Selects ticket
4. Fills form with participant data
5. Completes booking
6. Marks slot as booked

### Test 4: Delete Test Slot

1. Click "🗑️ Delete Test" button
2. Extension calls backend API
3. Backend deletes test slots
4. Ready for next test

---

## 🐛 Troubleshooting

### Issue: Extension Not Detecting Slots

**Check**:
1. Backend URL correct in settings
2. Backend is running: `docker-compose ps`
3. Slots exist in database: Check `/api/v1/available-slots/`
4. Extension console for errors (F12)

**Solution**:
```javascript
// Check extension console
// Should see:
"🔄 Checking backend for available slots..."
"No available slots yet, continuing to poll..."

// If error:
"Backend API error: 404"  // Backend not running
"CORS error"              // CORS not configured
```

### Issue: Incognito Window Opens But Doesn't Book

**Check**:
1. Content script loaded (check console in incognito window)
2. Participant data available
3. Vatican website structure changed

**Solution**:
```javascript
// Open incognito window console (F12)
// Should see:
"Vatican Ticket Monitor - Content Script Loaded"
"Starting auto-booking flow..."
"Step 1/10: Selecting ticket... ✅"

// If stuck:
"❌ Failed to select ticket"  // Ticket ID invalid
"❌ Exact time not available"  // Time slot not found
"❌ No profile data"           // Missing participant data
```

### Issue: Form Not Filling Correctly

**Check**:
1. Participant data format
2. Vatican form selectors changed
3. Browser console errors

**Solution**:
```javascript
// Check participant data format
{
  "first_name": "John",  // ✅ Correct
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+39 123456789"
}

// NOT:
{
  "firstName": "John",   // ❌ Wrong (camelCase)
  "name": "John Doe"     // ❌ Wrong (combined)
}
```

### Issue: Payment Form Not Filling

**Check**:
1. Card data available in slot
2. Epay page loaded correctly
3. Datatrans iframe present

**Solution**:
```javascript
// Check card data format
{
  "number": "4111111111111111",  // ✅ No spaces
  "expiry": "12/25",              // ✅ MM/YY format
  "cvv": "123",                   // ✅ String
  "holder": "JOHN DOE"            // ✅ Uppercase
}
```

---

## 📊 Monitoring Extension Activity

### Extension Console

Open extension popup → Right-click → Inspect → Console

**Expected Messages**:
```
✅ Backend listener started - polling every 10 seconds
🔄 Checking backend for available slots...
No available slots yet, continuing to poll...
🎉 Found 1 available slots from backend!
📋 1 new slots to process
📦 Opening 1 incognito windows for parallel booking
✅ Opened incognito window #1 for 28/03/2026 10:00 (AUTO mode)
```

### Incognito Window Console

Open incognito window → F12 → Console

**Expected Messages**:
```
Vatican Ticket Monitor - Content Script Loaded
🚀 Auto-booking started...
⏳ Loading Vatican website...
🎫 Step 1/10: Selecting ticket...
✅ Clicked ticket button for: Vatican Museums - Standard Entry
👥 Step 2/10: Setting quantity...
⏰ Step 3/10: Selecting time slot...
✅ Selected EXACT time: 10:00
➡️ Step 4/10: Proceeding to checkout...
📝 Step 5/10: Filling form with participants...
🔐 Step 6/10: Solving Turnstile...
💳 Step 7/10: Confirming purchase...
⏳ Step 8/10: Waiting for payment page...
✅ Redirected to payment page
💳 Step 9/10: Filling payment details...
💰 Step 10/10: Submitting payment...
✅ Payment submitted! Waiting for confirmation...
🎉 Booking completed successfully!
```

---

## 🚀 Advanced Features

### 1. **Parallel Booking**

Book multiple dates simultaneously:

```javascript
// Extension opens 10 incognito windows at once
// Each window books a different date
// No conflicts (isolated sessions)

// Example:
Window 1: 28/03/2026 10:00
Window 2: 29/03/2026 11:00
Window 3: 30/03/2026 09:00
...
Window 10: 06/04/2026 14:00
```

### 2. **Hold Mode**

Keep slot alive without booking:

```javascript
// Enable hold mode in extension settings
holdMode: true

// Extension will:
// 1. Navigate to checkout
// 2. Fill form
// 3. Refresh page every 4 minutes
// 4. Keep slot alive for up to 55 minutes
// 5. Show "Complete Booking" button
// 6. User clicks when ready
```

### 3. **Auto-Pay**

Automatically submit payment:

```javascript
// Enable auto-pay in extension settings
autoPay: true

// Extension will:
// 1. Fill payment form
// 2. Click PAY button
// 3. Wait for 3DS approval (if required)
// 4. Complete booking
```

### 4. **Timing Display**

Real-time monitoring stats:

```javascript
// Extension popup shows:
- Start Time: 10:30:00
- Last Check: 10:35:45
- Next Check: 10:35:55 (in 10s)
- Total Checks: 35
- Check Interval: 10 seconds
- Running Duration: 5m 45s
```

---

## 📚 Code Examples

### Example 1: Start Backend Listener

```javascript
// In popup.js
chrome.runtime.sendMessage({
  action: 'startBackendListener',
  config: {
    backendUrl: 'http://localhost:8000',
    apiKey: '',
    maxConcurrentBookings: 10,
    holdMode: false,
    autoPay: true
  }
});
```

### Example 2: Check Available Slots

```javascript
// In background.js
async function checkBackendForAvailableSlots(config) {
  const response = await fetch(`${config.backendUrl}/api/v1/available-slots/`, {
    headers: {
      'Authorization': `Bearer ${config.apiKey}`,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  
  if (data.slots && data.slots.length > 0) {
    await openIncognitoBookingWindows(data.slots, config);
  }
}
```

### Example 3: Auto-Book Slot

```javascript
// In content.js
async function startAutoBookingFlow(config) {
  // Step 1: Select ticket
  await selectTicket(config);
  
  // Step 2: Select quantity
  await selectQuantity(config.visitors);
  
  // Step 3: Select time slot (STRICT)
  const slotSelected = await selectTimeSlot(config.preferredTime);
  if (!slotSelected) {
    notifyProgress('❌ Exact time not available', 'error');
    return;
  }
  
  // Step 4: Proceed to checkout
  await clickProcedi();
  
  // Step 5: Fill form
  await fillCheckoutFormWithParticipants(
    config.profile,
    config.participants,
    config.visitors
  );
  
  // Step 6: Complete booking
  await clickBuyButton();
  
  // Step 7: Fill payment
  const epayUrl = await waitForEpayRedirect();
  if (epayUrl && config.card) {
    await fillPaymentForm(config.card, config.profile);
    if (config.autoPay) {
      await clickPayButton();
    }
  }
}
```

---

## 🎓 Best Practices

### 1. **Use Backend Listener Mode**
- Most reliable
- Parallel booking support
- Automatic participant data

### 2. **Enable Strict Time Selection**
- Only books exact time
- Prevents wrong bookings
- Better user experience

### 3. **Test with Test Slots**
- Use "Create Test Slot" button
- Verify complete flow
- Check participant data

### 4. **Monitor Extension Console**
- Check for errors
- Verify API calls
- Track booking progress

### 5. **Use Hold Mode for Review**
- Review booking before payment
- Verify participant data
- Manual payment control

---

## 📖 Related Documentation

- **PC Setup Guide**: `PC_SETUP_GUIDE.md`
- **System Workflow**: `COMPLETE_SYSTEM_WORKFLOW.md`
- **Vatican Bot Rules**: `VATICAN_BOT_RULES.md`
- **Extension Quick Start**: `browser-extension/QUICK_START.md`

---

**Last Updated**: May 22, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
