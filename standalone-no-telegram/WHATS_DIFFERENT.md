# What's Different - Standalone vs Telegram Version

## 🎯 Key Differences

| Feature | Telegram Version | Standalone Version |
|---------|------------------|-------------------|
| **Task Creation** | Manual via `/monitor` command | Automatic from Google Sheets |
| **Input Source** | Telegram bot | Google Sheets only |
| **User Interaction** | Telegram chat | Google Sheets rows |
| **Notifications** | Telegram messages | Google Sheets status updates |
| **Setup Complexity** | Requires Telegram bot token | No Telegram needed |
| **Automation Level** | Semi-automated | Fully automated |

---

## 📁 New Files (Standalone Only)

These files are NEW and only exist in standalone version:

```
standalone-no-telegram/
├── backend/
│   ├── services/
│   │   └── booking_sync_service.py          ← NEW: Syncs from Google Sheets
│   └── monitors/
│       ├── tasks_booking_sync.py            ← NEW: Celery task for auto-sync
│       └── migrations/
│           └── 0028_add_external_reference.py ← NEW: Database migration
```

---

## 📝 Modified Files (What Changed)

### 1. `backend/core/settings.py`

**Added**:
```python
CELERY_BEAT_SCHEDULE = {
    # ... existing tasks ...
    
    # NEW: Auto-sync from Google Sheets
    'sync-booking-requests': {
        'task': 'monitors.tasks_booking_sync.sync_booking_requests',
        'schedule': crontab(minute='*/5'),
    },
}
```

### 2. `backend/core/celery.py`

**Added**:
```python
app.autodiscover_tasks([
    'monitors',
    'monitors.tasks_google_sheets',
    'monitors.tasks_booking_sync',  # NEW
])
```

### 3. `backend/monitors/views.py`

**Updated** `mark_slot_booked()` function:
```python
# Added Google Sheets update when booking completes
if slot.task and slot.task.external_reference:
    sync_service = BookingSyncService()
    sync_service.update_booking_completion(
        slot.task.id,
        reference or f'VAT-{slot.id}'
    )
```

### 4. `backend/monitors/models.py`

**Added** fields to `MonitorTask`:
```python
external_reference = models.CharField(max_length=100, null=True, blank=True)
created_via = models.CharField(max_length=50, default='manual')
```

---

## 🔄 Data Flow Comparison

### Telegram Version

```
USER
  ↓ /monitor command
TELEGRAM BOT
  ↓ Creates MonitorTask
BACKEND DATABASE
  ↓
WORKER (monitors Vatican)
  ↓
EXTENSION (auto-books)
  ↓
TELEGRAM BOT (sends notification)
```

### Standalone Version

```
BOKUN BOOKING
  ↓
GOOGLE SHEETS (Booking Requests + Participants)
  ↓ Auto-sync every 5 minutes
BACKEND (Creates MonitorTask automatically)
  ↓
WORKER (monitors Vatican)
  ↓
EXTENSION (auto-books)
  ↓
BACKEND (Updates Google Sheets status)
```

---

## 🔧 Configuration Differences

### Telegram Version Requires

```env
# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ADMIN_ID=your-user-id

# Google Sheets (optional)
GOOGLE_SHEETS_CREDENTIALS_JSON=path/to/credentials.json
```

### Standalone Version Requires

```env
# Google Sheets (required)
GOOGLE_SHEETS_CREDENTIALS_JSON=path/to/credentials.json

# No Telegram tokens needed!
```

---

## 📊 Google Sheets Format

### Telegram Version

**Single sheet** with participants:
```
First Name | Last Name | Email | Phone | Birth Date
John       | Doe       | ...   | ...   | ...
```

### Standalone Version

**Two sheets**:

**Sheet 1: Booking Requests**
```
Request ID | Date | Visitors | Ticket Type | Status | Booking Ref
REQ-001    | ...  | 2        | standard    | pending| 
```

**Sheet 2: Participants**
```
Request ID | First Name | Last Name | Email | Phone
REQ-001    | John       | Doe       | ...   | ...
REQ-001    | Jane       | Doe       | ...   | ...
```

---

## 🎯 Use Cases

### Use Telegram Version When

- ✅ You want manual control over each booking
- ✅ Users interact directly with bot
- ✅ You need real-time Telegram notifications
- ✅ You prefer command-based interface
- ✅ Multiple users need to create tasks independently

### Use Standalone Version When

