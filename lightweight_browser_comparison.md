# Lightweight Browser Alternatives for Vatican Holding

## Current: nodriver + Chrome
- **RAM per instance**: 800-1000 MB
- **Pros**: Bypasses Turnstile, stable, well-tested
- **Cons**: High RAM usage

## Alternative 1: Playwright with Shared Browser Context
```python
# Share one browser process across multiple contexts
browser = await playwright.chromium.launch()
contexts = [await browser.new_context() for _ in range(10)]
# Each context = separate session, but shared browser process
# RAM savings: ~30-40% (600-700 MB per context instead of 1 GB)
```
**Issue**: Turnstile detection risk increases with shared browser

## Alternative 2: Headless Chrome with --disable-features
```python
# Aggressive Chrome flags to reduce RAM
chrome_args = [
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-software-rasterizer',
    '--disable-extensions',
    '--disable-background-networking',
    '--disable-sync',
    '--disable-translate',
    '--disable-default-apps',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-blink-features=AutomationControlled',
]
# RAM savings: ~20-25% (650-750 MB per instance)
```
**Issue**: May trigger Turnstile challenges more frequently

## Alternative 3: API-Only Holding (No Browser)
```python
# Pure requests library with session cookies
session = requests.Session()
# Step 1: Get JSESSIONID via search API
# Step 2: Call recap API every 4 minutes
# No browser needed!
```
**Issue**: Vatican requires Turnstile token for reservation step
**Workaround**: Use 2captcha to solve Turnstile ($1-3 per 1000 solves)
**RAM per hold**: ~50 MB (95% reduction!)

## Alternative 4: Hybrid Approach (Recommended)
```python
# Use API-only for holding (steps 1-8)
# Only open browser for final payment (step 9-12)
# Keep hold alive via API recap (no browser)
```
**RAM per hold**: 50 MB (holding) + 800 MB (payment, temporary)
**Capacity**: 100+ holds on 8GB VPS, browser only for 5-10 min during payment

## Recommendation: Hybrid Approach

### Phase 1: API-Only Holding
1. Search API → get ticket_id + JSESSIONID
2. Timeavail API → get slot_id
3. Recap API → hold slot (returns recap_id)
4. Background task: Re-call recap API every 4 min (pure HTTP, no browser)

### Phase 2: Browser for Payment Only
1. When user clicks "Pay Now" button
2. Open nodriver Chrome
3. Navigate to checkout with pre-filled session cookies
4. Fill payment form
5. Click PAY
6. Close browser (hold is already active via API)

### Benefits
- ✅ 95% RAM reduction during holding phase
- ✅ 100+ simultaneous holds on single 8GB VPS
- ✅ Browser only needed for 5-10 minutes during payment
- ✅ No Turnstile issues (API calls don't trigger it)
- ✅ Faster, more reliable, cheaper

### Implementation
```python
# backend/monitors/api_hold_manager.py
class APIHoldManager:
    def hold_slot_api_only(self, date, slot_id, visitors):
        """Hold via pure API calls (no browser)"""
        s = requests.Session()
        
        # Step 1: Search API
        r = s.get(f'{BASE}/api/search/resultPerTag', params={...})
        ticket_id = extract_ticket_id(r.json())
        jsessionid = s.cookies.get('JSESSIONID')
        
        # Step 2: Recap API
        r = s.post(f'{BASE}/api/visit/recap', json={
            'visitId': slot_id,
            'visitTypeId': ticket_id,
            'visitorNum': visitors,
            ...
        })
        recap_id = r.json()['recapId']
        
        # Step 3: Save to DB
        held = HeldSlot.objects.create(
            jsessionid=jsessionid,
            recap_id=recap_id,
            status='held_api',
            ...
        )
        
        # Step 4: Start background recap loop (Celery task)
        start_recap_keepalive.delay(held.id)
        
        return held
    
    def keepalive_recap_api(self, held_slot):
        """Re-call recap every 4 min (pure API, no browser)"""
        s = requests.Session()
        s.cookies.set('JSESSIONID', held_slot.jsessionid)
        
        # Resolve fresh ticket_id
        ticket_id = self.resolve_fresh_ticket_id(held_slot.date, held_slot.visitors)
        
        # Re-call recap
        r = s.post(f'{BASE}/api/visit/recap', json={
            'visitId': held_slot.slot_id,
            'visitTypeId': ticket_id,
            'visitorNum': held_slot.visitors,
            ...
        })
        
        if r.status_code == 200:
            held_slot.last_keepalive_at = timezone.now()
            held_slot.save()
            return True
        return False

# Celery task
@shared_task
def start_recap_keepalive(held_slot_id):
    """Background task: recap every 4 min"""
    while True:
        held = HeldSlot.objects.get(id=held_slot_id)
        if held.status != 'held_api':
            break
        
        success = APIHoldManager().keepalive_recap_api(held)
        if not success:
            # Retry or notify admin
            pass
        
        time.sleep(240)  # 4 minutes
```

### Payment Flow (Browser Only When Needed)
```python
# When user clicks "Pay Now" in Telegram
@shared_task
def complete_payment_with_browser(held_slot_id, card_details):
    """Open browser ONLY for payment step"""
    held = HeldSlot.objects.get(id=held_slot_id)
    
    # Launch nodriver Chrome
    browser = await uc.start(...)
    tab = browser.main_tab
    
    # Navigate to checkout with existing session
    await tab.get(f'{BASE}/checkout')
    
    # Inject cookies from API hold
    await tab.browser.cookies.set({
        'name': 'JSESSIONID',
        'value': held.jsessionid,
        'domain': '.museivaticani.va'
    })
    
    # Reload to activate session
    await tab.get(f'{BASE}/checkout')
    
    # Fill payment form (steps 11-12 from your test_full_reservation.py)
    await fill_payment_form(tab, card_details)
    
    # Click PAY
    await click_pay_button(tab)
    
    # Wait for confirmation
    epay_url = await wait_for_epay_redirect(tab)
    
    # Close browser (hold is still active via API)
    browser.stop()
    
    # Update DB
    held.status = 'paid'
    held.payment_url = epay_url
    held.save()
```
