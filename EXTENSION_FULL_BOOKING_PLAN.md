# 🎯 Extension Full Booking Flow Implementation Plan

## Current State vs Desired State

### Current (Incomplete):
- ❌ Extension opens window
- ❌ Tries to select ticket (fails)
- ❌ Stops there

### Desired (Complete Flow):
- ✅ Backend finds available slot via API
- ✅ Extension receives slot data (date, time, ticket_id, visitors)
- ✅ Extension opens incognito window
- ✅ Extension navigates to Vatican ticket page
- ✅ Extension selects correct ticket
- ✅ Extension sets quantity (visitors)
- ✅ Extension selects time slot
- ✅ Extension clicks PROCEDI
- ✅ Extension fills booking form (name, email, phone, etc.)
- ✅ Extension fills birth date
- ✅ Extension checks GDPR boxes
- ✅ Extension clicks BUY
- ✅ Extension waits for epay redirect
- ✅ User completes payment manually (or extension fills card if configured)

---

## Implementation Steps

### Step 1: Update Backend to Pass Complete Slot Data ✅
**Already done** - Backend passes:
```json
{
  "id": 123,
  "date": "15/06/2026",
  "time": "09:00",
  "ticket_id": "2129030053",
  "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
  "visitors": 2,
  "language": null
}
```

### Step 2: Update content.js to Follow Complete Flow
**File:** `browser-extension/content.js`

**Add these functions (from test_full_reservation.py):**

1. `navigateToTicketPage()` - Navigate to deep link
2. `selectTicketById()` - Click ticket button by ID
3. `setQuantity()` - Set visitor count
4. `selectTimeSlot()` - Click time slot
5. `clickProcedi()` - Click PROCEDI button
6. `fillBookingForm()` - Fill all form fields
7. `setBirthDate()` - Handle calendar picker
8. `checkGDPRBoxes()` - Check consent boxes
9. `clickBuy()` - Submit booking
10. `waitForEpay()` - Wait for payment redirect

### Step 3: Update background.js
**File:** `browser-extension/background.js`

**Changes:**
- Pass complete slot data to content script
- Include booking profile from extension settings
- Wait longer for booking to complete (60s instead of 5s)

### Step 4: Add Booking Profile to Extension Settings
**File:** `browser-extension/options.html` + `options.js`

**Add fields:**
- First Name
- Last Name
- Email
- Phone
- City
- Birth Date
- Country

### Step 5: Test Flow
1. Create test slot
2. Extension opens window
3. Extension completes full booking
4. User sees epay payment page
5. User completes payment

---

## Code Structure

### content.js Flow:
```javascript
async function startAutoBookingFlow(config) {
  // config contains: slot, profile
  
  // Step 1: Navigate to ticket page
  await navigateToTicketPage(config.slot);
  
  // Step 2: Select ticket
  await selectTicketById(config.slot.ticket_id);
  
  // Step 3: Set quantity
  await setQuantity(config.slot.visitors);
  
  // Step 4: Select time
  await selectTimeSlot(config.slot.time);
  
  // Step 5: Click PROCEDI
  await clickProcedi();
  
  // Step 6: Fill form
  await fillBookingForm(config.profile, config.slot);
  
  // Step 7: Check GDPR
  await checkGDPRBoxes();
  
  // Step 8: Click BUY
  await clickBuy();
  
  // Step 9: Wait for epay
  const epayUrl = await waitForEpay();
  
  // Done - user completes payment
  notifySuccess(`Ready for payment: ${epayUrl}`);
}
```

---

## Benefits

### For User:
- ✅ **Fully automated** - No manual clicking needed
- ✅ **Faster** - Extension completes booking in 10-15 seconds
- ✅ **Reliable** - Follows proven Playwright flow
- ✅ **Convenient** - Just complete payment at the end

### For System:
- ✅ **Lighter** - No Playwright/nodriver needed
- ✅ **Scalable** - Can handle multiple bookings simultaneously
- ✅ **Flexible** - Works on any computer with Chrome

---

## Timeline

1. **Update content.js** - 30 minutes (copy logic from test_full_reservation.py)
2. **Update background.js** - 10 minutes (pass profile data)
3. **Add profile settings** - 20 minutes (UI + storage)
4. **Test** - 15 minutes
5. **Total:** ~75 minutes

---

## Next Steps

1. Should I proceed with implementing this?
2. Do you want the extension to also fill payment card details, or stop at epay page?
3. Should the booking profile be:
   - Stored in extension settings (user fills once)
   - Passed from backend (from Telegram bot user data)
   - Both options available?

Let me know and I'll implement it!
