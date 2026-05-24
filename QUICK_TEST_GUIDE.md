# Quick Test Guide - Manual Review Mode

## 🚀 Quick Start (5 Minutes)

### 1. Reload Extension
```
chrome://extensions/ → Find extension → Click "Reload"
```

### 2. Start Backend Listener
```
1. Click extension icon
2. Enable "Backend Listener Mode"
3. Backend URL: http://localhost:8000
4. Agency ID: 15
5. Click "Start Backend Listener"
```

### 3. Watch It Work
```
✅ Extension opens incognito windows
✅ Navigates to Vatican
✅ Fills form automatically
✅ Clicks checkboxes
⏸️ STOPS at checkout page
👉 YOU click ACQUISTA manually
```

---

## 📋 What to Check

When extension stops, verify:

### Form Fields:
- ✅ Name filled
- ✅ Email filled
- ✅ Phone filled (NO + sign: `393331234567`)
- ✅ City filled
- ✅ Country set to Italia
- ✅ Birth date filled

### Checkboxes:
- ✅ First checkbox checked
- ✅ Modal closed
- ✅ Second checkbox checked

### Ready to Click:
- ✅ ACQUISTA button enabled
- ✅ No red error messages

---

## 🧪 Test Google Sheets (Optional)

### Setup (One Time):
```bash
# 1. Copy service account JSON
docker cp google_credentials.json vatican-bot-backend-1:/app/google_credentials.json

# 2. Update agency
docker-compose exec backend python manage.py shell
>>> from monitors.models import Agency
>>> agency = Agency.objects.get(id=15)
>>> agency.google_sheet_url = 'YOUR_SHEET_URL'
>>> agency.save()
>>> exit()

# 3. Test it
docker-compose exec backend python test_google_sheets_integration.py
```

### Google Sheet Format:
```
| First Name | Last Name | Email              | Phone         | Birth Date | Gender |
|------------|-----------|-------------------|---------------|------------|--------|
| John       | Doe       | john@example.com  | 393331234567  | 1990-01-01 | M      |
| Jane       | Doe       | jane@example.com  | 393331234568  | 1992-05-15 | F      |
```

**Worksheet name:** `Vatican_Participants`

---

## 🐛 Troubleshooting

### Extension doesn't stop
**Check:** `browser-extension/content.js` line ~410 has `return;`

### Form not filled
**Check console:** Look for "Checkout form did not load"
**Solution:** PROCEDI might be clicked twice (see FINAL_FIXES_RECAP_AND_CHECKBOXES.md)

### Phone has + sign
**Check:** Phone field value in form
**Solution:** Verify `fillPhoneField()` is stripping + sign

### Checkboxes not checked
**Check console:** Look for "First checkbox found: false"
**Solution:** Inspect page, verify IDs: `#mat-mdc-checkbox-1-input`, `#mat-mdc-checkbox-4-input`

### "General Error" after ACQUISTA
**Cause:** Using test data with fake IDs
**Solution:** Use real Vatican dates (see FIX_GENERAL_ERROR.md)

### Google Sheets not working
**Test:** `docker-compose exec backend python test_google_sheets_integration.py`
**Common issues:**
- Service account file missing
- Sheet not shared with service account
- Wrong worksheet name
- Wrong column names

---

## 📊 Console Logs to Watch

### Background Console:
```
🎉 Found 10 available slots from backend!
📦 Opening 10 incognito windows for parallel booking
✅ Opened incognito window #1 for 2026-08-25 09:00
```

### Content Console (Incognito Window):
```
🚀 Auto-booking started...
🎫 Step 1/10: Selecting ticket...
✅ Selected time slot: 09:00
✅ Clicked PROCEDI
✅ Form loaded
📋 Clicking checkboxes...
✅ Checkboxes processed
✅ Form filled successfully! Ready for manual review.
👉 Please review the form and click ACQUISTA manually when ready.
```

---

## ⚡ Quick Commands

```bash
# Reload extension
chrome://extensions/ → Reload

# Check backend logs
docker-compose logs -f backend

# Check worker logs
docker-compose logs -f worker_vatican

# Test Google Sheets
docker-compose exec backend python test_google_sheets_integration.py

# Check database
docker-compose exec backend python manage.py shell
>>> from monitors.models import HeldSlot
>>> HeldSlot.objects.filter(status='held').count()
```

---

## 📚 Full Documentation

- **TESTING_MANUAL_REVIEW_MODE.md** - Complete testing guide
- **FIX_GENERAL_ERROR.md** - Fix "General Error" issue
- **FINAL_FIXES_RECAP_AND_CHECKBOXES.md** - Form filling fixes
- **CHANGES_SUMMARY.md** - What changed in this update

---

## ✅ Success Checklist

- [ ] Extension reloaded
- [ ] Backend listener started
- [ ] Incognito windows open
- [ ] Form fills automatically
- [ ] Phone without + sign
- [ ] Checkboxes checked
- [ ] Extension stops at checkout
- [ ] You click ACQUISTA manually
- [ ] Vatican accepts the data
- [ ] Redirects to payment page

---

**Status:** ✅ Ready to test
**Time:** ~5 minutes
**Mode:** Manual review (safe testing)
