# Production Setup Guide - Real Vatican Bookings

## 🎯 Complete Production Workflow

### System Architecture:
```
Bokun → Google Sheets → Backend (Hetzner) → Worker → Finds Slots
                                                ↓
                                         Telegram Bot → Sends Payment Link
                                                ↓
                                         Extension (Local) → Books Ticket
                                                ↓
                                         Updates Google Sheets → Mark as Booked
```

---

## Part 1: Create Real Monitoring Tasks

### Step 1: Remove Test Data

```bash
# Connect to backend
docker-compose exec backend python /app/backend/manage.py shell

# Remove test slots
>>> from monitors.models import HeldSlot, MonitorTask
>>> HeldSlot.objects.filter(slot_id__startswith='TEST').delete()
>>> MonitorTask.objects.filter(ticket_name__icontains='TEST').delete()
>>> exit()
```

### Step 2: Create Real Monitoring Task

Create a script to add real tasks:

```python
# create_real_task.py
import os
import sys
import django

sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import Agency, MonitorTask
from datetime import datetime, timedelta

def create_real_task():
    """Create a real monitoring task for Vatican"""
    
    # Get your agency
    agency = Agency.objects.get(id=15)  # Your test agency
    
    # Create task for real future dates
    # Example: Monitor June 15-20, 2026
    dates = []
    start_date = datetime(2026, 6, 15)
    for i in range(6):  # 6 days
        date = start_date + timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
    
    task = MonitorTask.objects.create(
        agency=agency,
        site='vatican',
        area_name='Vatican Museums',
        dates=dates,
        preferred_times=['09:00', '10:00', '11:00', '14:00', '15:00'],
        visitors=2,
        adult_count=2,
        child_count=0,
        ticket_type=0,  # 0 = Standard ticket, 1 = Guided tour
        ticket_name='Vatican Museums - Standard Entry',
        ticket_id=None,  # Will be resolved dynamically
        language=None,  # None for standard tickets
        check_interval=300,  # Check every 5 minutes
        tier='snipe',
        match_strategy='any',
        notification_mode='available_only',
        is_active=True
    )
    
    print(f"✅ Created real monitoring task (ID: {task.id})")
    print(f"   Dates: {', '.join(dates)}")
    print(f"   Times: {', '.join(task.preferred_times)}")
    print(f"   Visitors: {task.visitors}")
    print(f"   Check interval: {task.check_interval} seconds")
    
    return task

if __name__ == '__main__':
    create_real_task()
```

Run it:
```bash
docker cp create_real_task.py vatican-bot-backend-1:/app/
docker-compose exec backend python /app/create_real_task.py
```

### Step 3: Start Worker to Monitor

```bash
# Check worker is running
docker-compose ps worker_vatican

# Watch worker logs
docker-compose logs -f worker_vatican

# You should see:
# "Checking Vatican availability for task ID: X"
# "Calling Search API for fresh ticket IDs"
# "Found X tickets for 2026-06-15"
```

---

## Part 2: Google Sheets Integration

### Architecture:
```
Bokun → Google Sheets (Input) → Backend reads → Creates tasks
                                                      ↓
                                                 Finds slots
                                                      ↓
                                                 Books tickets
                                                      ↓
Google Sheets (Output) ← Backend updates ← Booking complete
```

### Step 1: Setup Google Sheets API

#### 1.1 Create Service Account
```
1. Go to: https://console.cloud.google.com/
2. Create project: "Vatican Bot"
3. Enable APIs:
   - Google Sheets API
   - Google Drive API
4. Create Service Account:
   - Name: vatican-bot-service
   - Role: Editor
5. Create Key:
   - Type: JSON
   - Download: google_credentials.json
```

#### 1.2 Copy Credentials to Server
```bash
# Local development
docker cp google_credentials.json vatican-bot-backend-1:/app/google_credentials.json

# Hetzner server (later)
scp google_credentials.json root@YOUR_SERVER_IP:/root/vatican-bot/google_credentials.json
```

