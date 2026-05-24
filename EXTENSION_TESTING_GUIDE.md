# Extension Full Booking - Testing Guide

## Quick Start Testing

### Test 1: Verify Extension Loads

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select `browser-extension` folder
6. ✅ Extension icon should appear in toolbar

---

### Test 2: Create Test Slot (Safe - No Real Booking)

1. **Click extension icon** in toolbar
2. **Click "Create Test Slot"** button
3. **Watch console** (F12):
   ```
   ✅ Test slot created successfully!
   Slot ID: 22133
   Date: 15/06/2026
   Time: 09:00
   ```
4. **Within 10 seconds**, incognito window should open
5. **Watch browser console** in incognito window:
   ```
   [Auto-booking] Auto-booking started...
   [Auto-booking] Step 1: Selecting ticket...
   [Auto-booking] Step 2: Setting quantity...
   [Auto-booking] Step 3: Selecting time slot...
   ...
   ```

**Expected Result:**
- ✅ Incognito window opens automatically
- ✅ Extension navigates to Vatican website
- ✅ Extension starts auto-booking flow
- ✅ Console shows progress messages

**If It Fails:**
- Check backend is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Check extension console for errors

---

### Test 3: Backend Listener Mode (Safe - No Real Booking)

1. **Start backend listener:**
   - Click "Backend Listener" tab in extension
   - Enter backend URL: `http://localhost:8000`
   - **Uncheck "Auto-pay"** (safe mode)
   - Click "Start Listener"

2. **Create test slot via backend:**
   ```bash
   docker-compose exec backend python manage.py shell
   ```
   ```python
   from monitors.models import HeldSlot, MonitorTask, Agency
   
   # Get or create test agency
   agency = Agency.objects.first()
   
   # Create test task
   task = MonitorTask.objects.create(
       agency=agency,
       site='vatican',
       area_name='Musei Vaticani',
       dates=['15/06/2026'],
       preferred_times=['09:00'],
       visitors=2,
       adult_count=2,
       child_count=0,
       ticket_type=0
   )
   
   # Create test held slot
   slot = HeldSlot.objects.create(
       task=task,
       date='15/06/2026',
       slot_id='TEST_123',
       slot_time='09:00',
       ticket_id='2129030053',
       ticket_name='Musei Vaticani - Biglietti d\'ingresso',
       visitors=2,
       adult_count=2,
       child_count=0,
       jsessionid='test_session',
       status='held'
   )
   
   print(f"Created test slot: {slot.id}")
   ```

3. **Watch extension console:**
   ```
   🎉 Found 1 available slots from backend!
   📦 Opening 1 incognito windows for parallel booking
   ✅ Opened incognito window #1 for 15/06/2026 09:00
   ```

4. **Watch incognito window:**
   - Extension should start auto-booking
   - Should fill forms automatically
   - Should stop at payment page (auto-pay disabled)

**Expected Result:**
- ✅ Extension polls backend every 10 seconds
- ✅ Opens incognito window when slot available
- ✅ Completes booking flow up to payment
- ✅ Stops before clicking PAY (safe mode)

---

### Test 4: Profile and Participant Data

1. **Add profile data via Django admin:**
   ```bash
   docker-compose exec backend python manage.py shell
   ```
   ```python
   from monitors.models import BuyerProfile, Agency
   from datetime import date
   
   agency = Agency.objects.first()
   
   profile, created = BuyerProfile.objects.get_or_create(
       agency=agency,
       defaults={
           'first_name': 'Mario',
           'last_name': 'Rossi',
           'email': 'mario.rossi@example.com',
           'phone': '3401234567',
           'city': 'Roma',
           'country': 'Italia',
           'birth_date': date(1990, 1, 15),
           'gender': 'M',
           'language': 'en'
       }
   )
   
   print(f"Profile: {profile}")
   ```

2. **Add participant names:**
   ```python
   import json
   
   participants = [
       {'first_name': 'Mario', 'last_name': 'Rossi'},
       {'first_name': 'Luigi', 'last_name': 'Verdi'}
   ]
   
   profile.participants_json = json.dumps(participants)
   profile.save()
   
   print(f"Participants: {profile.participants_json}")
   ```

3. **Test booking with participants:**
   - Create test slot (as in Test 3)
   - Watch extension fill forms
   - Verify participant names are used

**Expected Result:**
- ✅ Representative form filled with profile data
- ✅ Participant 1: Mario Rossi
- ✅ Participant 2: Luigi Verdi

---

### Test 5: Card Details (Safe - No Real Payment)

1. **Add test card data:**
   ```python
   profile.card_number = '4111111111111111'  # Test card
   profile.card_expiry = '12/25'
   profile.card_cvv = '123'
   profile.card_holder = 'MARIO ROSSI'
   profile.save()
   
   print(f"Card: {profile.card_number[:4]}...{profile.card_number[-4:]}")
   ```

2. **Test booking with card:**
   - Create test slot
   - **Keep auto-pay disabled**
   - Watch extension fill payment form

**Expected Result:**
- ✅ Extension fills card number
- ✅ Extension fills CVV
- ✅ Extension fills expiry date
- ✅ Extension checks agreement box
- ❌ Extension does NOT click PAY (safe mode)

---

### Test 6: Real Booking (Use Real Card!)

⚠️ **WARNING: This will make a real booking and charge your card!**

1. **Add real profile data:**
   ```python
   profile.first_name = 'Your Real Name'
   profile.last_name = 'Your Real Surname'
   profile.email = 'your.real.email@example.com'
   profile.phone = '3401234567'  # Your real phone
   profile.birth_date = date(1990, 1, 15)  # Your real birth date (18+)
   profile.save()
   ```

