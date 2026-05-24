# Fix: General Error After Clicking ACQUISTA

## Problem Identified ✅

The **"General Error"** (500 Internal Server Error) happens because you're using **test data with fake Vatican IDs**.

### What's Wrong:

Your test data (`create_test_data_docker.py`) creates fake IDs:
```python
slot_id='TEST_1'              # ❌ Fake
ticket_id='TEST_TICKET_123'   # ❌ Fake  
jsessionid='TEST_SESSION'     # ❌ Fake
recap_id='TEST_RECAP_1'       # ❌ Fake
```

When the extension navigates to Vatican and goes through the booking flow, Vatican generates **real IDs** based on the current session. But when you click ACQUISTA, Vatican tries to create a reservation and looks up these IDs in their database - **they don't exist** → 500 Error.

### From HAR File Analysis:

The reservation request contained:
```json
{
  "visitId": "2026*9930",           // ❌ Test ID (asterisk is suspicious)
  "visitTypeId": 1368845133,        // ❌ Stale/hardcoded ID
  "reservationId": "2L2NFF9R0000002SB",  // ❌ Test ID
  "recapId": "2026/9930/100"        // ❌ Test ID
}
```

Vatican's backend rejected this because these IDs don't exist in their system.

---

## Solution Options

### Option 1: Use REAL Vatican Data (Recommended for Production)

**Stop using test data.** Let the system work naturally:

1. **Create Real Monitoring Tasks**
   ```python
   # In Django shell or create_real_tasks.py
   task = MonitorTask.objects.create(
       agency=agency,
       site='vatican',
       dates=['2026-06-15'],  # Real future date
       preferred_times=['09:00', '10:00'],
       visitors=2,
       ticket_type=0,
       ticket_name='Vatican Museums - Standard Entry',
       is_active=True
   )
   ```

2. **Start Worker to Monitor Vatican**
   ```bash
   docker-compose up worker_vatican
   ```

3. **Worker Finds Real Slots**
   - Worker calls Vatican Search API
   - Gets fresh ticket IDs
   - Checks availability
   - When slot is available, creates HeldSlot with **REAL IDs**:
     - Real JSESSIONID from Vatican
     - Real ticket_id from Search API
     - Real recap_id from booking flow

4. **Extension Books with Real Data**
   - Extension gets slot from backend
   - Navigates to Vatican with real session
   - Fills form with your profile data
   - Clicks ACQUISTA
   - Vatican creates reservation with real IDs
   - ✅ **Success!**

---

### Option 2: Manual Extension Test (Quick Test for Form Filling)

If you just want to test that the extension **fills the form correctly**, skip the backend:

1. **Open Vatican Manually**
   - Go to https://tickets.museivaticani.va/
   - Select a real available date (e.g., June 2026)
   - Select ticket type
   - Select time slot
   - Click PROCEDI to get to checkout page

2. **Let Extension Fill Form**
   - Extension detects checkout page
   - Fills form with your profile data
   - Clicks checkboxes
   - Fills phone without + sign

3. **Verify Form Data**
   - Check that all fields are filled correctly
   - Check that phone is `393331234567` (no +)
   - Check that checkboxes are checked

4. **Click ACQUISTA Manually**
   - Review the filled form
   - Click ACQUISTA yourself
   - See if Vatican accepts it

This tests the **form filling** without needing the backend.

---

### Option 3: Hybrid Approach (Test Form, Skip Payment)

