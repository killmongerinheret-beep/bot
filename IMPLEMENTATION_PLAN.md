# Vatican Holding System - Hybrid API Implementation Plan

## Goal
Scale to 100+ simultaneous holds on a single 8GB VPS by using API-only holding with browser only for payment.

## Current State
- ✅ `hold_manager.py` already implements API-only holding
- ✅ `test_full_reservation.py` has full browser payment flow
- ✅ `local_browser_agent.py` has browser agent architecture
- ❌ Currently using browser for entire flow (1 GB RAM per hold)

## Phase 1: Optimize Existing API Holding (Week 1)

### 1.1 Enhance `hold_manager.py`
**File**: `backend/monitors/hold_manager.py`

```python
# Add optimized recap loop
def start_infinite_recap_loop(held_slot_id):
    """
    Background task that keeps hold alive indefinitely via API-only recap.
    No browser needed - pure HTTP requests every 4 minutes.
    """
    while True:
        try:
            held = HeldSlot.objects.get(id=held_slot_id)
            
            # Check if hold should continue
            if held.status not in ('held', 'holding'):
                logger.info(f"Hold #{held_slot_id} status={held.status}, stopping recap loop")
                break
            
            # Re-call recap API
            success = keepalive_slot(held)
            
            if success:
                logger.info(f"💓 Hold #{held_slot_id} recap OK - next in 4 min")
            else:
                logger.warning(f"⚠️ Hold #{held_slot_id} recap failed - will retry")
                # Try fresh re-hold
                if not _fresh_re_hold(held):
                    logger.error(f"❌ Hold #{held_slot_id} could not be recovered")
                    held.status = 'expired'
                    held.save()
                    break
            
            # Wait 4 minutes
            time.sleep(240)
            
        except Exception as e:
            logger.error(f"Recap loop error for hold #{held_slot_id}: {e}")
            time.sleep(60)  # Wait 1 min before retry
```

### 1.2 Create Celery Task for Recap Loops
**File**: `backend/monitors/tasks_hold.py`

```python
from celery import shared_task
from .hold_manager import start_infinite_recap_loop

@shared_task(bind=True, max_retries=None)
def run_infinite_recap_loop(self, held_slot_id):
    """
    Celery task that runs the infinite recap loop.
    This task never exits - it runs until the hold is released/paid/expired.
    """
    try:
        start_infinite_recap_loop(held_slot_id)
    except Exception as e:
        logger.error(f"Recap loop task crashed for hold #{held_slot_id}: {e}")
        # Restart the task after 1 minute
        self.retry(countdown=60)
```

### 1.3 Update Hold Creation to Start Recap Loop
**File**: `backend/monitors/hold_manager.py`

```python
def hold_slot(task, date, slot_id, slot_time, ticket_id, ticket_name, visitors, proxy_str=None):
    """
    Hold a Vatican slot via /api/visit/recap.
    Returns HeldSlot instance or None on failure.
    """
    # ... existing hold logic ...
    
    held = HeldSlot.objects.create(
        task=task,
        date=date,
        slot_id=slot_id,
        slot_time=slot_time,
        ticket_id=str(ticket_id),
        ticket_name=ticket_name,
        visitors=visitors,
        adult_count=task.adult_count,
        child_count=task.child_count,
        total_price=total_price,
        jsessionid=jsessionid,
        ticketmv=ticketmv,
        recap_id=recap_id,
        status='held',
        payment_url=payment_url,
        notes=notes,
    )
    
    # 🆕 Start infinite recap loop in background
    from .tasks_hold import run_infinite_recap_loop
    run_infinite_recap_loop.delay(held.id)
    
    logger.info(f"✅ HeldSlot #{held.id} created + recap loop started")
    return held
```

## Phase 2: Browser-Only Payment Flow (Week 2)

### 2.1 Create Payment-Only Browser Function
**File**: `backend/monitors/browser_payment.py` (NEW)

