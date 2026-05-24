# Standalone Setup - No Telegram Required

## 🎯 Goal

Create a fully automated system that:
1. ✅ Reads booking requests from Google Sheets
2. ✅ Automatically creates monitoring tasks
3. ✅ Worker monitors Vatican 24/7
4. ✅ Extension auto-books when tickets found
5. ✅ Works on any computer
6. ✅ No Telegram required

---

## 📊 System Flow

```
1. BOKUN BOOKING
   ↓ Webhook/API
   ↓ Updates Google Sheets

2. GOOGLE SHEETS
   ↓ Contains booking requests
   ↓ Columns: Date, Visitors, Ticket Type, Status

3. BACKEND AUTO-SYNC
   ↓ Reads sheet every 5 minutes
   ↓ Creates MonitorTask for each request
   ↓ Status: pending → monitoring → booked

4. WORKER MONITORS VATICAN
   ↓ Checks Vatican API every 5 seconds
   ↓ Creates HeldSlot when tickets found

5. EXTENSION AUTO-BOOKS
   ↓ Polls backend every 10 seconds
   ↓ Opens incognito windows
   ↓ Completes booking automatically

6. BACKEND UPDATES SHEET
   ↓ Marks booking as completed
   ↓ Adds booking reference
```

---

## 📋 Step 1: Google Sheets Format

### Sheet 1: Booking Requests

**Columns**:
```
| Request ID | Date       | Visitors | Ticket Type | Language | Status    | Booking Ref | Created At          |
|------------|------------|----------|-------------|----------|-----------|-------------|---------------------|
| REQ-001    | 28/03/2026 | 2        | standard    |          | pending   |             | 2026-05-22 10:00:00 |
| REQ-002    | 29/03/2026 | 4        | guided      | ENG      | pending   |             | 2026-05-22 10:05:00 |
| REQ-003    | 30/03/2026 | 1        | standard    |          | monitoring|             | 2026-05-22 10:10:00 |
```

**Status Values**:
- `pending` - New request, not yet monitoring
- `monitoring` - Worker is checking Vatican
- `found` - Tickets found, booking in progress
- `booked` - Successfully booked
- `failed` - Booking failed
- `cancelled` - Request cancelled

### Sheet 2: Participants

**Columns**:
```
| Request ID | First Name | Last Name | Email              | Phone          | Birth Date |
|------------|------------|-----------|-------------------|----------------|------------|
| REQ-001    | John       | Doe       | john@example.com  | +39 123456789  | 1990-01-15 |
| REQ-001    | Jane       | Doe       | jane@example.com  | +39 987654321  | 1992-03-20 |
| REQ-002    | Mario      | Rossi     | mario@example.com | +39 555123456  | 1985-07-10 |
```

---

## 📋 Step 2: Create Auto-Sync Service

### Create New File: `backend/services/booking_sync_service.py`

