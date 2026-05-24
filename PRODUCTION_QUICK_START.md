# Production Quick Start - Real Vatican Bookings

## 🚀 Get Started in 15 Minutes

---

## Step 1: Create Real Monitoring Task (5 minutes)

### Remove Test Data:
```bash
docker-compose exec backend python /app/create_real_monitoring_task.py
```

This will:
- ✅ Remove test slots (TEST_1, TEST_2, etc.)
- ✅ Remove test tasks
- ✅ Create real monitoring task for June 15-20, 2026
- ✅ Configure worker to check every 5 minutes

### Customize Dates:
Edit `create_real_monitoring_task.py` line 115:
```python
task = create_real_task(
    agency_id=15,
    start_date_str='2026-06-15',  # Change this date
    num_days=6                     # Change number of days
)
```

---

## Step 2: Verify Worker is Monitoring (2 minutes)

### Watch Worker Logs:
```bash
docker-compose logs -f worker_vatican
```

### Expected Output:
```
✅ Checking Vatican availability for task ID: 157
🔍 Calling Search API for fresh ticket IDs
📅 Date: 2026-06-15, Visitors: 2
🎫 Found 15 tickets for 2026-06-15
✅ Ticket: Vatican Museums - Standard Entry (ID: 2129030053)
⏰ Checking time availability...
```

### If Slot Found:
```
🎉 SLOT AVAILABLE!
   Date: 2026-06-15
   Time: 09:00
   Ticket: Vatican Museums - Standard Entry
   Creating HeldSlot...
✅ HeldSlot created (ID: 22180)
📱 Sending Telegram notification...
```

---

## Step 3: Setup Google Sheets (5 minutes)

### 3.1 Create Service Account
```
1. Go to: https://console.cloud.google.com/
2. Create project: "Vatican Bot"
3. Enable: Google Sheets API + Google Drive API
4. Create Service Account → Download JSON
5. Copy to server:
   docker cp google_credentials.json vatican-bot-backend-1:/app/
```

### 3.2 Create Google Sheet
```
Create 3 worksheets:

1. "Bookings_Input" (Bokun writes here)
   | Booking ID | Date       | Time  | Visitors | First Name | Last Name | Email | Phone | Status |

2. "Bookings_Output" (Bot updates here)
   | Booking ID | Date       | Time  | Status | Payment Link | Booked At | Marked |

3. "Participants"
   | Booking ID | Participant # | First Name | Last Name | Birth Date | Gender |
```

### 3.3 Share Sheet
```
1. Click "Share"
2. Add service account email (from JSON)
3. Give "Editor" access
4. Copy sheet URL
```

### 3.4 Configure Agency
```bash
docker-compose exec backend python /app/backend/manage.py shell

>>> from monitors.models import Agency
>>> agency = Agency.objects.get(id=15)
>>> agency.google_sheet_url = 'YOUR_SHEET_URL'
>>> agency.save()
>>> exit()
```

---

## Step 4: Test Extension (3 minutes)

### 4.1 Check API
```bash
curl http://localhost:8000/api/v1/available-slots/?agency_id=15
```

Expected:
```json
{
  "slots": [],
  "count": 0
}
```
(Empty until worker finds slots)

### 4.2 Configure Extension
```
1. Reload extension in Chrome
2. Set Backend URL: http://localhost:8000
3. Set Agency ID: 15
4. Enable Backend Listener
5. Watch background console
```

### 4.3 Wait for Slots
```
When worker finds slot:
1. Extension detects it
2. Opens incognito window
3. Fills form automatically
4. Stops at checkout
5. You click ACQUISTA manually
```

---

## Step 5: Deploy to Hetzner (Optional)

### 5.1 Create Server
```
1. Go to: https://www.hetzner.com/cloud
2. Create CX21 server (€5.83/month)
3. Ubuntu 22.04
4. Note IP address
```

### 5.2 Setup Server
```bash
# Connect
ssh root@YOUR_SERVER_IP

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose -y

# Copy project
scp -r . root@YOUR_SERVER_IP:/root/vatican-bot/

# Start services
cd /root/vatican-bot
docker-compose up -d
```

