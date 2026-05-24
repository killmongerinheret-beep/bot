# WOR Bot Status Report
**Generated**: 2026-04-27 16:50 UTC

## ✅ System Status: RUNNING (But Not Monitoring for WOR)

The Vatican bot infrastructure is fully operational, but **WOR agency has no active monitoring tasks**.

---

## 🏢 WOR Agency Configuration

| Property | Value |
|----------|-------|
| **Agency ID** | 14 |
| **Name** | WOR |
| **Status** | ✅ Active |
| **Plan** | agency |
| **Created** | 2026-04-22 05:08:43 UTC |

---

## ⚠️ Current Issues

### 1. No Active Monitoring Tasks
- **Total tasks**: 1
- **Active tasks**: 0 ❌
- **Inactive tasks**: 1
- **Status**: Task #272 is deactivated

**Impact**: The bot is running but **not monitoring any dates** for WOR agency.

### 2. No Buyer Profile
- **Status**: ❌ Not configured
- **Impact**: Cannot complete automated bookings (Tier 3 snipe mode)

### 3. Historical Held Slots
- **Total held slots**: 16,215 (historical)
- **Active holds**: 0
- **Status**: All previous holds have been released/expired

---

## 🔧 What Needs to Be Done

### Option A: Activate Existing Task

The inactive task (#272) needs to be reactivated:

```python
# Via Django admin or shell
from monitors.models import MonitorTask
task = MonitorTask.objects.get(id=272)
task.is_active = True
task.save()
```

### Option B: Create New Monitoring Task

Create a new task for WOR agency:

```python
from monitors.models import Agency, MonitorTask

wor = Agency.objects.get(name='WOR')

# Create monitoring task
task = MonitorTask.objects.create(
    agency=wor,
    site='vatican',
    dates=['04/05/2026', '05/05/2026', '06/05/2026'],  # Add desired dates
    preferred_times=['09:00', '10:00', '14:00'],
    visitors=1,  # Or 2, depending on requirement
    ticket_type=0,  # 0 = Standard, 1 = Guided tour
    ticket_name="Musei Vaticani - Biglietti d'ingresso",
    tier='notify',  # Options: 'notify', 'hold', 'snipe'
    check_interval=60,  # Check every 60 seconds
    is_active=True
)

print(f"Created task #{task.id} for WOR")
```

### Option C: Configure via Django Admin

1. Go to: http://localhost:8000/admin
2. Navigate to: Monitors → Monitor Tasks
3. Find Task #272 or create new task
4. Set:
   - Agency: WOR
   - Dates: [desired dates]
   - Ticket type: Standard Entry
   - Visitors: 1 or 2
   - Tier: notify/hold/snipe
   - Is active: ✅ Checked
5. Save

---

## 📋 Recommended Configuration for WOR

### Monitoring Task Settings

```json
{
  "agency": "WOR",
  "site": "vatican",
  "dates": [
    "04/05/2026",
    "05/05/2026",
    "06/05/2026",
    "07/05/2026",
    "08/05/2026",
    "09/05/2026",
    "11/05/2026",
    "12/05/2026"
  ],
  "preferred_times": ["09:00", "10:00", "11:00", "14:00", "15:00"],
  "visitors": 1,
  "ticket_type": 0,
  "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
  "tier": "hold",
  "check_interval": 60,
  "is_active": true
}
```

### Buyer Profile (Required for Tier 2/3)

If you want automated holding or sniping, configure buyer profile:

```python
from monitors.models import BuyerProfile

profile = BuyerProfile.objects.create(
    agency=wor,
    first_name='Mario',
    last_name='Rossi',
    email='wor@example.com',
    phone='3401234567',
    country='Italy',
    city='Roma',
    birth_date='1990-01-15',
    gender='M',
    language='en',
    # For snipe mode (Tier 3):
    card_number='4111111111111111',
    card_expiry='12/25',
    card_cvv='123',
    card_holder='MARIO ROSSI'
)
```

---

## 🚀 Quick Start Guide

### Step 1: Activate Monitoring

Run this command to activate monitoring for WOR:

```bash
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "
from monitors.models import Agency, MonitorTask
wor = Agency.objects.get(name='WOR')
task = MonitorTask.objects.create(
    agency=wor,
    site='vatican',
    dates=['04/05/2026', '05/05/2026', '06/05/2026'],
    preferred_times=['09:00', '10:00', '14:00'],
    visitors=1,
    ticket_type=0,
    ticket_name='Musei Vaticani - Biglietti d\\'ingresso',
    tier='notify',
    check_interval=60,
    is_active=True
)
print(f'Created task #{task.id} for WOR')
"
```

### Step 2: Verify Monitoring Started

Check worker logs:

```bash
docker logs --tail 50 travelagenntbot-worker_vatican-1 | grep -i "agencies: 2"
```

You should see lines like:
```
🚀 SEARCH API CHECK: 04/05/2026 | ... | Agencies: 2
```

The "Agencies: 2" means WOR is now included in monitoring.

### Step 3: Check Telegram Notifications

When tickets become available, WOR will receive Telegram notifications in their configured group.

---

## 📊 Current Bot Activity (Other Agencies)

The bot is actively monitoring for other agencies:

- **Vatican Bot Agency 1** ✅
- **Vatican Bot Agency 2** ✅
- **Tour_guides** ✅
- **Italy pass** ✅
- **Big bus** ✅
- **Wondersofrome** ✅
- **Mahabur** ✅

**WOR** ❌ - Not monitoring (needs activation)

---

## 🔍 Monitoring Tiers Explained

### Tier 1: Notify Only
- Bot sends Telegram alert when tickets available
- User books manually on Vatican website
- **RAM**: 0 MB (API-only monitoring)
- **Cost**: Free

### Tier 2: Hold + Notify
- Bot automatically holds slot via API
- Sends payment link to user
- User completes payment manually
- **RAM**: 50 MB per hold
- **Duration**: Holds for 24 hours

### Tier 3: Snipe (Full Auto)
- Bot holds slot
- Auto-fills form with buyer profile
- Auto-completes payment
- **RAM**: 50 MB + 800 MB browser (5 min)
- **Requires**: Buyer profile + card details

---

## ✅ Next Steps

1. **Activate monitoring** for WOR (see Step 1 above)
2. **Configure buyer profile** if you want Tier 2/3
3. **Set up Telegram group** for WOR notifications
4. **Monitor logs** to verify WOR is being checked

---

## 📞 Support

If you need help:
1. Check logs: `docker logs --tail 100 travelagenntbot-worker_vatican-1`
2. Check Django admin: http://localhost:8000/admin
3. Verify task is active: Task #272 or newly created task

---

**Summary**: The bot infrastructure is running perfectly, but WOR agency needs an active monitoring task to start checking for tickets. Once activated, WOR will be monitored alongside the other 7 active agencies.
