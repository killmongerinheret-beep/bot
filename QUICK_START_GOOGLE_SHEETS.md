# Quick Start: Google Sheets Integration

**5-Minute Setup Guide**

---

## 🎯 Goal
Automatically import participant names from Google Sheets and use them for Vatican ticket bookings via the browser extension.

---

## 📋 Prerequisites

- ✅ Docker services running
- ✅ WOR agency configured (ID: 14)
- ✅ Buyer profile created via Telegram bot

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Install Dependencies (1 minute)

```bash
# Install Google Sheets packages
docker-compose exec backend pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

### Step 2: Create Google Sheet (2 minutes)

1. **Create new Google Sheet**
2. **Add these columns:**
   ```
   First Name | Last Name | Email | Phone | Birth Date | Gender | Notes
   ```

3. **Add participant data:**
   ```
   Mario | Rossi | mario@example.com | 3401234567 | 15/01/1990 | M | Adult
   Luigi | Verdi | luigi@example.com | 3407654321 | 20/05/1985 | M | Adult
   ```

4. **Make it public:**
   - Click "Share" button
   - Click "Change to anyone with the link"
   - Set to "Viewer"
   - Copy the URL

5. **Name the sheet:** `Vatican_Participants`

---

### Step 3: Import Participants (1 minute)

```bash
# Replace YOUR_SHEET_ID with your actual sheet ID
docker-compose exec backend python /app/backend/manage.py import_participants \
  --agency=WOR \
  --sheet-url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

**Expected Output:**
```
📊 Importing participants from Google Sheet...
✅ Found 2 participants:
  1. Mario Rossi (Adult)
  2. Luigi Verdi (Adult)
✅ Updated agency Google Sheet URL
✅ Saved 2 participants to BuyerProfile
```

---

## ✅ Verify It Works

```bash
# Test the API endpoint
curl -UseBasicParsing http://localhost:8000/api/v1/available-slots/
```

Should return:
```json
{"slots":[],"count":0,"timestamp":"2026-05-19T14:52:00Z"}
```

---

## 🔄 Update Participants

Anytime you change the Google Sheet, just re-run the import command:

```bash
docker-compose exec backend python /app/backend/manage.py import_participants --agency=WOR
```

---

## 🌐 Extension Integration

### Configure Extension (Backend Listener Mode)

1. Open extension popup
2. Select "Backend Listener" mode
3. Enter backend URL: `http://localhost:8000`
4. Set poll interval: 10 seconds
5. Click "Start Monitoring"

### What Happens Next

```
Extension polls → GET /api/v1/available-slots/ every 10s
  ↓
Slot found → Opens incognito window
  ↓
Auto-fills form → Uses participants from Google Sheet
  ↓
Booking complete → POST /api/v1/slots/{id}/mark-booked/
  ↓
Done! ✅
```

---

## 📊 API Endpoints

### Get Available Slots
```
GET http://localhost:8000/api/v1/available-slots/
```

Returns slots with participant data ready for auto-booking.

### Mark Slot Booked
```
POST http://localhost:8000/api/v1/slots/{slot_id}/mark-booked/
Body: {"reference": "VAT-123", "epay_url": "..."}
```

Called by extension after successful booking.

---

## 🔧 Troubleshooting

### "No participants found"
- Check sheet name is `Vatican_Participants`
- Verify column headers match exactly
- Ensure sheet has data rows

### "Agency not found"
- Check agency name: `docker-compose exec -T db psql -U postgres -d ticketbot -c "SELECT id, name FROM agencies;"`

### "No BuyerProfile found"
- Create profile via Telegram bot: `/setprofile`

---

## 📝 Example Google Sheet

**Sheet Name:** `Vatican_Participants`

| First Name | Last Name | Email              | Phone       | Birth Date | Gender | Notes  |
|------------|-----------|-------------------|-------------|------------|--------|--------|
| Mario      | Rossi     | mario@example.com | 3401234567  | 15/01/1990 | M      | Adult  |
| Luigi      | Verdi     | luigi@example.com | 3407654321  | 20/05/1985 | M      | Adult  |
| Anna       | Bianchi   | anna@example.com  | 3409876543  | 10/03/1992 | F      | Adult  |
| Sofia      | Neri      | sofia@example.com | 3402345678  | 25/08/2010 | F      | Child  |

**Share Link:** `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`

---

## 🎉 That's It!

You now have:
- ✅ Participant names in Google Sheets
- ✅ Automatic import to database
- ✅ API endpoints for extension
- ✅ Ready for auto-booking

**Next:** Configure your browser extension to poll the backend and start auto-booking! 🚀