### 5.3 Configure Extension for Remote
```
Backend URL: http://YOUR_SERVER_IP:8000
Agency ID: 15
```

---

## Complete Workflow

### Automated Flow:
```
1. Worker monitors Vatican every 5 minutes
   ↓
2. Finds available slot
   ↓
3. Creates HeldSlot with REAL Vatican data
   ↓
4. Telegram bot sends notification
   ↓
5. Extension (local) detects slot
   ↓
6. Opens incognito window
   ↓
7. Fills form automatically
   ↓
8. Stops at checkout
   ↓
9. You click ACQUISTA
   ↓
10. Redirects to payment
   ↓
11. Complete payment
   ↓
12. Update Google Sheets (mark as ✓)
```

### With Google Sheets:
```
Bokun → Writes to "Bookings_Input"
   ↓
Backend reads sheet → Creates MonitorTask
   ↓
Worker finds slot → Writes to "Bookings_Output"
   ↓
Telegram notification → "Payment link: https://..."
   ↓
Extension books → Updates "Bookings_Output" (✓)
```

---

## Monitoring Commands

### Check Worker Status:
```bash
docker-compose ps worker_vatican
```

### Watch Worker Logs:
```bash
docker-compose logs -f worker_vatican | grep "Vatican"
```

### Check for Slots:
```bash
curl http://localhost:8000/api/v1/available-slots/?agency_id=15
```

### Database Check:
```bash
docker-compose exec backend python /app/backend/manage.py shell

>>> from monitors.models import HeldSlot, MonitorTask
>>> print(f"Active tasks: {MonitorTask.objects.filter(is_active=True).count()}")
>>> print(f"Held slots: {HeldSlot.objects.filter(status='held').count()}")
```

---

## Troubleshooting

### Worker not checking?
```bash
# Restart worker
docker-compose restart worker_vatican

# Check logs
docker-compose logs worker_vatican
```

### No slots found?
```
- Check dates are in the future
- Verify Vatican has availability
- Check worker logs for errors
- Ensure task is active
```

### Extension not detecting slots?
```
- Verify API returns slots
- Check backend URL is correct
- Check agency ID matches
- Reload extension
```

### "General Error" when clicking ACQUISTA?
```
This should NOT happen with real data!
If it does:
- Check slot has real Vatican IDs (not TEST_*)
- Verify worker created the slot
- Check worker logs for errors
```

---

## Google Sheets Alternatives

### Option 1: Airtable
- Better API
- Built-in automations
- Easier to use
- **Cost:** Paid plans for API

### Option 2: Notion
- Modern interface
- Good API
- **Cost:** Free for personal

### Option 3: PostgreSQL Direct
- Fastest
- Most reliable
- **Complexity:** Bokun needs DB access

### Option 4: REST API
- Most flexible
- Real-time updates
- **Complexity:** Need to build API

**Recommendation:** Start with Google Sheets (free, easy, good API)

---

## Next Steps

1. ✅ Create real monitoring task
2. ✅ Verify worker is checking
3. ✅ Setup Google Sheets (optional)
4. ✅ Test extension locally
5. ✅ Deploy to Hetzner (optional)
6. ✅ Configure Telegram notifications
7. ✅ Test complete workflow

---

## Key Differences: Test vs Real Data

### Test Data (Current):
- ❌ Fake Vatican IDs (TEST_1, TEST_TICKET_123)
- ❌ Fake session (TEST_SESSION)
- ❌ "General Error" when clicking ACQUISTA
- ✅ Good for testing form filling

### Real Data (Production):
- ✅ Real Vatican IDs (from Search API)
- ✅ Real session (from Vatican)
- ✅ Booking works successfully
- ✅ No errors when clicking ACQUISTA

---

**Status:** ✅ Ready for production!
**Time to setup:** 15 minutes
**Cost:** Free (or €5.83/month for Hetzner)

---

**Questions?** Check PRODUCTION_SETUP_GUIDE.md for detailed instructions.