```python
"""
Browser-only payment completion.
Opens nodriver Chrome ONLY for the payment step (5-10 minutes).
Hold is already active via API - browser just completes the transaction.
"""
import asyncio
import nodriver as uc
from datetime import datetime
from zoneinfo import ZoneInfo

async def complete_payment_browser(held_slot, card_details):
    """
    Open browser, inject existing session, fill payment form, click PAY.
    
    Args:
        held_slot: HeldSlot instance (already held via API)
        card_details: dict with {holder, number, expiry, cvv}
    
    Returns:
        dict with {success: bool, epay_url: str, error: str}
    """
    browser = None
    try:
        # Launch nodriver Chrome
        browser = await uc.start(
            user_data_dir=CHROME_PROFILE,
            browser_executable_path=CHROME_PATH,
            headless=False,
            lang='it-IT',
        )
        tab = browser.main_tab
        
        # Navigate to Vatican homepage first
        await tab.get('https://tickets.museivaticani.va/home')
        await tab.sleep(2)
        
        # Inject session cookies from API hold
        await tab.browser.cookies.set({
            'name': 'JSESSIONID',
            'value': held_slot.jsessionid,
            'domain': '.museivaticani.va',
            'path': '/',
        })
        if held_slot.ticketmv:
            await tab.browser.cookies.set({
                'name': 'ticketmv',
                'value': held_slot.ticketmv,
                'domain': '.museivaticani.va',
                'path': '/',
            })
        
        # Navigate to checkout (session should be active)
        rome = ZoneInfo('Europe/Rome')
        day, month, year = held_slot.date.split('/')
        dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
        ts = int(dt.timestamp() * 1000)
        checkout_url = f'https://tickets.museivaticani.va/home/fromtag/{held_slot.visitors}/{ts}/MV-Biglietti/1'
        
        await tab.get(checkout_url)
        await tab.sleep(3)
        
        # Check if we're at the checkout form
        form_present = await tab.evaluate("!!document.querySelector(\"[data-cy='managerSurname']\")")
        
        if not form_present:
            # Need to navigate through the flow
            # Click PRENOTA, set quantity, select time, click PROCEDI
            # (Copy logic from test_full_reservation.py steps 3-7)
            await navigate_to_checkout(tab, held_slot)
        
        # Now we should be at checkout form
        # Fill form (copy from test_full_reservation.py step 8)
        await fill_checkout_form(tab, held_slot)
        
        # Click BUY
        await tab.evaluate("""
            (() => {
                const btn = document.querySelector("[data-cy='buyVisit']") ||
                    Array.from(document.querySelectorAll('button')).find(b => /PROCEDI|ACQUISTA/i.test(b.textContent));
                if (btn) btn.click();
            })()
        """)
        await tab.sleep(5)
        
        # Wait for epay redirect
        epay_url = ''
        for _ in range(120):
            await tab.sleep(0.5)
            cur = await tab.evaluate("window.location.href")
            if cur and 'epay' in cur:
                epay_url = cur
                break
        
        if not epay_url:
            return {'success': False, 'error': 'No epay redirect'}
        
        # Fill payment form (copy from test_full_reservation.py step 11)
        await fill_payment_form(tab, card_details)
        
        # Click PAY
        await tab.evaluate("document.body.click(); document.activeElement?.blur();")
        await tab.sleep(0.5)
        await tab.evaluate("""
            (() => {
                const btn = document.querySelector("button#form-submit[type='submit'].btn-submit");
                if (btn && !btn.disabled) { btn.scrollIntoView(); btn.focus(); btn.click(); }
            })()
        """)
        
        # Wait for confirmation
        for _ in range(240):
            await tab.sleep(0.5)
            cur = await tab.evaluate("window.location.href")
            if 'feedback/success' in (cur or '') or 'confirm' in (cur or ''):
                return {'success': True, 'epay_url': cur}
            if 'feedback/fail' in (cur or ''):
                return {'success': False, 'error': 'Payment declined'}
        
        return {'success': False, 'error': 'Timeout waiting for confirmation'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        if browser:
            try:
                browser.stop()
            except:
                pass


async def navigate_to_checkout(tab, held_slot):
    """Navigate from ticket page to checkout form"""
    # Resolve fresh ticket_id
    import requests
    r = requests.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(held_slot.visitors),
        'visitDate': held_slot.date, 'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, timeout=10)
    ticket = next((v for v in r.json().get('visits', [])
                   if 'musei vaticani' in v.get('name', '').lower()
                   and 'ingresso' in v.get('name', '').lower()), None)
    if not ticket:
        raise Exception("Ticket not found")
    tid = str(ticket['id'])
    
    # Click PRENOTA
    await tab.evaluate(f"document.querySelector(\"[data-cy='bookTicket_{tid}']\")?.click()")
    await tab.sleep(2)
    
    # Set quantity (copy from test_full_reservation.py step 4)
    # ... quantity logic ...
    
    # Select time (copy from test_full_reservation.py step 5)
    # ... time selection logic ...
    
    # Click PROCEDI
    await tab.evaluate("""
        (() => {
            const btn = document.querySelector("[data-cy='bookVisit']");
            if (btn) btn.click();
        })()
    """)
    await tab.sleep(5)


async def fill_checkout_form(tab, held_slot):
    """Fill checkout form with buyer profile"""
    # Get profile from DB
    profile = held_slot.task.agency.buyerprofile
    
    # Fill fields (copy from test_full_reservation.py step 8)
    # ... form filling logic ...


async def fill_payment_form(tab, card_details):
    """Fill epay payment form"""
    # Copy from test_full_reservation.py step 11
    # ... payment form logic ...
```

