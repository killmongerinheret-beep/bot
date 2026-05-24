# Google Sheet Verification Guide

## 📋 Your Google Sheet

**URL**: https://docs.google.com/spreadsheets/d/1ZpGUSWlKM90NYzJIkAb8y1V6IarA9QWs3xRDcHRFX9M/edit?usp=sharing

---

## ✅ Step 1: Verify Sheet Format

### Required Columns

Your sheet should have these columns (case-insensitive):

| Column Name | Required | Format | Example |
|-------------|----------|--------|---------|
| First Name | ✅ Yes | Text | John |
| Last Name | ✅ Yes | Text | Doe |
| Email | ✅ Yes | Email | john@example.com |
| Phone | ✅ Yes | Phone | +39 123456789 |
| Birth Date | ⚠️ Optional | YYYY-MM-DD | 1990-01-15 |
| City | ⚠️ Optional | Text | Roma |
| Country | ⚠️ Optional | Text | Italia |

### Acceptable Column Name Variations

The system accepts these variations:
- `First Name`, `first_name`, `FirstName`, `firstname`
- `Last Name`, `last_name`, `LastName`, `lastname`
- `Email`, `email`, `E-mail`
- `Phone`, `phone`, `Phone Number`, `phone_number`
- `Birth Date`, `birth_date`, `birthdate`, `DOB`, `Date of Birth`

### Example Sheet Format

```
| First Name | Last Name | Email              | Phone          | Birth Date | City  | Country |
|------------|-----------|-------------------|----------------|------------|-------|---------|
| John       | Doe       | john@example.com  | +39 123456789  | 1990-01-15 | Roma  | Italia  |
| Jane       | Doe       | jane@example.com  | +39 987654321  | 1992-03-20 | Roma  | Italia  |
| Mario      | Rossi     | mario@example.com | +39 555123456  | 1985-07-10 | Roma  | Italia  |
```

---

## ✅ Step 2: Share Sheet with Service Account

### Get Service Account Email

```bash
# Check if credentials file exists
docker-compose exec backend cat /app/google-credentials.json | grep client_email

# Or check locally
cat backend/google-credentials.json | grep client_email
```

**Expected output**:
```json
"client_email": "vatican-bot@your-project.iam.gserviceaccount.com"
```

### Share Sheet

1. Open your Google Sheet
2. Click **"Share"** button (top right)
3. Add the service account email
4. Set permission to **"Editor"**
5. Uncheck "Notify people"
6. Click **"Send"**

---

## ✅ Step 3: Add Sheet URL to System

```bash
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Agency

# Get or create agency
agency = Agency.objects.first()
if not agency:
    agency = Agency.objects.create(
        name='My Agency',
        api_key='test-key-123',
        plan='pro'
    )

# Add Google Sheet URL
agency.google_sheet_url = 'https://docs.google.com/spreadsheets/d/1ZpGUSWlKM90NYzJIkAb8y1V6IarA9QWs3xRDcHRFX9M/edit?usp=sharing'
agency.save()

print(f"✅ Google Sheet URL added to Agency {agency.id}")
print(f"   Agency: {agency.name}")
print(f"   Sheet URL: {agency.google_sheet_url}")

exit()
```

---

## ✅ Step 4: Test Import

### Manual Import Test

```bash
# Import participants from Google Sheets
docker-compose exec backend python manage.py import_participants --agency-id 1
```

### Expected Output (Success)

```
✅ Imported 3 participants for Agency 1
- John Doe (john@example.com)
- Jane Doe (jane@example.com)
- Mario Rossi (mario@example.com)
```

### Common Errors and Solutions

#### Error 1: "Permission denied"

**Error Message**:
```
❌ Error: Permission denied. Please share the sheet with the service account.
```

**Solution**:
1. Check service account email is correct
2. Share sheet with service account
3. Give "Editor" permission
4. Try import again

#### Error 2: "Sheet not found"

**Error Message**:
```
❌ Error: Sheet not found or URL is invalid.
```

**Solution**:
1. Verify sheet URL is correct
2. Check sheet is not deleted
3. Ensure URL includes `/edit` at the end
4. Try accessing sheet in browser

#### Error 3: "Missing required columns"

**Error Message**:
```
❌ Error: Missing required columns: First Name, Last Name
```

**Solution**:
1. Check column names match required format
2. Ensure columns are in first row
3. Remove any empty rows at top
4. Try variations: "first_name" or "FirstName"

#### Error 4: "No data found"

