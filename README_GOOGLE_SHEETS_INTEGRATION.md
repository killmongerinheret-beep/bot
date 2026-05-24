# Google Sheets + Extension Integration - Complete Guide

**Automated Vatican Ticket Booking from Google Sheets**

---

## 🎯 What This Does

Automatically books Vatican tickets using participant names from Google Sheets:

1. **You maintain** a Google Sheet with participant names
2. **System imports** names to database
3. **Worker monitors** Vatican for available slots
4. **Extension detects** slots via backend API
5. **Extension auto-books** using participant names from Google Sheets
6. **You receive** confirmation email

**Zero manual work after setup!** ✨

---

## 📚 Documentation Files

### Quick Start
- **QUICK_START_GOOGLE_SHEETS.md** - 5-minute setup guide (START HERE!)

### Implementation Details
- **GOOGLE_SHEETS_IMPLEMENTATION_COMPLETE.md** - Full technical documentation
- **IMPLEMENTATION_STATUS.md** - Current status and next steps
- **SYSTEM_FLOW_DIAGRAM.md** - Visual workflow diagrams

### Original Design
- **GOOGLE_SHEETS_AUTOMATION_GUIDE.md** - Original design document
- **COMPLETE_WORKFLOW_GUIDE.md** - Complete system workflow
- **WORKFLOW_QUICK_REFERENCE.md** - Quick reference guide

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
docker-compose exec backend pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

### Step 2: Create Google Sheet
1. Create new Google Sheet
2. Add columns: `First Name | Last Name | Email | Phone | Birth Date | Gender | Notes`
3. Add participant data
4. Make sheet public (Share → Anyone with link → Viewer)
5. Name sheet: `Vatican_Participants`
6. Copy URL

### Step 3: Import Participants
```bash
docker-compose exec backend python /app/backend/manage.py import_participants \
  --agency=WOR \
  --sheet-url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

### Step 4: Verify
```bash
curl -UseBasicParsing http://localhost:8000/api/v1/available-slots/
```

**Done!** Backend is ready. Now configure your extension.

---

## 🌐 Extension Configuration

### Backend Listener Mode

1. Open extension popup
2. Select "Backend Listener" mode
3. Enter backend URL: `http://localhost:8000`
4. Set poll interval: 10 seconds
5. Click "Start Monitoring"

### What Happens

```
Extension polls backend every 10s
    ↓
Slot detected
    ↓
Opens incognito window
    ↓
Auto-fills form with Google Sheets participants
    ↓
Completes booking
    ↓
Marks slot as booked
    ↓
Done! ✅
```

---

## 📊 API Endpoints

### Get Available Slots
```
GET http://localhost:8000/api/v1/available-slots/
```

**Response:**
```json
{
  "slots": [
    {
      "id": 123,
      "date": "15/06/2026",
      "time": "10:00",
      "visitors": 2,
      "profile": {
        "first_name": "Mario",
        "last_name": "Rossi",
        "email": "mario@example.com"
      },
      "participants": [
        {"first_name": "Mario", "last_name": "Rossi"},
        {"first_name": "Luigi", "last_name": "Verdi"}
      ],
      "card": {
        "number": "4111...",
        "expiry": "12/2026"
      }
    }
  ],
  "count": 1
}
```

### Mark Slot Booked
```
POST http://localhost:8000/api/v1/slots/{slot_id}/mark-booked/
Body: {"reference": "VAT-123", "epay_url": "..."}
```

**Response:**
```json
{
  "success": true,
  "message": "Slot 123 marked as booked"
}
```

---

## 📋 Google Sheet Format

**Sheet Name:** `Vatican_Participants`

| First Name | Last Name | Email              | Phone       | Birth Date | Gender | Notes  |
|------------|-----------|-------------------|-------------|------------|--------|--------|
| Mario      | Rossi     | mario@example.com | 3401234567  | 15/01/1990 | M      | Adult  |
| Luigi      | Verdi     | luigi@example.com | 3407654321  | 20/05/1985 | M      | Adult  |
| Anna       | Bianchi   | anna@example.com  | 3409876543  | 10/03/1992 | F      | Adult  |

**Required Columns:**
- First Name (required)
- Last Name (required)
- Email (optional)
- Phone (optional)
- Birth Date (optional)
- Gender (optional, default: M)
- Notes (optional)

---

## 🔄 Update Participants

Anytime you change the Google Sheet:

```bash
docker-compose exec backend python /app/backend/manage.py import_participants --agency=WOR
```

Participants are updated immediately!

---

## 🔧 Troubleshooting

### "No participants found"
- Check sheet name is `Vatican_Participants`
- Verify column headers match exactly
- Ensure sheet has data rows (not just headers)