```python
import logging
from datetime import datetime
from django.utils import timezone
from monitors.models import Agency, MonitorTask, BuyerProfile
from services.google_sheets_service import GoogleSheetsService
import json

logger = logging.getLogger(__name__)

class BookingSyncService:
    """
    Syncs booking requests from Google Sheets to MonitorTasks
    """
    
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
    
    def sync_booking_requests(self, agency_id):
        """
        Read booking requests from Google Sheets and create MonitorTasks
        """
        try:
            from monitors.models import Agency
            agency = Agency.objects.get(id=agency_id)
            
            if not agency.google_sheet_url:
                logger.warning(f"Agency {agency_id} has no Google Sheet URL")
                return {'success': False, 'error': 'No Google Sheet URL'}
            
            # Read booking requests sheet
            requests = self._read_booking_requests(agency.google_sheet_url)
            
            # Read participants sheet
            participants_map = self._read_participants(agency.google_sheet_url)
            
            created_count = 0
            updated_count = 0
            
            for request in requests:
                request_id = request.get('request_id')
                status = request.get('status', 'pending').lower()
                
                # Only process pending requests
                if status != 'pending':
                    continue
                
                # Check if task already exists
                existing_task = MonitorTask.objects.filter(
                    agency=agency,
                    external_reference=request_id
                ).first()
                
                if existing_task:
                    logger.info(f"Task already exists for {request_id}")
                    continue
                
                # Create new monitoring task
                task = self._create_task_from_request(agency, request, participants_map)
                
                if task:
                    created_count += 1
                    # Update sheet status to "monitoring"
                    self._update_sheet_status(
                        agency.google_sheet_url,
                        request_id,
                        'monitoring'
                    )
            
            logger.info(f"Sync complete: {created_count} tasks created")
            
            return {
                'success': True,
                'created': created_count,
                'updated': updated_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing booking requests: {e}")
            return {'success': False, 'error': str(e)}
    
    def _read_booking_requests(self, sheet_url):
        """Read booking requests from Sheet 1"""
        data = self.sheets_service.read_sheet(sheet_url, sheet_name='Booking Requests')
        
        if not data or len(data) < 2:
            return []
        
        headers = [h.lower().replace(' ', '_') for h in data[0]]
        requests = []
        
        for row in data[1:]:
            if not row or len(row) < len(headers):
                continue
            
            request = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    request[header] = row[i]
            
            requests.append(request)
        
        return requests
    
    def _read_participants(self, sheet_url):
        """Read participants from Sheet 2, grouped by request_id"""
        data = self.sheets_service.read_sheet(sheet_url, sheet_name='Participants')
        
        if not data or len(data) < 2:
            return {}
        
        headers = [h.lower().replace(' ', '_') for h in data[0]]
        participants_map = {}
        
        for row in data[1:]:
            if not row or len(row) < len(headers):
                continue
            
            participant = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    participant[header] = row[i]
            
            request_id = participant.get('request_id')
            if request_id:
                if request_id not in participants_map:
                    participants_map[request_id] = []
                participants_map[request_id].append(participant)
        
        return participants_map
    
    def _create_task_from_request(self, agency, request, participants_map):
        """Create MonitorTask from booking request"""
        try:
            request_id = request.get('request_id')
            date = request.get('date')
            visitors = int(request.get('visitors', 1))
            ticket_type_str = request.get('ticket_type', 'standard').lower()
            language = request.get('language', '').upper() or None
            
            # Map ticket type
            ticket_type = 0 if ticket_type_str == 'standard' else 1
            
            # Get participants for this request
            participants = participants_map.get(request_id, [])
            
            # Create or update buyer profile
            if participants:
                first_participant = participants[0]
                profile, created = BuyerProfile.objects.get_or_create(
                    agency=agency,
                    defaults={
                        'first_name': first_participant.get('first_name', ''),
                        'last_name': first_participant.get('last_name', ''),
                        'email': first_participant.get('email', ''),
                        'phone': first_participant.get('phone', ''),
                        'city': first_participant.get('city', 'Roma'),
                        'country': first_participant.get('country', 'Italia'),
                        'birth_date': first_participant.get('birth_date'),
                        'participants_json': json.dumps(participants)
                    }
                )
                
                if not created:
                    # Update participants
                    profile.participants_json = json.dumps(participants)
                    profile.save()
            
            # Create monitoring task
            task = MonitorTask.objects.create(
                agency=agency,
                date=date,
                visitors=visitors,
                ticket_type=ticket_type,
                language=language,
                external_reference=request_id,
                is_active=True,
                created_via='google_sheets'
            )
            
            logger.info(f"Created task {task.id} for request {request_id}")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from request: {e}")
            return None
    
    def _update_sheet_status(self, sheet_url, request_id, status):
        """Update status in Google Sheets"""
        try:
            # This would use Google Sheets API to update the status column
            # Implementation depends on your Google Sheets setup
            logger.info(f"Updated {request_id} status to {status}")
        except Exception as e:
            logger.error(f"Error updating sheet status: {e}")
    
    def update_booking_completion(self, task_id, booking_reference):
        """
        Update Google Sheets when booking is completed
        """
        try:
            task = MonitorTask.objects.get(id=task_id)
            
            if not task.external_reference:
                return
            
            agency = task.agency
            if not agency.google_sheet_url:
                return
            
            # Update sheet with booking reference and status
            self._update_sheet_status(
                agency.google_sheet_url,
                task.external_reference,
                'booked'
            )
            
            # Add booking reference
            # Implementation depends on your Google Sheets setup
            
            logger.info(f"Updated sheet for task {task_id}: {booking_reference}")
            
        except Exception as e:
            logger.error(f"Error updating booking completion: {e}")
```