**Error Message**:
```
❌ Error: No participant data found in sheet.
```

**Solution**:
1. Check sheet has data rows (not just headers)
2. Ensure data starts from row 2
3. Remove any empty rows
4. Check sheet name is "Sheet1" or first sheet

---

## ✅ Step 5: Verify Import in Database

```bash
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Agency, BuyerProfile
import json

# Get agency
agency = Agency.objects.first()
print(f"Agency: {agency.name}")
print(f"Sheet URL: {agency.google_sheet_url}")
print()

# Get buyer profile
try:
    profile = agency.buyer_profile
    print("✅ BuyerProfile found:")
    print(f"   Name: {profile.first_name} {profile.last_name}")
    print(f"   Email: {profile.email}")
    print(f"   Phone: {profile.phone}")
    print(f"   City: {profile.city}")
    print(f"   Country: {profile.country}")
    print(f"   Birth Date: {profile.birth_date}")
    print()
    
    # Get participants
    if profile.participants_json:
        participants = json.loads(profile.participants_json)
        print(f"✅ Participants: {len(participants)}")
        for i, p in enumerate(participants, 1):
            print(f"   {i}. {p.get('first_name')} {p.get('last_name')}")
            print(f"      Email: {p.get('email')}")
            print(f"      Phone: {p.get('phone')}")
    else:
        print("⚠️ No participants data")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("   BuyerProfile not found. Import may have failed.")

exit()
```

### Expected Output

```
Agency: My Agency
Sheet URL: https://docs.google.com/spreadsheets/d/1ZpGUSWlKM90NYzJIkAb8y1V6IarA9QWs3xRDcHRFX9M/edit?usp=sharing

✅ BuyerProfile found:
   Name: John Doe
   Email: john@example.com
   Phone: +39 123456789
   City: Roma
   Country: Italia
   Birth Date: 1990-01-15

✅ Participants: 3
   1. John Doe
      Email: john@example.com
      Phone: +39 123456789
   2. Jane Doe
      Email: jane@example.com
      Phone: +39 987654321
   3. Mario Rossi
      Email: mario@example.com
      Phone: +39 555123456
```

---

## ✅ Step 6: Test with Extension

### Create Test Slot with Your Data

```bash
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import HeldSlot, MonitorTask, Agency

# Get agency
agency = Agency.objects.first()

# Get or create task
task = MonitorTask.objects.filter(agency=agency, is_active=True).first()
if not task:
    task = MonitorTask.objects.create(
        agency=agency,
        date='28/03/2026',
        visitors=2,  # Match number of participants you want to use
        ticket_type=0,
        is_active=True
    )

# Create test slot
slot = HeldSlot.objects.create(
    task=task,
    slot_id='TEST-GOOGLE-SHEETS-001',
    date='28/03/2026',
    slot_time='10:00',
    ticket_id='2129030053',
    ticket_name='Vatican Museums - Standard Entry',
    visitors=2,  # Must match task.visitors
    adult_count=2,
    child_count=0,
    status='held',
    total_price=32.00
)

print(f"✅ Test slot created: {slot.id}")
print(f"   Date: {slot.date} {slot.slot_time}")
print(f"   Visitors: {slot.visitors}")
print(f"   Ticket: {slot.ticket_name}")
print()
print("🎯 Extension should detect this slot within 10 seconds!")
print("   Watch extension console (F12) for:")
print("   🎉 Found 1 available slots from backend!")
print("   📦 Opening incognito window...")

exit()
```

### Watch Extension Auto-Book

**Extension Console** (Right-click extension icon → Inspect):
```
✅ Backend listener started - polling every 10 seconds
🔄 Checking backend for available slots...
🎉 Found 1 available slots from backend!
📋 1 new slots to process
📦 Opening 1 incognito windows for parallel booking
✅ Opened incognito window #1 for 28/03/2026 10:00 (AUTO mode)
```

**Incognito Window Console** (F12):
```
Vatican Ticket Monitor - Content Script Loaded
🚀 Auto-booking started...
🎫 Step 1/10: Selecting ticket...
👥 Step 2/10: Setting quantity...
⏰ Step 3/10: Selecting time slot...
📝 Step 5/10: Filling form with participants...
  Manager: John Doe (john@example.com)  ← FROM YOUR GOOGLE SHEET
  Participant 1: John Doe               ← FROM YOUR GOOGLE SHEET
  Participant 2: Jane Doe               ← FROM YOUR GOOGLE SHEET
🔐 Step 6/10: Solving Turnstile...
💳 Step 7/10: Confirming purchase...
```