### 2.2 Create Telegram Command for Payment
**File**: `backend/telegram_bot.py`

```python
# Add new command handler
async def handle_pay_command(update, context):
    """
    /pay <hold_id> - Complete payment for a held slot
    Opens browser on the agent machine to fill payment form.
    """
    if not update.message:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /pay <hold_id>")
        return
    
    hold_id = args[0]
    
    try:
        held = HeldSlot.objects.get(id=hold_id, status='held')
    except HeldSlot.DoesNotExist:
        await update.message.reply_text(f"❌ Hold #{hold_id} not found or already paid")
        return
    
    # Get card details from buyer profile
    profile = held.task.agency.buyerprofile
    card_details = {
        'holder': profile.card_holder,
        'number': profile.card_number,
        'expiry': profile.card_expiry,
        'cvv': profile.card_cvv,
    }
    
    # Send "processing" message
    await update.message.reply_text(
        f"🌐 Opening browser for Hold #{hold_id}...\n"
        f"📅 {held.date} {held.slot_time} | 👥 {held.visitors}v\n"
        f"This will take 5-10 minutes."
    )
    
    # Dispatch to browser agent
    from .monitors.tasks_hold import complete_payment_task
    complete_payment_task.delay(hold_id, card_details)
    
    await update.message.reply_text(
        f"✅ Payment request sent to browser agent.\n"
        f"You'll receive a notification when complete."
    )
```

### 2.3 Create Celery Task for Payment
**File**: `backend/monitors/tasks_hold.py`

```python
@shared_task
def complete_payment_task(hold_id, card_details):
    """
    Celery task that opens browser and completes payment.
    Runs on the worker machine with nodriver installed.
    """
    from .browser_payment import complete_payment_browser
    import asyncio
    
    try:
        held = HeldSlot.objects.get(id=hold_id)
        
        # Run async browser function
        result = asyncio.run(complete_payment_browser(held, card_details))
        
        if result['success']:
            held.status = 'paid'
            held.payment_url = result['epay_url']
            held.save()
            
            # Stop recap loop (hold is now paid)
            # The recap loop will see status='paid' and exit
            
            # Notify admin
            from .notification_utils import tg_send
            tg_send(
                f"✅ *PAYMENT COMPLETE!*\n\n"
                f"📅 {held.date} {held.slot_time}\n"
                f"👥 {held.visitors} visitors\n"
                f"💶 €{held.total_price}\n\n"
                f"🎉 Ticket booked successfully!\n"
                f"Hold #{hold_id}"
            )
        else:
            # Notify failure
            from .notification_utils import tg_send
            tg_send(
                f"❌ Payment failed for Hold #{hold_id}\n\n"
                f"Error: {result['error']}\n\n"
                f"Hold is still active - you can retry with /pay {hold_id}"
            )
    
    except Exception as e:
        logger.error(f"Payment task failed for hold #{hold_id}: {e}")
        from .notification_utils import tg_send
        tg_send(
            f"❌ Payment error for Hold #{hold_id}\n\n"
            f"Error: {str(e)}\n\n"
            f"Hold is still active - you can retry with /pay {hold_id}"
        )
```

## Phase 3: Testing & Deployment (Week 3)

### 3.1 Test API-Only Holding
```bash
# Test that holds stay alive via API-only recap
docker-compose exec backend python manage.py shell

from monitors.models import MonitorTask, HeldSlot
from monitors.hold_manager import hold_slot

# Create test hold
task = MonitorTask.objects.filter(is_active=True).first()
held = hold_slot(
    task=task,
    date='09/06/2026',
    slot_id='test_slot_id',
    slot_time='09:00',
    ticket_id='test_ticket_id',
    ticket_name='Musei Vaticani - Biglietti d\'ingresso',
    visitors=2
)

# Check that recap loop started
# Watch logs: docker-compose logs -f worker_vatican | grep "recap OK"

# Wait 10 minutes, verify hold is still active
# Check DB: HeldSlot.objects.get(id=held.id).last_keepalive_at
```