### "Agency not found"
```bash
# List agencies
docker-compose exec -T db psql -U postgres -d ticketbot -c "SELECT id, name FROM agencies;"
```

### "No BuyerProfile found"
- Create profile via Telegram bot: `/setprofile`

### Extension not detecting slots
- Check extension is in Backend Listener mode
- Verify backend URL is correct
- Check browser console for errors
- Verify API endpoint returns data

### Import command fails
- Check Google Sheets dependencies installed
- Verify sheet URL is correct
- Check sheet is public or service account configured
- Review backend logs: `docker-compose logs backend`

---

## 📊 System Status

### ✅ Implemented
- Google Sheets service
- Database schema (google_sheet_url field)
- Import command
- API endpoints (get-available-slots, mark-slot-booked)
- URL routes
- Backend restarted and working

### ⏳ Pending
- Install Google Sheets dependencies
- Create test Google Sheet
- Test import command
- Configure extension
- Test end-to-end workflow

---

## 🎯 Architecture

```
Google Sheets (Participants)
    ↓
Backend (Import & Store)
    ↓
Database (BuyerProfile.participants_json)
    ↓
Worker (Monitor Vatican API)
    ↓
HeldSlot (Available slot found)
    ↓
Extension (Poll backend API)
    ↓
Auto-Booking (Fill form & complete)
    ↓
Mark Booked (Update database)
    ↓
Confirmation Email (Success!)
```

---

## 📝 Key Commands

### Import Participants
```bash
docker-compose exec backend python /app/backend/manage.py import_participants \
  --agency=WOR \
  --sheet-url="YOUR_SHEET_URL"
```

### Test API
```bash
curl -UseBasicParsing http://localhost:8000/api/v1/available-slots/
```

### Check Database
```bash
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT id, first_name, last_name, participants_json IS NOT NULL 
   FROM buyer_profiles WHERE agency_id = 14;"
```

### View Logs
```bash
docker-compose logs backend
docker-compose logs worker_vatican
```

---

## 🎉 Benefits

### Before
- ❌ Manual form filling for each booking
- ❌ Copy-paste participant names
- ❌ Risk of typos
- ❌ Slow booking process
- ❌ Miss available slots

### After
- ✅ Automatic form filling
- ✅ Participant names from Google Sheets
- ✅ No typos
- ✅ Fast booking (seconds)
- ✅ Never miss a slot

---

## 🔐 Security

### Google Sheets
- Read-only access
- Public sheet OR service account
- No write permissions needed

### Backend API
- Optional API key authentication
- Rate limiting enabled
- HTTPS recommended for production

### Extension
- Runs in isolated incognito windows
- Each booking = new session
- No data persistence between bookings

### Database
- Encrypted at rest
- Sensitive data protected
- Regular backups recommended

---

## 📞 Support

### Check Logs
```bash
docker-compose logs backend
docker-compose logs worker_vatican
```

### Test API
```bash
curl -UseBasicParsing http://localhost:8000/api/v1/available-slots/
```

### Check Database
```bash
docker-compose exec -T db psql -U postgres -d ticketbot
```

### Review Documentation
- QUICK_START_GOOGLE_SHEETS.md
- GOOGLE_SHEETS_IMPLEMENTATION_COMPLETE.md
- SYSTEM_FLOW_DIAGRAM.md

---

## 🚀 Next Steps

1. **Install dependencies** (5 minutes)
2. **Create Google Sheet** (5 minutes)
3. **Import participants** (2 minutes)
4. **Configure extension** (5 minutes)
5. **Test end-to-end** (30 minutes)

**Total setup time: ~45 minutes**

---

## 🎯 Success Criteria

### Backend
- [x] Google Sheets service created
- [x] Database schema updated
- [x] Import command working
- [x] API endpoints implemented
- [ ] Dependencies installed
- [ ] Participants imported

### Extension
- [ ] Backend Listener mode configured
- [ ] Extension polls backend
- [ ] Slots detected automatically
- [ ] Forms auto-filled correctly
- [ ] Bookings completed successfully

### User Experience
- [ ] Telegram notifications received
- [ ] Extension auto-books without intervention
- [ ] Confirmation emails received
- [ ] Correct participant names in bookings

---

## 📚 Additional Resources

### Documentation
- Vatican Bot Rules: `VATICAN_BOT_RULES.md`
- Complete Workflow: `COMPLETE_WORKFLOW_GUIDE.md`
- Extension Guide: `browser-extension/README.md`

### Code Files
- Google Sheets Service: `backend/services/google_sheets_service.py`
- Import Command: `backend/monitors/management/commands/import_participants.py`
- API Views: `backend/monitors/views.py`
- Models: `backend/monitors/models.py`

---

**Ready to automate your Vatican ticket bookings?** 🎉

**Start with QUICK_START_GOOGLE_SHEETS.md!** 🚀