### Step 2: Create Google Sheets Structure

#### Sheet 1: "Bookings_Input" (Bokun writes here)
```
| Booking ID | Date       | Time  | Visitors | First Name | Last Name | Email              | Phone         | Status    |
|------------|------------|-------|----------|------------|-----------|-------------------|---------------|-----------|
| BK001      | 15/06/2026 | 09:00 | 2        | John       | Doe       | john@example.com  | 393331234567  | Pending   |
| BK002      | 16/06/2026 | 10:00 | 2        | Jane       | Smith     | jane@example.com  | 393331234568  | Pending   |
```

#### Sheet 2: "Bookings_Output" (Bot updates here)
```
| Booking ID | Date       | Time  | Status      | Payment Link                          | Booked At           | Marked |
|------------|------------|-------|-------------|---------------------------------------|---------------------|--------|
| BK001      | 15/06/2026 | 09:00 | Available   | https://epay.museivaticani.va/...     | 2026-06-01 10:30    |        |
| BK002      | 16/06/2026 | 10:00 | Booked      | https://epay.museivaticani.va/...     | 2026-06-01 10:35    | ✓      |
```

**Marked Column:**
- Empty = Not yet booked
- ✓ = Booked and paid
- Color: Green background = Completed

#### Sheet 3: "Participants" (For multi-visitor bookings)
```
| Booking ID | Participant # | First Name | Last Name | Birth Date | Gender |
|------------|---------------|------------|-----------|------------|--------|
| BK001      | 1             | John       | Doe       | 1990-01-01 | M      |
| BK001      | 2             | Jane       | Doe       | 1992-05-15 | F      |
```

### Step 3: Share Sheet with Service Account
```
1. Open your Google Sheet
2. Click "Share"
3. Add service account email (from JSON file):
   vatican-bot-service@vatican-bot-123456.iam.gserviceaccount.com
4. Give "Editor" access
5. Copy sheet URL
```

### Step 4: Configure Agency with Sheet URL
```bash
docker-compose exec backend python /app/backend/manage.py shell

>>> from monitors.models import Agency
>>> agency = Agency.objects.get(id=15)
>>> agency.google_sheet_url = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
>>> agency.save()
>>> exit()
```

---

## Part 3: Google Sheets Service Enhancement

Let me create an enhanced Google Sheets service that can:
1. Read bookings from input sheet
2. Write results to output sheet
3. Update booking status
4. Mark completed bookings

### Enhanced Service Code:

```python
# backend/services/google_sheets_service.py (enhanced)

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class GoogleSheetsService:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client"""
        try:
            service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', '/app/google_credentials.json')
            
            if os.path.exists(service_account_file):
                creds = Credentials.from_service_account_file(
                    service_account_file,
                    scopes=SCOPES
                )
                self.client = gspread.authorize(creds)
                logger.info("✅ Google Sheets client initialized")
            else:
                logger.warning("⚠️ Google service account file not found")
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
    
    def read_bookings_input(self, sheet_url: str) -> List[Dict]:
        """
        Read pending bookings from input sheet
        Returns list of booking dictionaries
        """
        try:
            if not self.client:
                return []
            
            sheet_id = self._extract_sheet_id(sheet_url)
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet('Bookings_Input')
            
            records = worksheet.get_all_records()
            
            # Filter only pending bookings
            bookings = []
            for record in records:
                if record.get('Status', '').lower() == 'pending':
                    bookings.append({
                        'booking_id': record.get('Booking ID', ''),
                        'date': record.get('Date', ''),
                        'time': record.get('Time', ''),
                        'visitors': int(record.get('Visitors', 1)),
                        'first_name': record.get('First Name', ''),
                        'last_name': record.get('Last Name', ''),
                        'email': record.get('Email', ''),
                        'phone': record.get('Phone', ''),
                    })
            
            logger.info(f"✅ Read {len(bookings)} pending bookings from sheet")
            return bookings
            
        except Exception as e:
            logger.error(f"Error reading bookings input: {e}")
            return []
    
    def write_booking_result(self, sheet_url: str, booking_id: str, 
                            status: str, payment_link: str = None):
        """
        Write booking result to output sheet
        """
        try:
            if not self.client:
                return False
            
            sheet_id = self._extract_sheet_id(sheet_url)
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet('Bookings_Output')
            
            # Find row with booking_id
            cell = worksheet.find(booking_id)
            if cell:
                row = cell.row
            else:
                # Add new row
                row = len(worksheet.get_all_values()) + 1
                worksheet.update_cell(row, 1, booking_id)
            
            # Update columns
            worksheet.update_cell(row, 4, status)  # Status column
            if payment_link:
                worksheet.update_cell(row, 5, payment_link)  # Payment Link column
            worksheet.update_cell(row, 6, datetime.now().strftime('%Y-%m-%d %H:%M'))  # Booked At
            
            logger.info(f"✅ Updated booking {booking_id} in output sheet")
            return True
            
        except Exception as e:
            logger.error(f"Error writing booking result: {e}")
            return False
    
    def mark_booking_completed(self, sheet_url: str, booking_id: str):
        """
        Mark booking as completed (add checkmark and green background)
        """
        try:
            if not self.client:
                return False
            
            sheet_id = self._extract_sheet_id(sheet_url)
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet('Bookings_Output')
            
            # Find row
            cell = worksheet.find(booking_id)
            if not cell:
                return False
            
            row = cell.row
            
            # Add checkmark
            worksheet.update_cell(row, 7, '✓')  # Marked column
            
            # Add green background
            worksheet.format(f'A{row}:G{row}', {
                'backgroundColor': {
                    'red': 0.7,
                    'green': 0.9,
                    'blue': 0.7
                }
            })
            
            logger.info(f"✅ Marked booking {booking_id} as completed")
            return True
            
        except Exception as e:
            logger.error(f"Error marking booking completed: {e}")
            return False
    
    def check_if_booked(self, sheet_url: str, booking_id: str) -> bool:
        """
        Check if booking is marked as completed in sheet
        """
        try:
            if not self.client:
                return False
            
            sheet_id = self._extract_sheet_id(sheet_url)
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet('Bookings_Output')
            
            # Find row
            cell = worksheet.find(booking_id)
            if not cell:
                return False
            
            row = cell.row
            marked = worksheet.cell(row, 7).value  # Marked column
            
            return marked == '✓'
            
        except Exception as e:
            logger.error(f"Error checking booking status: {e}")
            return False
    
    def _extract_sheet_id(self, sheet_url: str) -> str:
        """Extract sheet ID from URL"""
        if 'docs.google.com' in sheet_url:
            return sheet_url.split('/d/')[1].split('/')[0]
        return sheet_url


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

## Part 4: Telegram Integration

### Current Flow:
```
Worker finds slot → Creates HeldSlot → Telegram bot sends notification
```

### Enhanced Notification:

Update Telegram notification to include payment link:

```python
# In worker or notification service
def send_booking_notification(booking_id, date, time, payment_link):
    """Send Telegram notification with payment link"""
    message = f"""
🎫 **Vatican Ticket Available!**

📅 Date: {date}
⏰ Time: {time}
🆔 Booking ID: {booking_id}

💳 **Payment Link:**
{payment_link}

⚠️ **Action Required:**
1. Click the link above
2. Complete payment within 15 minutes
3. Mark as completed in Google Sheets

Status: Waiting for payment...
    """
    
    # Send to Telegram
    send_telegram_message(chat_id, message)
