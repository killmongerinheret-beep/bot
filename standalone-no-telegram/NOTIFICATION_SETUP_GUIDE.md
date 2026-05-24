# Telegram Notification Setup - Standalone System

## 🎯 Your Setup Requirements

You want:
1. ✅ **No Telegram for Input** - All booking requests from Google Sheets
2. ✅ **Telegram for Notifications Only** - Send payment links to specific Telegram chat
3. ✅ **Multi-Computer Extension** - Extension works on any computer
4. ✅ **Separate Notifications per Computer** (Optional) - Each extension can notify different Telegram chat

---

## 📊 System Architecture

```
GOOGLE SHEETS (Input)
   ↓
BACKEND (Creates Tasks)
   ↓
WORKER (Monitors Vatican)
   ↓
EXTENSION (Auto-Books)
   ↓
TELEGRAM (Notifications Only)
```

**Key Point**: Telegram is ONLY used for notifications, NOT for input or commands.

---

## 🔧 Configuration Options

### Option 1: Single Telegram Chat for All Notifications (Simplest)

**Use Case**: You have one Telegram chat that receives all booking notifications from all computers.

**Setup**:
1. All extensions connect to same backend
2. Backend sends all notifications to one Telegram chat
3. Simple and centralized

**Pros**:
- ✅ Simple setup
- ✅ All notifications in one place
- ✅ Easy to monitor

**Cons**:
- ❌ Can't distinguish which computer completed booking
- ❌ All notifications mixed together

---

### Option 2: Separate Telegram Chat per Computer (Recommended)

**Use Case**: You have multiple computers running extensions, and want each computer's notifications in a separate Telegram chat.

**Setup**:
1. Each computer has its own "Agency" in the system
2. Each Agency has its own Telegram chat
3. Extension on Computer A → Agency A → Telegram Chat A
4. Extension on Computer B → Agency B → Telegram Chat B

**Pros**:
- ✅ Know which computer completed booking
- ✅ Separate notification streams
- ✅ Can disable specific computers easily

**Cons**:
- ❌ More setup required
- ❌ Need multiple Telegram chats

---

### Option 3: Hybrid - One Input, Multiple Notification Chats

**Use Case**: All booking requests in one Google Sheet, but notifications go to different Telegram chats based on which computer completed the booking.

**Setup**:
1. One Google Sheet with all booking requests
2. Multiple Agencies (one per computer)
3. Backend assigns tasks to specific agencies
4. Each agency notifies its own Telegram chat

**Pros**:
- ✅ Centralized input (one Google Sheet)
- ✅ Distributed notifications (multiple Telegram chats)
- ✅ Best of both worlds

**Cons**:
- ❌ Most complex setup
- ❌ Need task routing logic

---

## 🚀 Recommended Setup (Option 2)

I recommend **Option 2** because it's clean, scalable, and easy to manage.

### Step 1: Create Telegram Chats

Create separate Telegram groups/chats for each computer:

1. **Computer 1 (Office)**:
   - Create Telegram group: "Vatican Bot - Office"
   - Add your bot to the group
   - Get chat ID

2. **Computer 2 (Home)**:
   - Create Telegram group: "Vatican Bot - Home"
   - Add your bot to the group
   - Get chat ID

3. **Computer 3 (Laptop)**:
   - Create Telegram group: "Vatican Bot - Laptop"
   - Add your bot to the group
   - Get chat ID

**How to Get Chat ID**:
```powershell
# Send a message in the group, then run:
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"

# Look for "chat":{"id":-1001234567890}
```

---

### Step 2: Create Agencies in Database

Create one agency per computer:

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Agency, TelegramGroup

# Computer 1 - Office
agency_office = Agency.objects.create(
    name="Office Computer",
    api_key="office-key-123",
    plan="pro",
    is_active=True,
    google_sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
)

# Create Telegram group for Office
TelegramGroup.objects.create(
    chat_id="-1001234567890",  # Your Office group chat ID
    chat_type="group",
    chat_title="Vatican Bot - Office",
    agency=agency_office,
    status="approved",  # Pre-approve
    notification_enabled=True
)

# Computer 2 - Home
agency_home = Agency.objects.create(
    name="Home Computer",
    api_key="home-key-456",
    plan="pro",
    is_active=True,
    google_sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"  # Same sheet
)

# Create Telegram group for Home
TelegramGroup.objects.create(
    chat_id="-1009876543210",  # Your Home group chat ID
    chat_type="group",
    chat_title="Vatican Bot - Home",
    agency=agency_home,
    status="approved",
    notification_enabled=True
)

# Computer 3 - Laptop
agency_laptop = Agency.objects.create(
    name="Laptop Computer",
    api_key="laptop-key-789",
    plan="pro",
    is_active=True,
    google_sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"  # Same sheet
)

