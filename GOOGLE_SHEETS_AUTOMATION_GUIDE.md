# Google Sheets Automation Guide

**Goal:** Automatically import participant names from Google Sheets and use them for booking

---

## 📊 PART 1: Google Sheets Setup

### Step 1: Create Your Google Sheet

**Sheet Structure:**
```
| First Name | Last Name | Email              | Phone       | Birth Date | Gender | Notes        |
|------------|-----------|-----------------------|-------------|------------|--------|--------------|
| Mario      | Rossi     | mario@example.com     | 3401234567  | 15/01/1990 | M      | Adult        |
| Luigi      | Verdi     | luigi@example.com     | 3407654321  | 20/05/1985 | M      | Adult        |
| Anna       | Bianchi   | anna@example.com      | 3409876543  | 10/03/1992 | F      | Adult        |
| Sofia      | Neri      | sofia@example.com     | 3402345678  | 25/08/2010 | F      | Child        |
```

**Sheet Name:** `Vatican_Participants`

**Google Sheet URL Example:**
```
https://docs.google.com/spreadsheets/d/1ABC123XYZ456/edit
```

---

### Step 2: Make Sheet Accessible

**Option A: Public (Simple but less secure)**
```
1. Click "Share" button
2. Click "Change to anyone with the link"
3. Set to "Viewer"
4. Copy the link
```

**Option B: Service Account (Recommended for production)**
```
1. Go to Google Cloud Console
2. Create a new project
3. Enable Google Sheets API
4. Create Service Account
5. Download JSON key file
6. Share sheet with service account email
```

---

## 🔧 PART 2: Backend Integration

### Step 1: Install Required Packages

Add to `requirements.txt`:
```txt
gspread==5.12.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
```

Install:
```bash
docker-compose exec backend pip install gspread google-auth
```

---

### Step 2: Create Google Sheets Service

Create `backend/services/google_sheets_service.py`:

```python
"""
Google Sheets Service
Imports participant names from Google Sheets
"""
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict
import os
import logging

logger = logging.getLogger(__name__)

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]


class GoogleSheetsService:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client"""
        try:
            # Option 1: Service Account (Recommended)
            service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', '/app/google_credentials.json')
            
            if os.path.exists(service_account_file):
                creds = Credentials.from_service_account_file(
                    service_account_file,
                    scopes=SCOPES
                )
                self.client = gspread.authorize(creds)
                logger.info("✅ Google Sheets client initialized with service account")
            else:
                logger.warning("⚠️ Google service account file not found")
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
    
    def get_participants_from_sheet(self, sheet_url: str, sheet_name: str = 'Vatican_Participants') -> List[Dict]:
        """
        Get participants from Google Sheet
        
        Args:
            sheet_url: Google Sheets URL or ID
            sheet_name: Name of the worksheet (default: Vatican_Participants)
        
        Returns:
            List of participant dictionaries
        """
        try:
            if not self.client:
                logger.error("Google Sheets client not initialized")
                return []
            
            # Extract sheet ID from URL if needed
            if 'docs.google.com' in sheet_url:
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Get all records (assumes first row is header)
            records = worksheet.get_all_records()
            
            # Convert to participant format
            participants = []
            for record in records:
                participant = {
                    'first_name': record.get('First Name', '').strip(),
                    'last_name': record.get('Last Name', '').strip(),
                    'email': record.get('Email', '').strip(),
                    'phone': record.get('Phone', '').strip(),
                    'birth_date': record.get('Birth Date', '').strip(),
                    'gender': record.get('Gender', 'M').strip().upper(),
                    'notes': record.get('Notes', '').strip()
                }
                
                # Only add if has name
                if participant['first_name'] and participant['last_name']:
                    participants.append(participant)
            
            logger.info(f"✅ Loaded {len(participants)} participants from Google Sheet")
            return participants
            
        except Exception as e:
            logger.error(f"Error reading Google Sheet: {e}")
            return []
    
    def get_participants_for_agency(self, agency_id: int) -> List[Dict]:
        """
        Get participants for a specific agency
        Looks up agency's Google Sheet URL from database
        """
        from monitors.models import Agency
        
        try:
            agency = Agency.objects.get(id=agency_id)
            
            # Check if agency has Google Sheet URL configured
            sheet_url = getattr(agency, 'google_sheet_url', None)
            
            if not sheet_url:
                logger.warning(f"Agency {agency.name} has no Google Sheet URL configured")
                return []
            
            return self.get_participants_from_sheet(sheet_url)
            
        except Agency.DoesNotExist:
            logger.error(f"Agency {agency_id} not found")
            return []
        except Exception as e:
            logger.error(f"Error getting participants for agency: {e}")
            return []


# Singleton instance
_sheets_service = None

def get_sheets_service() -> GoogleSheetsService:
    """Get or create Google Sheets service instance"""
    global _sheets_service
    if _sheets_service is None:
        _sheets_service = GoogleSheetsService()
    return _sheets_service
```