- ✅ You want fully automated workflow
- ✅ Bokun (or other system) feeds Google Sheets
- ✅ No user interaction needed
- ✅ You prefer spreadsheet-based management
- ✅ You want centralized booking request management
- ✅ You don't want to manage Telegram bot

---

## 🔄 Can I Use Both?

**Yes!** You can run both versions simultaneously:

1. **Telegram version** for manual bookings
2. **Standalone version** for automated bookings from Bokun

Both will:
- Share the same database
- Use the same worker
- Use the same extension
- Work independently without conflicts

Just ensure:
- Different `external_reference` values
- Different `created_via` values ('telegram' vs 'google_sheets')

---

## 📦 What's Shared (Same in Both)

These components are **identical** in both versions:

- ✅ **Worker Vatican** - Same monitoring logic
- ✅ **Browser Extension** - Same auto-booking
- ✅ **Database Models** - Same structure (with added fields)
- ✅ **Vatican API Integration** - Same Search API approach
- ✅ **Proxy Support** - Same Oxylabs integration
- ✅ **Docker Setup** - Same containers

---

## 🚀 Migration Path

### From Telegram to Standalone

1. Keep Telegram version running
2. Add standalone files
3. Update Google Sheets format
4. Run migration
5. Restart services
6. Both versions work simultaneously
7. Gradually phase out Telegram if desired

### From Standalone to Telegram

1. Keep standalone version running
2. Add Telegram bot token to `.env`
3. Start telegram_bot service
4. Both versions work simultaneously
5. Users can use either Telegram or Google Sheets

---

## 📊 Feature Comparison Matrix

| Feature | Telegram | Standalone | Both |
|---------|----------|------------|------|
| Auto-monitoring | ✅ | ✅ | ✅ |
| Auto-booking | ✅ | ✅ | ✅ |
| Google Sheets participants | ✅ | ✅ | ✅ |
| Proxy support | ✅ | ✅ | ✅ |
| Manual task creation | ✅ | ❌ | ✅ |
| Automatic task creation | ❌ | ✅ | ✅ |
| Telegram notifications | ✅ | ❌ | ✅ |
| Google Sheets status updates | ❌ | ✅ | ✅ |
| User commands | ✅ | ❌ | ✅ |
| Bokun integration | ⚠️ Manual | ✅ Auto | ✅ |
| Multi-user | ✅ | ✅ | ✅ |
| Portable extension | ✅ | ✅ | ✅ |

---

## 💡 Recommendations

### Choose Standalone If

- You have Bokun → Google Sheets automation
- You want zero manual intervention
- You prefer spreadsheet management
- You don't need Telegram notifications
- You want simpler setup (no bot token)

### Choose Telegram If

- You want manual control
- Users need to interact with bot
- You want real-time notifications
- You prefer command-based interface
- You don't have automated sheet updates

### Use Both If

- You want flexibility
- Some bookings are manual (Telegram)
- Some bookings are automated (Bokun → Sheets)
- You want both notification methods
- You want maximum coverage

---

## 🔧 Technical Differences

### Database Schema

**Telegram Version**:
```python
class MonitorTask(models.Model):
    agency = models.ForeignKey(Agency)
    date = models.CharField(max_length=20)
    visitors = models.IntegerField()
    ticket_type = models.IntegerField()
    is_active = models.BooleanField()
    # ... other fields
```

**Standalone Version** (adds):
```python
class MonitorTask(models.Model):
    # ... all fields from Telegram version ...
    external_reference = models.CharField(max_length=100)  # NEW
    created_via = models.CharField(max_length=50)          # NEW
```

### Services

**Telegram Version**:
- `telegram_bot/` - Telegram bot service
- `backend/monitors/tasks.py` - Manual task management

**Standalone Version** (adds):
- `backend/services/booking_sync_service.py` - Auto-sync service
- `backend/monitors/tasks_booking_sync.py` - Celery auto-sync task

---

## ✅ Summary

**Standalone version is**:
- ✅ Simpler (no Telegram)
- ✅ More automated (auto-sync)
- ✅ Better for Bokun integration
- ✅ Spreadsheet-centric
- ✅ Fully hands-off

**Telegram version is**:
- ✅ More interactive
- ✅ Better for manual control
- ✅ Real-time notifications
- ✅ Command-based
- ✅ Multi-user friendly

**Both versions**:
- ✅ Can run simultaneously
- ✅ Share same worker and extension
- ✅ Use same database
- ✅ Support same features
- ✅ Work independently

---

**Choose based on your workflow!** 🚀