# Create Telegram group for Laptop
TelegramGroup.objects.create(
    chat_id="-1005555555555",  # Your Laptop group chat ID
    chat_type="group",
    chat_title="Vatican Bot - Laptop",
    agency=agency_laptop,
    status="approved",
    notification_enabled=True
)

print("✅ Created 3 agencies with Telegram groups")
exit()
```

---

### Step 3: Configure Extensions

On each computer, configure the extension with its agency:

**Computer 1 (Office)**:
1. Install extension
2. Open extension settings
3. Backend URL: `http://your-backend-url:8000`
4. Agency ID: `1` (Office agency ID)
5. Save

**Computer 2 (Home)**:
1. Install extension
2. Open extension settings
3. Backend URL: `http://your-backend-url:8000`
4. Agency ID: `2` (Home agency ID)
5. Save

**Computer 3 (Laptop)**:
1. Install extension
2. Open extension settings
3. Backend URL: `http://your-backend-url:8000`
4. Agency ID: `3` (Laptop agency ID)
5. Save

---

### Step 4: Update Extension to Support Agency ID

The extension needs a small update to send agency ID with API requests.

**Edit `browser-extension/background.js`**:

Find the `pollBackend` function and add agency ID:

```javascript
async function pollBackend() {
    const settings = await chrome.storage.local.get(['backendUrl', 'agencyId']);
    const backendUrl = settings.backendUrl || 'http://localhost:8000';
    const agencyId = settings.agencyId || 1;  // Default to agency 1
    
    try {
        const response = await fetch(`${backendUrl}/api/v1/available-slots/?agency_id=${agencyId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // ... rest of the code
    } catch (error) {
        console.error('[Backend Listener] Error:', error);
    }
}
```

**Edit `browser-extension/options.html`**:

Add agency ID field:

```html
<div class="form-group">
    <label for="agencyId">Agency ID:</label>
    <input type="number" id="agencyId" placeholder="1">
    <small>Enter your agency ID (1, 2, 3, etc.)</small>
</div>
```

**Edit `browser-extension/options.js`**:

Save/load agency ID:

```javascript
// Load settings
chrome.storage.local.get(['backendUrl', 'agencyId'], (result) => {
    document.getElementById('backendUrl').value = result.backendUrl || 'http://localhost:8000';
    document.getElementById('agencyId').value = result.agencyId || 1;
});

// Save settings
document.getElementById('saveBtn').addEventListener('click', () => {
    const backendUrl = document.getElementById('backendUrl').value;
    const agencyId = parseInt(document.getElementById('agencyId').value) || 1;
    
    chrome.storage.local.set({
        backendUrl: backendUrl,
        agencyId: agencyId
    }, () => {
        alert('Settings saved!');
    });
});
```

---

### Step 5: Test Notifications

Test that each computer sends notifications to its own Telegram chat:

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.notification_utils import send_telegram_signal, format_vatican_notification
from monitors.models import Agency, TelegramGroup

# Test Office notifications
office_agency = Agency.objects.get(name="Office Computer")
office_groups = TelegramGroup.objects.filter(agency=office_agency, status='approved')

for group in office_groups:
    message = "🧪 Test notification from Office Computer"
    send_telegram_signal(group.chat_id, message)
    print(f"✅ Sent test to Office: {group.chat_title}")

# Test Home notifications
home_agency = Agency.objects.get(name="Home Computer")
home_groups = TelegramGroup.objects.filter(agency=home_agency, status='approved')

for group in home_groups:
    message = "🧪 Test notification from Home Computer"
    send_telegram_signal(group.chat_id, message)
    print(f"✅ Sent test to Home: {group.chat_title}")

# Test Laptop notifications
laptop_agency = Agency.objects.get(name="Laptop Computer")
laptop_groups = TelegramGroup.objects.filter(agency=laptop_agency, status='approved')

for group in laptop_groups:
    message = "🧪 Test notification from Laptop Computer"
    send_telegram_signal(group.chat_id, message)
    print(f"✅ Sent test to Laptop: {group.chat_title}")

exit()
```

**Expected Result**:
- Office Telegram group receives: "🧪 Test notification from Office Computer"
- Home Telegram group receives: "🧪 Test notification from Home Computer"
- Laptop Telegram group receives: "🧪 Test notification from Laptop Computer"

---

## 📊 Notification Flow

### When Tickets Found

```
WORKER detects tickets
   ↓
Creates AvailableSlot
   ↓
Sends Telegram notification to Agency's groups
   ↓
"🎉 TICKETS JUST OPENED! [date] [time] [link]"
```

### When Booking Completed

```
EXTENSION completes booking
   ↓
Calls /api/v1/slots/{id}/mark-booked/
   ↓
Backend updates Google Sheets
   ↓
Sends Telegram notification to Agency's groups
   ↓
"✅ BOOKING COMPLETED! [reference] [payment link]"
```

---

## 🎯 What Notifications You'll Receive

### 1. Tickets Available Notification