```

---

## Part 5: Hetzner Server Deployment

### Server Setup:

#### 1. Create Hetzner Server
```
1. Go to: https://www.hetzner.com/cloud
2. Create server:
   - Type: CX21 (2 vCPU, 4GB RAM) - €5.83/month
   - Location: Nuremberg, Germany
   - Image: Ubuntu 22.04
   - SSH Key: Add your key
3. Note IP address
```

#### 2. Initial Server Setup
```bash
# Connect to server
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create app directory
mkdir -p /root/vatican-bot
cd /root/vatican-bot
```

#### 3. Copy Project to Server
```bash
# From your local machine
scp -r . root@YOUR_SERVER_IP:/root/vatican-bot/

# Or use git
ssh root@YOUR_SERVER_IP
cd /root/vatican-bot
git clone YOUR_REPO_URL .
```

#### 4. Configure Environment
```bash
# On server
cd /root/vatican-bot

# Copy environment file
cp .env.example .env

# Edit environment
nano .env

# Set:
# - Database credentials
# - Redis URL
# - Telegram bot token
# - Google credentials path
```

#### 5. Start Services
```bash
# Build and start
docker-compose up -d

# Check status
docker-compose ps

# Check logs
docker-compose logs -f
```

#### 6. Configure Firewall
```bash
# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp  # Backend API

# Enable firewall
ufw enable
```

#### 7. Setup Domain (Optional)
```
1. Point domain to server IP
2. Install Certbot for SSL:
   apt install certbot python3-certbot-nginx
3. Get certificate:
   certbot --nginx -d yourdomain.com
```

---

## Part 6: Complete Workflow

### Automated Flow:

```
1. Bokun creates booking → Writes to Google Sheets (Bookings_Input)
                                    ↓
2. Backend reads sheet every 5 minutes → Creates MonitorTask
                                    ↓
3. Worker monitors Vatican → Finds available slot
                                    ↓
4. Worker creates HeldSlot → Writes to Google Sheets (Bookings_Output)
                                    ↓
5. Telegram bot sends notification → "Payment link: https://..."
                                    ↓
6. Extension (on local computer) → Polls backend API
                                    ↓
7. Extension detects slot → Opens incognito window
                                    ↓
8. Extension fills form → Stops at checkout
                                    ↓
9. You click ACQUISTA → Redirects to payment
                                    ↓
10. Payment completed → Update Google Sheets (Mark as ✓)
                                    ↓
11. Telegram bot sends confirmation → "Booking BK001 completed!"
```

### Manual Verification:
```
1. Check Google Sheets "Bookings_Output"
2. Look for green rows with ✓ mark
3. Verify payment link works
4. Confirm booking in Vatican system
```

---

## Part 7: Alternatives to Google Sheets

### Option 1: Airtable
**Pros:**
- Better API
- Built-in automations
- Easier to use
- Better UI

**Cons:**
- Paid plans for API access
- More expensive than Sheets

### Option 2: Notion
**Pros:**
- Modern interface
- Good API
- Free for personal use

**Cons:**
- API rate limits
- Slower than Sheets

### Option 3: PostgreSQL Direct
**Pros:**
- Fastest
- Most reliable
- No external dependencies

**Cons:**
- Bokun needs database access
- Less user-friendly

### Option 4: REST API
**Pros:**
- Most flexible
- Bokun can POST directly
- Real-time updates

**Cons:**
- Need to build API
- More complex

### Recommendation:
**Use Google Sheets** for now because:
- ✅ Free
- ✅ Bokun can write to it easily
- ✅ You can view/edit manually
- ✅ Good API with Python library
- ✅ Can add colors/formatting
- ✅ Easy to share with team

---

## Next Steps

1. **Create real monitoring task** (Part 1)
2. **Setup Google Sheets** (Part 2)
3. **Test locally** with real Vatican dates
4. **Deploy to Hetzner** (Part 5)
5. **Configure Telegram** (Part 4)
6. **Test complete workflow** (Part 6)

---

**Ready to start?** Let me know which part you want to implement first!