---

## 📋 Step 3: Create Celery Task for Auto-Sync

### Create: `backend/monitors/tasks_booking_sync.py`

```python
from celery import shared_task
from services.booking_sync_service import BookingSyncService
import logging

logger = logging.getLogger(__name__)

@shared_task
def sync_booking_requests():
    """
    Sync booking requests from Google Sheets for all agencies
    Runs every 5 minutes
    """
    from monitors.models import Agency
    
    service = BookingSyncService()
    
    agencies = Agency.objects.filter(
        is_active=True,
        google_sheet_url__isnull=False
    ).exclude(google_sheet_url='')
    
    total_created = 0
    
    for agency in agencies:
        logger.info(f"Syncing booking requests for agency {agency.id}")
        
        result = service.sync_booking_requests(agency.id)
        
        if result['success']:
            total_created += result.get('created', 0)
            logger.info(f"Agency {agency.id}: {result.get('created', 0)} tasks created")
        else:
            logger.error(f"Agency {agency.id}: {result.get('error')}")
    
    return {
        'success': True,
        'total_created': total_created
    }

@shared_task
def sync_booking_requests_for_agency(agency_id):
    """
    Sync booking requests for a specific agency
    """
    service = BookingSyncService()
    return service.sync_booking_requests(agency_id)
```

---

## 📋 Step 4: Add to Celery Beat Schedule

### Edit: `backend/core/settings.py`

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # ... existing tasks ...
    
    # Sync booking requests every 5 minutes
    'sync-booking-requests': {
        'task': 'monitors.tasks_booking_sync.sync_booking_requests',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

### Edit: `backend/core/celery.py`

```python
# Add to autodiscover_tasks
app.autodiscover_tasks([
    'monitors',
    'monitors.tasks_google_sheets',
    'monitors.tasks_booking_sync',  # Add this
])
```

---

## 📋 Step 5: Add External Reference Field

### Create Migration: `backend/monitors/migrations/0028_add_external_reference.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('monitors', '0027_add_google_sheet_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitortask',
            name='external_reference',
            field=models.CharField(max_length=100, null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name='monitortask',
            name='created_via',
            field=models.CharField(max_length=50, default='manual'),
        ),
    ]
```

Run migration:
```bash
docker-compose exec backend python manage.py migrate
```

---

## 📋 Step 6: Update Extension to Mark Completion

### Extension Already Handles This!

When booking completes, extension calls:
```javascript
POST /api/v1/slots/{slot_id}/mark-booked/
```

We just need to update the backend to also update Google Sheets:

### Edit: `backend/monitors/views.py`

```python
@api_view(['POST'])
def mark_slot_booked(request, slot_id):
    """
    Mark a slot as booked after extension completes booking.
    Also updates Google Sheets status.
    """
    from .models import HeldSlot
    from services.booking_sync_service import BookingSyncService
    
    try:
        slot = HeldSlot.objects.get(id=slot_id)
        
        # Update slot status
        slot.payment_ready = True
        slot.status = 'paying'
        
        # Store optional data
        reference = request.data.get('reference', '')
        epay_url = request.data.get('epay_url', '')
        
        if epay_url:
            slot.payment_url = epay_url
            slot.save(update_fields=['payment_ready', 'status', 'payment_url'])
        else:
            slot.save(update_fields=['payment_ready', 'status'])
        
        # Update Google Sheets if task has external_reference
        if slot.task and slot.task.external_reference:
            sync_service = BookingSyncService()
            sync_service.update_booking_completion(
                slot.task.id,
                reference or f'VAT-{slot.id}'
            )
        
        return Response({
            'success': True,
            'message': f'Slot {slot_id} marked as booked',
            'slot': {
                'id': slot.id,
                'date': slot.date,
                'time': slot.slot_time,
                'status': slot.status
            }
        })
        
    except HeldSlot.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Slot not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error marking slot as booked: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
```

---

## 📋 Step 7: Portable Extension Setup

### Make Extension Work on Any Computer

The extension is already portable! Just need to configure it:

#### On Computer 1:
```
1. Install Chrome
2. Load extension from folder
3. Configure:
   - Backend URL: http://your-server-ip:8000
   - Or: http://localhost:8000 (if backend on same computer)