```
🎉 TICKETS JUST OPENED!

━━━━━━━━━━━━━━━━━━━━━━
📅 DATE: 28/03/2026
🎫 TICKET: Vatican Museums - Standard Entry
👥 VISITORS: 2
━━━━━━━━━━━━━━━━━━━━━━

⏰ Checked at: 14:30:15 Rome time
🔍 Method: search_api

⭐ YOUR PREFERRED TIMES (2):
   ⭐ 10:00
   ⭐ 14:00

🕐 Other Available Times (5):
   • 08:00
   • 09:00
   • 11:00
   • 12:00
   • 15:00

📊 Total Available Slots: 7

━━━━━━━━━━━━━━━━━━━━━━
🔗 BOOK NOW:
https://tickets.museivaticani.va/home/fromtag/2/...
━━━━━━━━━━━━━━━━━━━━━━

⚡ Act fast - tickets sell quickly!
```

### 2. Booking Completed Notification

```
✅ BOOKING COMPLETED!

━━━━━━━━━━━━━━━━━━━━━━
📅 DATE: 28/03/2026
⏰ TIME: 10:00
👥 VISITORS: 2
🎫 TICKET: Vatican Museums - Standard Entry
━━━━━━━━━━━━━━━━━━━━━━

📝 Booking Reference: VAT-12345
💳 Total Price: €34.00

🔗 Payment Link:
https://epay.catholica.va/...

⚠️ Complete payment within 24 hours

✅ Booked by: Office Computer
📊 Request ID: REQ-001
```

---

## 🔧 Advanced Configuration

### Disable Notifications for Specific Computer

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import TelegramGroup

# Disable Office computer notifications
office_group = TelegramGroup.objects.get(chat_title="Vatican Bot - Office")
office_group.notification_enabled = False
office_group.save()

print("✅ Disabled notifications for Office computer")
exit()
```

### Change Notification Chat for Computer

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import TelegramGroup

# Change Office computer to new chat
office_group = TelegramGroup.objects.get(chat_title="Vatican Bot - Office")
office_group.chat_id = "-1001111111111"  # New chat ID
office_group.save()

print("✅ Updated Office computer notification chat")
exit()
```

### Add Multiple Notification Chats per Computer

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Agency, TelegramGroup

# Get Office agency
office_agency = Agency.objects.get(name="Office Computer")

# Add second notification chat
TelegramGroup.objects.create(
    chat_id="-1002222222222",  # Second chat ID
    chat_type="group",
    chat_title="Vatican Bot - Office Backup",
    agency=office_agency,
    status="approved",
    notification_enabled=True
)

print("✅ Added second notification chat for Office computer")
exit()
```

---

## 📝 Summary

### What You Have Now

1. ✅ **Google Sheets Input** - All booking requests from sheets
2. ✅ **No Telegram Commands** - System fully automated
3. ✅ **Telegram Notifications Only** - Payment links sent to Telegram
4. ✅ **Multi-Computer Support** - Each computer has own agency
5. ✅ **Separate Notification Chats** - Each computer notifies different chat
6. ✅ **Centralized Management** - One Google Sheet, multiple computers

### Notification Types

1. **Tickets Available** - When worker finds tickets
2. **Booking Completed** - When extension completes booking
3. **Payment Link** - Link to complete payment
4. **Status Updates** - Google Sheets status changes

### Configuration

- **Agency per Computer**: Each computer = one agency
- **Telegram Group per Agency**: Each agency = one or more Telegram groups
- **Extension Configuration**: Each extension configured with agency ID
- **Google Sheets**: All agencies can share same Google Sheet

---

## 🆘 Troubleshooting

### Issue: Not Receiving Notifications

**Check Telegram group status:**
```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import TelegramGroup

groups = TelegramGroup.objects.all()
for group in groups:
    print(f"{group.chat_title}: status={group.status}, enabled={group.notification_enabled}")
exit()
```

**Fix: Approve and enable group:**
```python
group = TelegramGroup.objects.get(chat_title="Vatican Bot - Office")
group.status = "approved"
group.notification_enabled = True
group.save()
```

### Issue: Notifications Going to Wrong Chat

**Check agency-group mapping:**
```python
from monitors.models import Agency, TelegramGroup

agency = Agency.objects.get(name="Office Computer")
groups = TelegramGroup.objects.filter(agency=agency)

print(f"Agency: {agency.name}")
for group in groups:
    print(f"  - {group.chat_title} ({group.chat_id})")
```

### Issue: Extension Not Sending Agency ID

**Check extension settings:**
1. Open extension
2. Click "Settings"
3. Verify "Agency ID" field exists and has correct value
4. If missing, update extension files as shown in Step 4

---

**Setup Time**: 30 minutes  
**Complexity**: Medium  
**Recommended**: Option 2 (Separate chat per computer)  
**Scalability**: Unlimited computers