2. **Add real card data:**
   ```python
   profile.card_number = '4569331515529372'  # Your real card
   profile.card_expiry = '07/28'  # Your real expiry
   profile.card_cvv = '721'  # Your real CVV
   profile.card_holder = 'YOUR NAME ON CARD'  # Uppercase
   profile.save()
   ```

3. **Enable auto-pay in extension:**
   - Click "Backend Listener" tab
   - **Check "Auto-pay"** checkbox
   - Click "Start Listener"

4. **Wait for real slot:**
   - Backend monitors Vatican website
   - When slot available, extension opens window
   - Extension completes full booking
   - Extension clicks PAY automatically

**Expected Result:**
- ✅ Extension completes full booking
- ✅ Extension fills payment form
- ✅ Extension clicks PAY button
- ✅ Payment is submitted to bank
- ✅ 3DS approval (if required)
- ✅ Booking confirmed

---

## Parallel Booking Test

### Test 7: Multiple Slots (Safe - No Real Booking)

1. **Create multiple test slots:**
   ```python
   for i in range(3):
       slot = HeldSlot.objects.create(
           task=task,
           date=f'{15+i}/06/2026',
           slot_id=f'TEST_{i}',
           slot_time='09:00',
           ticket_id='2129030053',
           ticket_name='Musei Vaticani - Biglietti d\'ingresso',
           visitors=2,
           adult_count=2,
           child_count=0,
           jsessionid=f'test_session_{i}',
           status='held'
       )
       print(f"Created slot {i+1}: {slot.date}")
   ```

2. **Watch extension:**
   - Should open 3 incognito windows
   - Each window books different date
   - All run in parallel

**Expected Result:**
- ✅ 3 incognito windows open
- ✅ Each window books different slot
- ✅ No conflicts between windows
- ✅ All bookings complete independently

---

## Debugging

### Check Extension Console

1. **Open extension popup**
2. **Right-click** → "Inspect"
3. **Console tab** shows:
   ```
   Vatican Ticket Monitor - Content Script Loaded
   Starting auto-booking flow...
   Current page state: home
   Auto-booking config: {...}
   ```

### Check Background Script Console

1. **Go to** `chrome://extensions/`
2. **Click** "Inspect views: background page"
3. **Console tab** shows:
   ```
   🚀 Starting Backend Listener Mode
   ✅ Backend listener started - polling every 10 seconds
   🎉 Found 1 available slots from backend!
   ```

### Check Backend Logs

```bash
# Backend API logs
docker-compose logs backend | tail -50

# Worker logs
docker-compose logs worker_vatican | tail -50

# All logs
docker-compose logs -f
```

### Common Issues

**"Backend API error: 404"**
- Backend not running
- Wrong backend URL
- API endpoint not found

**"Failed to select ticket"**
- Ticket ID is stale
- Vatican changed IDs
- Backend needs to refresh IDs

**"No available time slots"**
- Slot sold out
- Wrong date format
- Vatican API error

**"Payment page not loaded"**
- Reservation failed
- Turnstile not solved
- Form validation error

---

## Performance Testing

### Test 8: Stress Test (10 Parallel Bookings)

1. **Create 10 test slots:**
   ```python
   for i in range(10):
       HeldSlot.objects.create(
           task=task,
           date=f'{15+i}/06/2026',
           slot_id=f'TEST_{i}',
           slot_time='09:00',
           ticket_id='2129030053',
           ticket_name='Musei Vaticani',
           visitors=2,
           jsessionid=f'test_{i}',
           status='held'
       )
   ```

2. **Monitor system resources:**
   ```bash
   # CPU and memory
   docker stats
   
   # Container status
   docker-compose ps
   ```

3. **Watch extension:**
   - Should open 10 windows
   - All should complete
   - No crashes or errors

**Expected Result:**
- ✅ 10 windows open simultaneously
- ✅ All bookings complete
- ✅ System remains stable
- ✅ Memory usage acceptable

---

## Checklist

### Before Testing
- [ ] Backend is running (`docker-compose up -d`)
- [ ] Extension is loaded in Chrome
- [ ] Profile data is added
- [ ] Participant names are set
- [ ] Card details are added (for payment tests)

### Safe Tests (No Real Booking)
- [ ] Test 1: Extension loads ✅
- [ ] Test 2: Create test slot ✅
- [ ] Test 3: Backend listener mode ✅
- [ ] Test 4: Profile and participants ✅
- [ ] Test 5: Card details (no pay) ✅
- [ ] Test 7: Multiple slots ✅

### Real Booking Tests (Use Real Card!)
- [ ] Test 6: Real booking with auto-pay ⚠️

### Performance Tests
- [ ] Test 8: 10 parallel bookings ✅

---

## Success Criteria

### Extension Works If:
- ✅ Opens incognito windows automatically
- ✅ Navigates to Vatican website
- ✅ Selects correct ticket
- ✅ Fills all form fields
- ✅ Uses participant names from backend
- ✅ Handles GDPR checkboxes
- ✅ Waits for Turnstile
- ✅ Submits reservation
- ✅ Fills payment card
- ✅ Clicks PAY (if auto-pay enabled)

### Parallel Booking Works If:
- ✅ Opens multiple windows
- ✅ Each window books different slot
- ✅ No session conflicts
- ✅ All bookings complete
- ✅ System remains stable

---

## Next Steps After Testing

1. **If tests pass:**
   - ✅ Extension is ready for production
   - ✅ Can handle real bookings
   - ✅ Supports parallel booking

2. **If tests fail:**
   - Check console for errors
   - Review backend logs
   - Verify data is correct
   - Test each step individually

3. **Production deployment:**
   - Encrypt card data
   - Add API authentication
   - Enable rate limiting
   - Monitor performance

---

**Testing Date:** May 6, 2026  
**Status:** Ready to test  
**Version:** 1.0
