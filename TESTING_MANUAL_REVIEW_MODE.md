# Testing Manual Review Mode + Google Sheets

## Changes Made ✅

### 1. Extension Now Stops at Checkout (No Auto-Click ACQUISTA)

The extension will now:
1. ✅ Navigate to Vatican deep link
2. ✅ Select ticket
3. ✅ Set quantity
4. ✅ Select time slot
5. ✅ Click PROCEDI
6. ✅ Fill checkout form with profile data
7. ✅ Click GDPR checkboxes
8. ✅ Close modal
9. ✅ Solve Turnstile (if present)
10. ⏸️ **STOP HERE** - Wait for manual review

**What's disabled:**
- ❌ Clicking ACQUISTA button (you do this manually)
- ❌ Waiting for payment page
- ❌ Filling payment form
- ❌ Clicking PAY button

### 2. Console Logs for Debugging

When the extension stops, you'll see:
```
🎉 Auto-booking stopped at checkout page
📋 Form has been filled with:
   - Profile data (name, email, phone, etc.)
   - Participant information
   - GDPR checkboxes checked
   - Turnstile solved (if present)

👉 Next steps:
   1. Review all form fields
   2. Verify checkboxes are checked
   3. Click ACQUISTA button manually
   4. Complete payment if needed
```

### 3. Browser Notification

You'll get a notification:
```
Form Ready for Review
2026-08-25 09:00 - Form filled, please review and click ACQUISTA manually
```

---

## Testing Steps

### Step 1: Setup Google Sheets (Optional)

If you want to test Google Sheets integration:

#### 1.1 Create Google Service Account
```bash
# Go to Google Cloud Console
# https://console.cloud.google.com/

# 1. Create a new project (or use existing)
# 2. Enable Google Sheets API
# 3. Create Service Account
# 4. Download JSON key file
# 5. Save as google_credentials.json
```

#### 1.2 Share Google Sheet
```
1. Create a Google Sheet with this structure:

   | First Name | Last Name | Email              | Phone         | Birth Date | Gender | Notes |
   |------------|-----------|-------------------|---------------|------------|--------|-------|
   | John       | Doe       | john@example.com  | 393331234567  | 1990-01-01 | M      |       |
   | Jane       | Doe       | jane@example.com  | 393331234568  | 1992-05-15 | F      |       |

2. Name the worksheet: "Vatican_Participants"

3. Share with service account email (found in JSON file):
   - Open Google Sheet
   - Click "Share"
   - Add service account email (e.g., vatican-bot@project.iam.gserviceaccount.com)
   - Give "Viewer" access
```

#### 1.3 Configure Agency
```bash
# Copy credentials to Docker
docker cp google_credentials.json vatican-bot-backend-1:/app/google_credentials.json

# Update agency with sheet URL
docker-compose exec backend python manage.py shell

>>> from monitors.models import Agency
>>> agency = Agency.objects.get(id=15)  # Your test agency
>>> agency.google_sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
>>> agency.save()
>>> exit()
```

#### 1.4 Test Google Sheets Integration
```bash
docker-compose exec backend python test_google_sheets_integration.py
```

Expected output:
```
🧪 TESTING GOOGLE SHEETS INTEGRATION
================================================================================

📁 Checking for service account file...
   Path: /app/google_credentials.json
   ✅ Service account file found

🔧 Initializing Google Sheets service...
   ✅ Google Sheets client initialized

🏢 Testing with agencies...

   Agency: Test Agency (ID: 15)
      Sheet URL: https://docs.google.com/spreadsheets/d/...
      📥 Fetching participants...
      ✅ Found 2 participants:
         1. John Doe (john@example.com)
         2. Jane Doe (jane@example.com)

================================================================================
✅ TEST COMPLETE
================================================================================
```

---

### Step 2: Test Extension with Manual Review

#### 2.1 Reload Extension
```
1. Go to chrome://extensions/
2. Find "Vatican Auto-Booking Extension"
3. Click "Reload"
```

#### 2.2 Configure Extension
```
1. Click extension icon
2. Enable "Backend Listener Mode"
3. Set Backend URL: http://localhost:8000
4. Set Agency ID: 15
5. Click "Start Backend Listener"
```

#### 2.3 Watch the Flow

