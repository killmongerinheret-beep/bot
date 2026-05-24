# Vatican Bot Fix Summary
**Date:** April 29, 2026
**Issue:** Bot not sending logs since morning

## Root Cause

The Vatican bot **WAS working** but appeared silent due to:

1. **Turnstile Token Pool** running in background
2. **2captcha balance = $0** 
3. Worker logs flooded with `ERROR_ZERO_BALANCE` errors (1,599+ per day)
4. Token pool trying to maintain 5 pre-solved CAPTCHA tokens continuously

## What Was Happening

- ✅ Celery Beat **WAS** scheduling tasks every minute
- ✅ Orchestrator **WAS** running (`orchestrate_vatican_tasks_search_api`)
- ❌ Token pool **WAS** blocking worker with CAPTCHA errors
- ❌ Logs flooded, making it appear bot was broken

## Solution Applied

**Disabled the Turnstile Token Pool** in `backend/core/celery.py`:

```python
@worker_ready.connect
def start_token_pool(sender=None, **kwargs):
    # ✅ DISABLED: Token pool requires 2captcha balance
    # Only enable if you have 2captcha credits and need instant snipe
    pass
```

## Impact

### ✅ What Still Works:
- Vatican ticket monitoring (Search API)
- Telegram notifications
- Availability checking
- All monitoring features

### ⚠️ What Requires 2captcha Balance:
- **Instant snipe** (auto-booking when slots open)
- **Hold feature** (reserving slots)
- **Auto-checkout** (completing reservations)

## Next Steps

### Option 1: Keep Monitoring Only (Current State)
- Bot will monitor and notify via Telegram
- No auto-booking/holding
- **Cost:** $0/month
- **Action:** None needed

### Option 2: Enable Auto-Booking Features
1. Top up 2captcha balance at https://2captcha.com
   - Minimum: $3 (lasts ~3,000 bookings)
   - Cost per booking: ~$0.001
2. Uncomment token pool in `backend/core/celery.py`
3. Restart worker: `docker-compose restart worker_vatican`

## Verification Commands

```bash
# Check if worker is running without errors
docker-compose logs worker_vatican --tail=50

# Check if orchestrator is dispatching tasks
docker-compose logs worker_vatican | grep "ORCHESTRATOR"

# Check if monitoring tasks are running
docker-compose logs worker_vatican | grep "SEARCH API CHECK"

# Check 2captcha balance
curl "https://2captcha.com/res.php?key=YOUR_API_KEY&action=getbalance&json=1"
```

## Files Modified

1. `backend/core/celery.py` - Disabled token pool auto-start

## Configuration

Current Vatican monitor mode: **Search API** (fast, no browser needed)
- Uses Vatican's official API endpoints
- 10x faster than browser automation
- Works for all days (including Mondays)
- No CAPTCHA needed for monitoring

## Token Pool Details

**Purpose:** Pre-solve Turnstile CAPTCHAs for instant booking
**Target:** 5 tokens maintained continuously
**Cost:** ~$0.005/hour when active
**Benefit:** 0-second booking (vs 30-second delay)

**When to enable:**
- High-demand tickets (sell out in seconds)
- Multiple agencies competing
- Need fastest possible booking

**When to keep disabled:**
- Monitoring only (no booking)
- Low-demand tickets
- Cost-conscious operation

## Monitoring Status

The bot is now running cleanly without CAPTCHA errors. Monitoring tasks should resume normal operation within 1-2 minutes of worker restart.

To verify monitoring is working:
1. Check logs for "ORCHESTRATOR" messages every minute
2. Check logs for "SEARCH API CHECK" when tasks are dispatched
3. Verify no ERROR_ZERO_BALANCE messages

## Support

If monitoring still not working after fix:
1. Check if any active Vatican tasks exist in database
2. Verify Celery Beat is scheduling tasks
3. Check Redis connection
4. Review task dates (past dates are skipped automatically)