1. **Use Real Dates but Don't Complete Payment**
   - Create real monitoring tasks
   - Let worker find real slots
   - Extension fills form and clicks ACQUISTA
   - **Stop before payment** (don't actually pay)

2. **Verify Extension Behavior**
   - Check that form is filled correctly
   - Check that ACQUISTA is clicked
   - Check that payment page loads
   - **Don't complete payment** (just testing)

---

## Why Test Data Doesn't Work

### The Vatican Booking Flow:

```
1. User visits Vatican website
   ↓
2. Vatican creates session (JSESSIONID)
   ↓
3. User selects date/ticket
   ↓
4. Vatican assigns visitId and visitTypeId
   ↓
5. User selects time
   ↓
6. Vatican creates recap (recapId)
   ↓
7. User clicks PROCEDI
   ↓
8. Vatican generates reservationId
   ↓
9. User fills form
   ↓
10. User clicks ACQUISTA
    ↓
11. Vatican validates:
    - Is JSESSIONID valid? ✅
    - Does visitId exist? ✅
    - Does recapId exist? ✅
    - Does reservationId exist? ✅
    ↓
12. Vatican creates reservation
    ↓
13. Success! Redirect to payment
```

### With Test Data:

```
1. Extension gets test slot from backend
   - slot_id: "TEST_1"
   - jsessionid: "TEST_SESSION"
   - ticket_id: "TEST_TICKET_123"
   ↓
2. Extension navigates to Vatican
   ↓
3. Vatican creates NEW session (different from TEST_SESSION)
   ↓
4. Extension goes through booking flow
   ↓
5. Vatican assigns REAL visitId (not "2026*9930")
   ↓
6. Extension clicks ACQUISTA
   ↓
7. Vatican validates:
    - Is JSESSIONID valid? ✅ (real session)
    - Does visitId exist? ❌ (mismatch between test and real)
    - Does recapId exist? ❌ (test ID doesn't exist)
    - Does reservationId exist? ❌ (test ID doesn't exist)
    ↓
8. Vatican rejects: "General Error" (500)
```

---

## Recommended Next Steps

### For Testing Form Filling Only:
1. Use **Option 2** (Manual Extension Test)
2. Open Vatican manually
3. Get to checkout page
4. Let extension fill form
5. Verify form data is correct
6. Click ACQUISTA manually to test

### For Testing Full Flow:
1. Use **Option 1** (Real Vatican Data)
2. Create real monitoring task with future date
3. Start worker to monitor Vatican
4. Wait for worker to find available slot
5. Extension books automatically with real data
6. Complete payment (or stop before payment)

### For Development:
1. Use **Option 2** for quick form testing
2. Use **Option 1** for end-to-end testing
3. Don't use test data with fake IDs

---

## What to Change

### ❌ Don't Do This:
```python
# create_test_data_docker.py
slot = HeldSlot.objects.create(
    slot_id='TEST_1',              # Fake ID
    ticket_id='TEST_TICKET_123',   # Fake ID
    jsessionid='TEST_SESSION',     # Fake session
    recap_id='TEST_RECAP_1'        # Fake ID
)
```

### ✅ Do This Instead:
```python
# Let worker create slots with real data
# Worker will call Vatican API and get:
slot = HeldSlot.objects.create(
    slot_id='real_slot_id_from_vatican',
    ticket_id='2129030053',  # Real ID from Search API
    jsessionid='ABC123XYZ',  # Real session from Vatican
    recap_id='2026/12345/100'  # Real recap from Vatican
)
```

---

## Quick Test Script

If you want to test the extension quickly without backend:

```javascript
// In browser console on Vatican checkout page
// Simulate extension filling form
const profile = {
  firstName: 'John',
  lastName: 'Doe',
  email: 'john.doe@example.com',
  phone: '393331234567',  // No + sign
  city: 'Rome',
  birthDate: '1990-01-01'
};

// Fill fields
document.querySelector("[data-cy='managerSurname']").value = profile.lastName;
document.querySelector("[data-cy='managerName']").value = profile.firstName;
document.querySelector("[data-cy='managerEmail']").value = profile.email;
document.querySelector("[data-cy='managerConfirmEmail']").value = profile.email;
document.querySelector("[data-cy='managerPhone']").value = profile.phone;
document.querySelector("[data-cy='managerCity']").value = profile.city;

// Click checkboxes
document.querySelector('#mat-mdc-checkbox-1-input').click();
setTimeout(() => {
  document.querySelector("[data-cy='purchase-rules-close-btn']").click();
  document.querySelector('#mat-mdc-checkbox-4-input').click();
}, 2000);

console.log('Form filled! Check if data is correct, then click ACQUISTA manually.');
```

---

## Summary

**Problem:** Test data uses fake Vatican IDs that don't exist in Vatican's system.

**Solution:** Use real Vatican data from worker monitoring, or test form filling manually without backend.

**Key Insight:** The extension should work with **real Vatican sessions and IDs**, not test data. Test data is only useful for testing the backend API structure, not for actual booking.

**Next Step:** Choose Option 1 (real data) or Option 2 (manual test) and test again.

---

**Status:** ✅ Issue identified and solution provided
**Recommendation:** Use Option 2 for quick form testing, then Option 1 for full flow