---

## ✅ Step 7: Verify API Response

### Check Available Slots Endpoint

```bash
# Check what extension sees
curl http://localhost:8000/api/v1/available-slots/ | jq
```

### Expected Response

```json
{
  "slots": [
    {
      "id": 1,
      "date": "28/03/2026",
      "time": "10:00",
      "ticket_id": "2129030053",
      "ticket_name": "Vatican Museums - Standard Entry",
      "visitors": 2,
      "profile": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+39 123456789",
        "city": "Roma",
        "country": "Italia",
        "birth_date": "1990-01-15"
      },
      "participants": [
        {
          "first_name": "John",
          "last_name": "Doe",
          "email": "john@example.com",
          "phone": "+39 123456789"
        },
        {
          "first_name": "Jane",
          "last_name": "Doe",
          "email": "jane@example.com",
          "phone": "+39 987654321"
        }
      ]
    }
  ],
  "count": 1,
  "timestamp": "2026-05-22T10:30:00Z"
}
```

**This is exactly what the extension receives and uses for auto-booking!**

---

## 🔧 Troubleshooting

### Issue: Import Shows 0 Participants

**Check**:
1. Sheet has data rows (not just headers)
2. Column names match required format
3. No empty rows between header and data
4. Sheet is shared with service account

**Debug**:
```bash
docker-compose exec backend python manage.py shell
```

```python
from services.google_sheets_service import GoogleSheetsService

service = GoogleSheetsService()
sheet_url = 'https://docs.google.com/spreadsheets/d/1ZpGUSWlKM90NYzJIkAb8y1V6IarA9QWs3xRDcHRFX9M/edit?usp=sharing'

# Test reading sheet
try:
    data = service.read_sheet(sheet_url)
    print(f"✅ Sheet readable")
    print(f"   Rows: {len(data)}")
    print(f"   First row (headers): {data[0] if data else 'No data'}")
    print(f"   Second row (data): {data[1] if len(data) > 1 else 'No data'}")
except Exception as e:
    print(f"❌ Error: {e}")

exit()
```

### Issue: Wrong Data Imported

**Check**:
1. First row is headers (not data)
2. Data starts from row 2
3. No merged cells
4. All required columns present

**Fix**:
1. Ensure row 1 has column names
2. Ensure row 2+ has participant data
3. Remove any formatting issues
4. Re-import: `docker-compose exec backend python manage.py import_participants --agency-id 1`

---

## ✅ Success Checklist

- [ ] Google Sheet has correct format
- [ ] Sheet shared with service account (Editor permission)
- [ ] Sheet URL added to agency
- [ ] Import command successful
- [ ] BuyerProfile created in database
- [ ] Participants data stored
- [ ] API endpoint returns participant data
- [ ] Test slot created
- [ ] Extension detected slot
- [ ] Incognito window opened
- [ ] Form filled with Google Sheets data

---

## 🎯 Next Steps

Once verification is complete:

1. **Delete Test Slot**:
   ```bash
   docker-compose exec backend python manage.py shell
   >>> from monitors.models import HeldSlot
   >>> HeldSlot.objects.filter(slot_id__startswith='TEST').delete()
   >>> exit()
   ```

2. **Enable Auto-Sync** (Optional):
   - Add Google Sheets dependencies to `requirements.txt`
   - Rebuild containers
   - Uncomment auto-sync in settings
   - Participants will sync automatically every hour

3. **Create Real Monitoring Tasks**:
   - Via Telegram: `/monitor`
   - Via API: `POST /api/v1/monitor-tasks/`
   - Worker will monitor Vatican 24/7

4. **Keep Browser Open**:
   - Extension listens 24/7
   - Automatically books when tickets found
   - Uses your Google Sheets data

---

## 📞 Ready to Verify!

**Run these commands in order**:

```bash
# 1. Add sheet URL
docker-compose exec backend python manage.py shell
# (paste Python code from Step 3)

# 2. Import participants
docker-compose exec backend python manage.py import_participants --agency-id 1

# 3. Verify import
docker-compose exec backend python manage.py shell
# (paste Python code from Step 5)

# 4. Check API
curl http://localhost:8000/api/v1/available-slots/

# 5. Create test slot
docker-compose exec backend python manage.py shell
# (paste Python code from Step 6)

# 6. Watch extension auto-book!
```

**Let me know the output of each step and I'll help troubleshoot if needed!** 🚀