---

### Step 3: Add Google Sheet URL to Agency Model

Update `backend/monitors/models.py`:

```python
class Agency(models.Model):
    # ... existing fields ...
    
    # Add this field
    google_sheet_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Google Sheets URL for participant names"
    )
```

Create migration:
```bash
docker-compose exec backend sh -c "cd backend && python manage.py makemigrations"
docker-compose exec backend sh -c "cd backend && python manage.py migrate"
```

---

### Step 4: Create Management Command to Import Names

Create `backend/monitors/management/commands/import_participants.py`:

```python
"""
Import participants from Google Sheets
Usage: python manage.py import_participants --agency=WOR
"""
from django.core.management.base import BaseCommand
from monitors.models import Agency, BuyerProfile
from services.google_sheets_service import get_sheets_service
import json


class Command(BaseCommand):
    help = 'Import participants from Google Sheets'
    
    def add_arguments(self, parser):
        parser.add_argument('--agency', type=str, help='Agency name')
        parser.add_argument('--sheet-url', type=str, help='Google Sheet URL (optional)')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    
    def handle(self, *args, **options):
        agency_name = options.get('agency')
        sheet_url = options.get('sheet_url')
        dry_run = options.get('dry_run', False)
        
        if not agency_name:
            self.stdout.write(self.style.ERROR('❌ --agency is required'))
            return
        
        # Get agency
        try:
            agency = Agency.objects.get(name__iexact=agency_name)
        except Agency.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Agency "{agency_name}" not found'))
            return
        
        # Get Google Sheets service
        sheets_service = get_sheets_service()
        
        # Get sheet URL
        if not sheet_url:
            sheet_url = agency.google_sheet_url
        
        if not sheet_url:
            self.stdout.write(self.style.ERROR('❌ No Google Sheet URL provided'))
            self.stdout.write('Use: --sheet-url=<URL> or set agency.google_sheet_url')
            return
        
        # Import participants
        self.stdout.write(f'📊 Importing participants from Google Sheet...')
        participants = sheets_service.get_participants_from_sheet(sheet_url)
        
        if not participants:
            self.stdout.write(self.style.WARNING('⚠️ No participants found in sheet'))
            return
        
        self.stdout.write(f'✅ Found {len(participants)} participants:')
        
        for i, p in enumerate(participants, 1):
            self.stdout.write(f"  {i}. {p['first_name']} {p['last_name']} ({p.get('notes', 'N/A')})")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN - No changes made'))
            return
        
        # Update agency's Google Sheet URL if provided
        if sheet_url and sheet_url != agency.google_sheet_url:
            agency.google_sheet_url = sheet_url
            agency.save(update_fields=['google_sheet_url'])
            self.stdout.write(f'✅ Updated agency Google Sheet URL')
        
        # Store participants in agency's buyer profile
        try:
            profile = BuyerProfile.objects.get(agency=agency)
            profile.participants_json = json.dumps(participants)
            profile.save(update_fields=['participants_json'])
            self.stdout.write(self.style.SUCCESS(f'✅ Saved {len(participants)} participants to BuyerProfile'))
        except BuyerProfile.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ No BuyerProfile found for agency'))
            self.stdout.write('Create one via Telegram bot first')
```

---