**Background Console (chrome://extensions/ → Details → Inspect views: background page):**
```
🎉 Found 10 available slots from backend!
📦 Opening 10 incognito windows for parallel booking
✅ Opened incognito window #1 for 2026-08-25 09:00 (AUTO mode)
✅ Opened incognito window #2 for 2026-08-25 10:00 (AUTO mode)
...
```

**Content Script Console (in incognito window → F12):**
```
🚀 Auto-booking started...
🎫 Step 1/10: Selecting ticket...
👥 Step 2/10: Setting quantity...
⏰ Step 3/10: Selecting time slot...
✅ Selected time slot: 09:00
➡️ Step 4/10: Proceeding to checkout...
✅ Clicked PROCEDI
📍 Current URL after PROCEDI: https://tickets.museivaticani.va/home/checkout
📝 Step 5/10: Filling form with participants...
✅ Form loaded (detected via: managerSurname)
📋 Clicking checkboxes...
✅ Checkboxes processed
🔐 Step 6/10: Solving Turnstile...
✅ Form filled successfully! Ready for manual review.
👉 Please review the form and click ACQUISTA manually when ready.

🎉 Auto-booking stopped at checkout page
📋 Form has been filled with:
   - Profile data (name, email, phone, etc.)
   - Participant information
   - GDPR checkboxes checked
   - Turnstile solved (if present)

👉 Next steps:
   1. Review all form fields
   2. Verify checkboxes are checked
   3. Click ACQUISTA button manually
   4. Complete payment if needed
```

#### 2.4 Manual Review Checklist

In the incognito window, verify:

- [ ] **Representative (Manager) Fields:**
  - [ ] Cognome (Last Name): Filled correctly
  - [ ] Nome (First Name): Filled correctly
  - [ ] Email: Filled correctly
  - [ ] Conferma Email: Matches email
  - [ ] Numero di cellulare: Filled WITHOUT + sign (e.g., 393331234567)
  - [ ] Città: Filled correctly
  - [ ] Paese: Set to "Italia"
  - [ ] Sesso: Selected
  - [ ] Data di nascita: Filled correctly

- [ ] **Participant Fields:**
  - [ ] Participant 1: Name filled
  - [ ] Participant 2: Name filled (if 2 visitors)

- [ ] **GDPR Checkboxes:**
  - [ ] First checkbox (terms): ✅ Checked
  - [ ] Modal closed (if appeared)
  - [ ] Second checkbox (privacy): ✅ Checked

- [ ] **Turnstile:**
  - [ ] Turnstile solved (checkmark visible)

- [ ] **ACQUISTA Button:**
  - [ ] Button is enabled (not grayed out)
  - [ ] Ready to click

#### 2.5 Click ACQUISTA Manually

Once you've verified everything:
1. Click the **ACQUISTA** button
2. Watch what happens:
   - ✅ Success → Redirects to payment page
   - ❌ Error → Check console for error message

---

## Expected Outcomes

### ✅ Success Case:
```
1. Extension fills form correctly
2. All fields populated
3. Checkboxes checked
4. Phone without + sign
5. You click ACQUISTA
6. Vatican accepts the data
7. Redirects to payment page (epay)
8. You see payment form
```

### ❌ Error Cases:

**Case 1: "Formato non valido" on phone**
- **Cause:** Phone still has + sign
- **Check:** Look at phone field value
- **Fix:** Verify fillPhoneField is stripping + sign

**Case 2: "General Error" (500)**
- **Cause:** Using test data with fake IDs
- **Solution:** Use real Vatican session (see FIX_GENERAL_ERROR.md)

**Case 3: Checkboxes not checked**
- **Cause:** Wrong selectors
- **Check:** Inspect checkbox elements
- **Fix:** Update selectors in content.js

**Case 4: ACQUISTA button disabled**
- **Cause:** Form validation failed
- **Check:** Look for red error messages on form
- **Fix:** Correct the invalid fields

---

## Troubleshooting

### Extension doesn't stop at checkout
**Check:**
```javascript
// In content.js, verify this line exists:
return; // Stop here - don't click ACQUISTA
```

### Form not filled
**Check console for:**
```
❌ Checkout form did not load
```
**Solution:** Check if PROCEDI was clicked twice (see FINAL_FIXES_RECAP_AND_CHECKBOXES.md)

### Checkboxes not clicking
**Check console for:**
```
🔍 First checkbox found: false
🔍 Second checkbox found: false
```
**Solution:** Inspect page and verify checkbox IDs match:
- `#mat-mdc-checkbox-1-input`
- `#mat-mdc-checkbox-4-input`

### Google Sheets not working
**Check:**
```bash
docker-compose exec backend python test_google_sheets_integration.py
```
**Common issues:**
- Service account file missing
- Sheet not shared with service account
- Wrong worksheet name (must be "Vatican_Participants")
- Wrong column names

---

## Re-enabling Auto-Click ACQUISTA

If you want to re-enable automatic clicking (after testing):

1. Open `browser-extension/content.js`
2. Find this section (around line 410):
```javascript
return; // Stop here - don't click ACQUISTA

/* DISABLED - Manual review required
// Step 7: Click BUY button
```

3. Remove the `return;` statement and uncomment the code:
```javascript
// Step 7: Click BUY button
notifyProgress('💳 Step 7/10: Confirming purchase...', 'info');
await clickBuyButton();
// ... rest of the code
```

4. Reload extension

---

## Summary

**What's Changed:**
- ✅ Extension stops at checkout page
- ✅ Form is filled automatically
- ✅ Checkboxes are clicked
- ✅ Phone format is correct (no +)
- ⏸️ ACQUISTA is NOT clicked (you do it manually)

**What to Test:**
1. Google Sheets integration (optional)
2. Extension fills form correctly
3. All fields populated properly
4. Checkboxes checked
5. Manual ACQUISTA click works

**Next Steps:**
1. Test with real Vatican dates (not test data)
2. Verify form data is accepted
3. Complete a test booking
4. Re-enable auto-click if needed

---

**Status:** ✅ Ready for testing
**Mode:** Manual review (ACQUISTA disabled)
**Google Sheets:** Optional (test with test_google_sheets_integration.py)