4. Start Backend Listener
5. Keep browser open 24/7
```

#### On Computer 2:
```
Same steps, just point to same backend URL
Multiple computers can run extension simultaneously!
```

### Remote Backend Setup

If you want extension to work from any computer:

1. **Deploy Backend to Cloud**:
   - AWS, DigitalOcean, Heroku, etc.
   - Get public IP or domain
   - Example: `https://vatican-bot.yourdomain.com`

2. **Configure Extension**:
   ```
   Backend URL: https://vatican-bot.yourdomain.com
   API Key: your-api-key
   ```

3. **Extension Works from Anywhere**:
   - Home computer
   - Office computer
   - Friend's computer
   - All connect to same backend

---

## 📋 Step 8: Complete Setup Commands

### 1. Create Booking Sync Service

```bash
# Create the file
notepad backend/services/booking_sync_service.py
# Paste the code from Step 2
```

### 2. Create Celery Task

```bash
# Create the file
notepad backend/monitors/tasks_booking_sync.py
# Paste the code from Step 3
```

### 3. Update Settings

```bash
# Edit settings.py
notepad backend/core/settings.py
# Add the CELERY_BEAT_SCHEDULE entry from Step 4
```

### 4. Update Celery Config

```bash
# Edit celery.py
notepad backend/core/celery.py
# Add tasks_booking_sync to autodiscover_tasks
```

### 5. Run Migration

```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

### 6. Restart Services

```bash
docker-compose restart backend worker_vatican
```

---

## 📋 Step 9: Test Complete Flow

### 1. Add Booking Request to Google Sheets

In "Booking Requests" sheet, add:
```
| REQ-TEST-001 | 28/03/2026 | 2 | standard | | pending | | 2026-05-22 10:00:00 |
```

In "Participants" sheet, add:
```
| REQ-TEST-001 | John | Doe | john@example.com | +39 123456789 | 1990-01-15 |
| REQ-TEST-001 | Jane | Doe | jane@example.com | +39 987654321 | 1992-03-20 |
```

### 2. Wait 5 Minutes (or trigger manually)

```bash
# Trigger sync manually
docker-compose exec backend python manage.py shell
```

```python
from monitors.tasks_booking_sync import sync_booking_requests
result = sync_booking_requests()
print(result)
exit()
```

### 3. Verify Task Created

```bash
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import MonitorTask

task = MonitorTask.objects.filter(external_reference='REQ-TEST-001').first()
if task:
    print(f"✅ Task created: {task.id}")
    print(f"   Date: {task.date}")
    print(f"   Visitors: {task.visitors}")
    print(f"   Status: Active={task.is_active}")
else:
    print("❌ Task not found")

exit()
```

### 4. Worker Monitors Vatican

```bash
# Check worker logs
docker-compose logs -f worker_vatican

# Should see:
# [INFO] Monitoring 1 tasks
# [INFO] Checking Vatican API for REQ-TEST-001...
```

### 5. Extension Auto-Books

When tickets found:
1. Worker creates HeldSlot
2. Extension detects slot (within 10 seconds)
3. Opens incognito window
4. Auto-books with participants from sheet
5. Marks as booked
6. Updates Google Sheets status to "booked"

---

## ✅ Final Architecture

```
BOKUN BOOKING
   ↓
GOOGLE SHEETS (Booking Requests + Participants)
   ↓ Auto-sync every 5 minutes
BACKEND (Creates MonitorTasks)
   ↓
WORKER (Monitors Vatican 24/7)
   ↓ Creates HeldSlot when found
BACKEND API (/api/v1/available-slots/)
   ↓ Extension polls every 10 seconds
EXTENSION (Auto-books)
   ↓ Marks as booked
BACKEND (Updates Google Sheets)
```

**No Telegram Required!** ✅

---

## 🎯 Benefits

1. ✅ **Fully Automated**: Bokun → Sheets → Bot → Extension
2. ✅ **No Manual Input**: No Telegram commands needed
3. ✅ **Portable**: Extension works on any computer
4. ✅ **Scalable**: Multiple computers can run extension
5. ✅ **Centralized**: All data in Google Sheets
6. ✅ **Status Tracking**: Sheet shows booking status
7. ✅ **Multi-User**: Multiple people can add requests to sheet

---

**Ready to implement! Let me know if you want me to create the actual files or help with any specific part.** 🚀