### Step 5: Set Up Google Credentials

**Option A: Service Account (Recommended)**

1. Download service account JSON from Google Cloud Console
2. Save as `google_credentials.json` in project root
3. Add to `.gitignore`:
```bash
echo "google_credentials.json" >> .gitignore
```

4. Mount in `docker-compose.yml`:
```yaml
backend:
  volumes:
    - .:/app
    - ./google_credentials.json:/app/google_credentials.json:ro
  environment:
    - GOOGLE_SERVICE_ACCOUNT_FILE=/app/google_credentials.json
```

**Option B: Public Sheet (Quick Test)**

Just use the sheet URL directly - no credentials needed if sheet is public.

---

## 🚀 PART 3: Usage

### Import Participants from Google Sheets

```bash
# Preview (dry run)
docker-compose exec backend python /app/backend/manage.py import_participants \
  --agency=WOR \
  --sheet-url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit" \
  --dry-run

# Actually import
docker-compose exec backend python /app/backend/manage.py import_participants \
  --agency=WOR \
  --sheet-url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

**Output:**
```
📊 Importing participants from Google Sheet...
✅ Found 4 participants:
  1. Mario Rossi (Adult)
  2. Luigi Verdi (Adult)
  3. Anna Bianchi (Adult)
  4. Sofia Neri (Child)
✅ Updated agency Google Sheet URL
✅ Saved 4 participants to BuyerProfile
```

---

### Verify Import

```bash
# Check database
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT id, first_name, last_name, participants_json IS NOT NULL as has_participants 
   FROM buyer_profiles WHERE agency_id = 14;"
```

---

## 🌐 PART 4: Extension Integration

### Step 1: Create Backend API Endpoint

Create `backend/monitors/views.py` (or add to existing):

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from monitors.models import HeldSlot, BuyerProfile
import json


@csrf_exempt
@require_http_methods(["GET"])
def get_available_slots(request):
    """
    API endpoint for browser extension to poll for available slots
    Returns held slots that are ready for booking
    """
    try:
        # Get agency from API key (optional authentication)
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # Get all held slots that are not yet booked
        held_slots = HeldSlot.objects.filter(
            status='held',
            payment_ready=False
        ).select_related('task', 'task__agency').order_by('-hold_started_at')[:20]
        
        slots_data = []
        
        for slot in held_slots:
            # Get buyer profile with participants
            try:
                profile = BuyerProfile.objects.get(agency=slot.task.agency)
                
                # Parse participants JSON
                participants = []
                if profile.participants_json:
                    participants = json.loads(profile.participants_json)
                
                # Build profile data
                profile_data = {
                    'firstName': profile.first_name,
                    'lastName': profile.last_name,
                    'email': profile.email,
                    'phone': profile.phone,
                    'city': profile.city,
                    'country': profile.country,
                    'birthDate': {
                        'year': '1990',
                        'month': 'GEN',
                        'day': '15'
                    } if profile.birth_date else None,
                    'gender': profile.gender
                }
                
                # Build card data if available
                card_data = None
                if profile.card_number:
                    card_data = {
                        'number': profile.card_number,
                        'expiry': profile.card_expiry,
                        'cvv': profile.card_cvv,
                        'holder': profile.card_holder
                    }
                
            except BuyerProfile.DoesNotExist:
                profile_data = None
                participants = []
                card_data = None
            
            # Add slot to response
            slots_data.append({
                'id': slot.id,
                'date': slot.date,
                'time': slot.slot_time,
                'ticket_id': slot.ticket_id,
                'ticket_name': slot.ticket_name,
                'visitors': slot.visitors,
                'adult_count': slot.adult_count,
                'child_count': slot.child_count,
                'language': slot.task.language if hasattr(slot.task, 'language') else None,
                'profile': profile_data,
                'participants': participants,
                'card': card_data,
                'jsessionid': slot.jsessionid,
                'recap_id': slot.recap_id
            })
        
        return JsonResponse({
            'success': True,
            'count': len(slots_data),
            'slots': slots_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mark_slot_booked(request, slot_id):
    """
    Mark a slot as booked after extension completes booking
    """
    try:
        slot = HeldSlot.objects.get(id=slot_id)
        slot.payment_ready = True
        slot.status = 'paying'
        slot.save(update_fields=['payment_ready', 'status'])
        
        return JsonResponse({
            'success': True,
            'message': f'Slot {slot_id} marked as booked'
        })
        
    except HeldSlot.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Slot not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
```