### 3.2 Test Browser Payment
```bash
# Test payment completion via browser
docker-compose exec backend python manage.py shell

from monitors.tasks_hold import complete_payment_task

# Use a real held slot
held_id = 123  # Replace with actual hold ID
card_details = {
    'holder': 'TEST USER',
    'number': '4111111111111111',  # Test card
    'expiry': '12/25',
    'cvv': '123',
}

complete_payment_task(held_id, card_details)

# Watch browser open, fill form, click PAY
# Check logs for success/failure
```

### 3.3 Monitor RAM Usage
```bash
# Check RAM usage with 10 active holds
docker stats

# Should see:
# - worker_vatican: ~1-2 GB (10 holds × 50 MB each + Python overhead)
# - Temporary spike to 2-3 GB when browser opens for payment
# - Back to 1-2 GB after payment completes
```

## Phase 4: Scale Testing (Week 4)

### 4.1 Load Test with 50 Holds
```python
# Create 50 test holds
for i in range(50):
    held = hold_slot(
        task=task,
        date=f'{(i % 30) + 1:02d}/06/2026',
        slot_id=f'test_slot_{i}',
        slot_time='09:00',
        ticket_id='test_ticket_id',
        ticket_name='Musei Vaticani - Biglietti d\'ingresso',
        visitors=2
    )
    print(f"Hold #{held.id} created")
    time.sleep(1)

# Monitor RAM: should be ~3-4 GB total
# Monitor CPU: should be <20% (just HTTP requests every 4 min)
```

### 4.2 Verify Recap Loops
```bash
# Check that all 50 holds are recapping successfully
docker-compose logs worker_vatican | grep "recap OK" | tail -50

# Should see regular "recap OK" messages for all 50 holds
# No "recap failed" or "expired" messages
```

### 4.3 Test Payment Under Load
```bash
# With 50 holds active, trigger payment for one
# Verify browser opens, completes payment, closes
# Verify other 49 holds continue recapping normally
```

## Expected Results

### RAM Usage
- **Before (browser-based)**: 10 holds = 10 GB RAM
- **After (API-based)**: 100 holds = 5-6 GB RAM
- **Savings**: 95% reduction in RAM per hold

### Capacity
- **Before**: 6-7 holds per 8GB VPS
- **After**: 100+ holds per 8GB VPS
- **Scaling**: 15× improvement

### Cost
- **Before**: $30/month for 3× 8GB VPS = 18-21 holds
- **After**: $10/month for 1× 8GB VPS = 100+ holds
- **Savings**: 70% cost reduction

## Rollout Plan

### Week 1: API Optimization
- ✅ Enhance `hold_manager.py` with infinite recap loop
- ✅ Create Celery task for recap loops
- ✅ Test with 5 holds for 24 hours

### Week 2: Browser Payment
- ✅ Create `browser_payment.py` module
- ✅ Add `/pay` command to Telegram bot
- ✅ Test payment flow with test card

### Week 3: Integration Testing
- ✅ Test full flow: hold → recap → payment
- ✅ Verify holds survive 48+ hours
- ✅ Load test with 20 holds

### Week 4: Production Deployment
- ✅ Deploy to production
- ✅ Migrate existing holds to new system
- ✅ Monitor for 1 week
- ✅ Scale to 50+ holds

## Monitoring & Alerts

### Key Metrics
1. **Active holds**: `HeldSlot.objects.filter(status='held').count()`
2. **Recap success rate**: Count of successful recaps / total recaps
3. **RAM usage**: `docker stats worker_vatican`
4. **Payment success rate**: Count of paid holds / payment attempts

### Alerts
- ⚠️ If recap fails 3× in a row → Telegram alert
- ⚠️ If RAM usage > 7 GB → Telegram alert
- ⚠️ If any hold hasn't recapped in 10 minutes → Telegram alert
- ⚠️ If payment fails → Telegram alert with error details

## Fallback Plan

If API-only holding fails:
1. Keep existing browser-based system as fallback
2. Use distributed swarm architecture (already spec'd)
3. Deploy 3× 8GB VPS for 18-21 browser-based holds
4. Cost: $30/month (vs $10/month for API-based)