---

### Step 2: Add URL Routes

Update `backend/core/urls.py`:

```python
from django.urls import path
from monitors import views

urlpatterns = [
    # ... existing patterns ...
    
    # Extension API endpoints
    path('api/v1/available-slots/', views.get_available_slots, name='available_slots'),
    path('api/v1/slots/<int:slot_id>/mark-booked/', views.mark_slot_booked, name='mark_slot_booked'),
]
```

Restart backend:
```bash
docker-compose restart backend
```

---

### Step 3: Test API Endpoint

```bash
# Test from command line
curl http://localhost:8000/api/v1/available-slots/

# Should return:
{
  "success": true,
  "count": 0,
  "slots": []
}
```

---

## 🎯 PART 5: Complete Workflow

### Automated Flow:

```
1. GOOGLE SHEETS
   ↓
   Contains participant names
   
2. IMPORT COMMAND
   ↓
   docker-compose exec backend python manage.py import_participants --agency=WOR
   
3. DATABASE
   ↓
   Participants stored in BuyerProfile.participants_json
   
4. TELEGRAM BOT
   ↓
   User creates monitor task
   
5. WORKER
   ↓
   Finds available slot → Creates HeldSlot
   
6. EXTENSION
   ↓
   Polls /api/v1/available-slots/ every 10 seconds
   
7. EXTENSION DETECTS SLOT
   ↓
   Opens incognito window
   
8. CONTENT SCRIPT
   ↓
   Auto-fills form with participants from API
   
9. BOOKING COMPLETED
   ↓
   Extension calls /api/v1/slots/{id}/mark-booked/
   
10. USER GETS CONFIRMATION EMAIL
```

---

## 📋 Quick Start Checklist

- [ ] Create Google Sheet with participant names
- [ ] Make sheet public OR set up service account
- [ ] Add `google_sheet_url` field to Agency model
- [ ] Create `google_sheets_service.py`
- [ ] Create `import_participants` management command
- [ ] Run import command
- [ ] Create API endpoints (`get_available_slots`, `mark_slot_booked`)
- [ ] Add URL routes
- [ ] Restart backend
- [ ] Test API endpoint
- [ ] Configure extension to use Backend Listener mode
- [ ] Test complete flow

---

## 🔧 Maintenance

### Update Participants

```bash
# Re-run import anytime sheet changes
docker-compose exec backend python /app/backend/manage.py import_participants --agency=WOR
```

### Auto-Sync (Optional)

Add to `backend/monitors/tasks.py`:

```python
@shared_task
def sync_participants_from_sheets():
    """Sync participants from Google Sheets every hour"""
    from services.google_sheets_service import get_sheets_service
    from monitors.models import Agency, BuyerProfile
    import json
    
    sheets_service = get_sheets_service()
    
    # Get all agencies with Google Sheet URLs
    agencies = Agency.objects.filter(
        google_sheet_url__isnull=False
    ).exclude(google_sheet_url='')
    
    for agency in agencies:
        try:
            participants = sheets_service.get_participants_from_sheet(agency.google_sheet_url)
            
            if participants:
                profile = BuyerProfile.objects.get(agency=agency)
                profile.participants_json = json.dumps(participants)
                profile.save(update_fields=['participants_json'])
                
                logger.info(f"✅ Synced {len(participants)} participants for {agency.name}")
        except Exception as e:
            logger.error(f"Failed to sync participants for {agency.name}: {e}")
```

Schedule in Celery Beat (add to `backend/core/celery.py`):

```python
app.conf.beat_schedule = {
    # ... existing schedules ...
    
    'sync-participants-hourly': {
        'task': 'monitors.tasks.sync_participants_from_sheets',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

---

**Now you have a complete automated system from Google Sheets to automatic booking!** 🎉

