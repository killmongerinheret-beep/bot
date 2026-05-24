# Bokun API Integration Guide

## 📋 Overview

This guide explains how to integrate the Bokun API with your Vatican ticket booking system to enhance participant data management and booking coordination.

---

## 🎯 What is Bokun?

**Bokun** is a booking and reservation management platform commonly used by tour operators and travel agencies. It provides:

- Booking management
- Customer data storage
- Payment processing
- Inventory management
- API access for integration

---

## 🔄 Integration Architecture

### Current System (Without Bokun)

```
TELEGRAM BOT → BACKEND → GOOGLE SHEETS → EXTENSION
```

### Enhanced System (With Bokun)

```
TELEGRAM BOT → BACKEND → BOKUN API + GOOGLE SHEETS → EXTENSION
                  ↓
            Participant Data
            Booking Status
            Payment Info
```

---

## 🔌 Bokun API Integration Points

### 1. **Participant Data Source**

**Use Case**: Fetch participant information from Bokun bookings

**Flow**:
```
BOKUN API
  ↓ GET /bookings
  ↓ Returns booking data with participants
BACKEND
  ↓ Parse participant data
  ↓ Store in BuyerProfile
  ↓ Merge with Google Sheets data
EXTENSION
  ↓ Use combined data for auto-booking
```

**Implementation**:
```python
# backend/services/bokun_service.py

import requests
from django.conf import settings

class BokunService:
    def __init__(self):
        self.api_key = settings.BOKUN_API_KEY
        self.api_url = settings.BOKUN_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_bookings(self, date=None, status='CONFIRMED'):
        """Fetch bookings from Bokun"""
        params = {'status': status}
        if date:
            params['date'] = date
        
        response = requests.get(
            f'{self.api_url}/bookings',
            headers=self.headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Bokun API error: {response.status_code}')
    
    def get_booking_participants(self, booking_id):
        """Get participants for a specific booking"""
        response = requests.get(
            f'{self.api_url}/bookings/{booking_id}/participants',
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Bokun API error: {response.status_code}')
    
    def parse_participants(self, bokun_data):
        """Parse Bokun participant data to our format"""
        participants = []
        
        for participant in bokun_data.get('participants', []):
            participants.append({
                'first_name': participant.get('firstName'),
                'last_name': participant.get('lastName'),
                'email': participant.get('email'),
                'phone': participant.get('phone'),
                'birth_date': participant.get('dateOfBirth'),
                'nationality': participant.get('nationality'),
                'passport_number': participant.get('passportNumber')
            })
        
        return participants
```

### 2. **Booking Status Sync**

**Use Case**: Update Bokun when Vatican tickets are booked

**Flow**:
```
EXTENSION
  ↓ Completes Vatican booking
  ↓ POST /api/v1/slots/{id}/mark-booked/
BACKEND
  ↓ Update HeldSlot status
  ↓ Call Bokun API to update booking
BOKUN API
  ↓ PATCH /bookings/{id}
  ↓ Update booking status
  ↓ Add Vatican ticket reference
```

**Implementation**:
```python
# backend/services/bokun_service.py

def update_booking_status(self, booking_id, status, reference=None):
    """Update booking status in Bokun"""
    data = {
        'status': status,
        'externalReference': reference
    }
    
    response = requests.patch(
        f'{self.api_url}/bookings/{booking_id}',
        headers=self.headers,
        json=data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Bokun API error: {response.status_code}')

def add_ticket_to_booking(self, booking_id, ticket_data):
    """Add Vatican ticket details to Bokun booking"""
    data = {
        'tickets': [{
            'type': 'VATICAN_MUSEUMS',
            'date': ticket_data['date'],
            'time': ticket_data['time'],
            'quantity': ticket_data['visitors'],
            'reference': ticket_data['reference'],
            'price': ticket_data['price']
        }]
    }
    
    response = requests.post(
        f'{self.api_url}/bookings/{booking_id}/tickets',
        headers=self.headers,
        json=data
    )
    
    return response.json()
```

### 3. **Payment Tracking**

**Use Case**: Track payment status between Bokun and Vatican

**Flow**:
```
BOKUN BOOKING
  ↓ Payment received
  ↓ Webhook notification
BACKEND
  ↓ Create MonitorTask
  ↓ Link to Bokun booking_id
WORKER
  ↓ Find Vatican tickets
EXTENSION
  ↓ Complete booking
BACKEND
  ↓ Update Bokun payment status
```

**Implementation**:
```python
# backend/services/bokun_service.py

def get_payment_status(self, booking_id):
    """Get payment status from Bokun"""
    response = requests.get(
        f'{self.api_url}/bookings/{booking_id}/payment',
        headers=self.headers
    )
    
    if response.status_code == 200:
        payment = response.json()
        return {
            'status': payment.get('status'),
            'amount': payment.get('amount'),
            'currency': payment.get('currency'),
            'method': payment.get('method')
        }
    else:
        return None

def update_payment_status(self, booking_id, status, reference=None):
    """Update payment status in Bokun"""
    data = {
        'status': status,
        'externalReference': reference
    }
    
    response = requests.patch(
        f'{self.api_url}/bookings/{booking_id}/payment',
        headers=self.headers,
        json=data
    )
    
    return response.json()
```

---

## 🔧 Configuration

### Step 1: Get Bokun API Credentials

1. **Login to Bokun Dashboard**
2. **Go to Settings → API**
3. **Create API Key**
4. **Copy API Key and API URL**

### Step 2: Add to Environment Variables

Edit `.env` file:

```env
# Bokun API Configuration
BOKUN_API_KEY=your-bokun-api-key-here
BOKUN_API_URL=https://api.bokun.io
BOKUN_WEBHOOK_SECRET=your-webhook-secret
```

### Step 3: Configure Django Settings

Edit `backend/core/settings.py`:

```python
# Bokun Configuration
BOKUN_API_KEY = os.getenv('BOKUN_API_KEY')
BOKUN_API_URL = os.getenv('BOKUN_API_URL', 'https://api.bokun.io')
BOKUN_WEBHOOK_SECRET = os.getenv('BOKUN_WEBHOOK_SECRET')
```

### Step 4: Create Bokun Service

Create `backend/services/bokun_service.py` (see implementation above)

### Step 5: Add Bokun Fields to Models

Edit `backend/monitors/models.py`:

```python
class MonitorTask(models.Model):
    # ... existing fields ...
    
    # Bokun integration
    bokun_booking_id = models.CharField(max_length=100, null=True, blank=True)
    bokun_booking_reference = models.CharField(max_length=100, null=True, blank=True)
    bokun_sync_enabled = models.BooleanField(default=False)
    
    def sync_with_bokun(self):
        """Sync task data with Bokun booking"""
        if not self.bokun_booking_id or not self.bokun_sync_enabled:
            return
        
        from services.bokun_service import BokunService
        bokun = BokunService()
        
        # Get participants from Bokun
        participants = bokun.get_booking_participants(self.bokun_booking_id)
        
        # Update task with Bokun data
        self.participants_json = json.dumps(participants)
        self.save()
```

---

## 🔄 Integration Workflows

### Workflow 1: Bokun → Vatican (Booking Creation)

**Scenario**: Customer books tour in Bokun, needs Vatican tickets

**Steps**:

1. **Customer Books Tour in Bokun**
   ```
   Bokun Booking Created
   - Booking ID: BOK-2026-001
   - Date: 28/03/2026
   - Participants: 2
   - Status: CONFIRMED
   ```

2. **Bokun Webhook Triggers Backend**
   ```python
   # backend/monitors/views.py
   
   @api_view(['POST'])
   def bokun_webhook(request):
       """Handle Bokun webhook notifications"""
       # Verify webhook signature
       signature = request.headers.get('X-Bokun-Signature')
       if not verify_bokun_signature(signature, request.body):
           return Response({'error': 'Invalid signature'}, status=401)
       
       # Parse webhook data
       event = request.data.get('event')
       booking = request.data.get('booking')
       
       if event == 'booking.confirmed':
           # Create monitoring task
           task = MonitorTask.objects.create(
               agency_id=1,
               date=booking['date'],
               visitors=booking['participants_count'],
               ticket_type=0,
               bokun_booking_id=booking['id'],
               bokun_booking_reference=booking['reference'],
               bokun_sync_enabled=True,
               is_active=True
           )
           
           # Fetch participants from Bokun
           bokun = BokunService()
           participants = bokun.get_booking_participants(booking['id'])
           task.participants_json = json.dumps(participants)
           task.save()
           
           return Response({'success': True, 'task_id': task.id})
       
       return Response({'success': True})
   ```

3. **Worker Monitors Vatican**
   ```
   Worker checks Vatican API every 5 seconds
   Finds available slot
   Creates HeldSlot
   ```

4. **Extension Books Ticket**
   ```
   Extension detects slot
   Opens incognito window
   Auto-fills with Bokun participants
   Completes booking
   ```

5. **Backend Updates Bokun**
   ```python
   # backend/monitors/views.py
   
   @api_view(['POST'])
   def mark_slot_booked(request, slot_id):
       slot = HeldSlot.objects.get(id=slot_id)
       task = slot.task
       
       # Update slot status
       slot.status = 'paid'
       slot.save()
       
       # Update Bokun if linked
       if task.bokun_booking_id and task.bokun_sync_enabled:
           bokun = BokunService()
           bokun.add_ticket_to_booking(
               task.bokun_booking_id,
               {
                   'date': slot.date,
                   'time': slot.slot_time,
                   'visitors': slot.visitors,
                   'reference': f'VAT-{slot.id}',
                   'price': slot.total_price
               }
           )
           
           bokun.update_booking_status(
               task.bokun_booking_id,
               'COMPLETED',
               reference=f'VAT-{slot.id}'
           )
       
       return Response({'success': True})
   ```

### Workflow 2: Vatican → Bokun (Status Update)

**Scenario**: Vatican booking completed, update Bokun

**Steps**:

1. **Extension Completes Booking**
2. **Backend Receives Notification**
3. **Backend Updates Bokun**
4. **Bokun Sends Confirmation Email**

### Workflow 3: Bokun + Google Sheets (Combined Data)

**Scenario**: Use both Bokun and Google Sheets for participant data

**Steps**:

1. **Fetch Bokun Participants**
   ```python
   bokun = BokunService()
   bokun_participants = bokun.get_booking_participants(booking_id)
   ```

2. **Fetch Google Sheets Participants**
   ```python
   from services.google_sheets_service import GoogleSheetsService
   sheets = GoogleSheetsService()
   sheets_participants = sheets.get_participants(agency_id)
   ```

3. **Merge Data**
   ```python
   # Prefer Bokun data, fallback to Sheets
   merged_participants = []
   
   for bokun_p in bokun_participants:
       # Find matching participant in Sheets
       sheets_p = next(
           (p for p in sheets_participants 
            if p['email'] == bokun_p['email']),
           None
       )
       
       # Merge data (Bokun takes priority)
       merged = {
           'first_name': bokun_p.get('first_name') or sheets_p.get('first_name'),
           'last_name': bokun_p.get('last_name') or sheets_p.get('last_name'),
           'email': bokun_p.get('email') or sheets_p.get('email'),
           'phone': bokun_p.get('phone') or sheets_p.get('phone'),
           'birth_date': bokun_p.get('birth_date') or sheets_p.get('birth_date')
       }
       
       merged_participants.append(merged)
   ```

4. **Use Merged Data for Booking**

---

## 🧪 Testing Bokun Integration

### Test 1: Fetch Bookings

```bash
# Test Bokun API connection
docker-compose exec backend python manage.py shell

# In Python shell:
from services.bokun_service import BokunService
bokun = BokunService()

# Fetch bookings
bookings = bokun.get_bookings(status='CONFIRMED')
print(f"Found {len(bookings)} bookings")

# Get participants
participants = bokun.get_booking_participants(bookings[0]['id'])
print(f"Participants: {participants}")
```

### Test 2: Webhook Simulation

```bash
# Simulate Bokun webhook
curl -X POST http://localhost:8000/api/v1/bokun/webhook/ \
  -H "Content-Type: application/json" \
  -H "X-Bokun-Signature: test-signature" \
  -d '{
    "event": "booking.confirmed",
    "booking": {
      "id": "BOK-2026-001",
      "reference": "REF-001",
      "date": "28/03/2026",
      "participants_count": 2
    }
  }'
```

### Test 3: Complete Flow

```bash
# 1. Create Bokun booking (via Bokun dashboard)
# 2. Webhook creates MonitorTask
# 3. Worker finds Vatican slot
# 4. Extension books ticket
# 5. Backend updates Bokun
# 6. Verify in Bokun dashboard
```

---

## 📊 Bokun Data Mapping

### Bokun → Vatican Mapping

| Bokun Field | Vatican Field | Notes |
|-------------|---------------|-------|
| `firstName` | `first_name` | Direct mapping |
| `lastName` | `last_name` | Direct mapping |
| `email` | `email` | Direct mapping |
| `phone` | `phone` | Format: +39 123456789 |
| `dateOfBirth` | `birth_date` | Format: YYYY-MM-DD |
| `nationality` | `country` | Map to country code |
| `passportNumber` | N/A | Not used by Vatican |

### Vatican → Bokun Mapping

| Vatican Field | Bokun Field | Notes |
|---------------|-------------|-------|
| `date` | `ticketDate` | Format: DD/MM/YYYY |
| `time` | `ticketTime` | Format: HH:MM |
| `ticket_id` | `externalId` | Vatican ticket ID |
| `reference` | `externalReference` | Vatican booking ref |
| `total_price` | `ticketPrice` | In EUR |

---

## 🔐 Security Considerations

### 1. **API Key Protection**
- Store in environment variables
- Never commit to git
- Rotate regularly

### 2. **Webhook Verification**
```python
import hmac
import hashlib

def verify_bokun_signature(signature, payload):
    """Verify Bokun webhook signature"""
    secret = settings.BOKUN_WEBHOOK_SECRET
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

### 3. **Data Privacy**
- Encrypt sensitive data
- Comply with GDPR
- Log access to participant data

---

## 📚 Bokun API Reference

### Common Endpoints

```
GET    /bookings                    # List bookings
GET    /bookings/{id}               # Get booking details
POST   /bookings                    # Create booking
PATCH  /bookings/{id}               # Update booking
GET    /bookings/{id}/participants  # Get participants
POST   /bookings/{id}/tickets       # Add tickets
GET    /bookings/{id}/payment       # Get payment status
PATCH  /bookings/{id}/payment       # Update payment
```

### Authentication

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### Rate Limits

- **Standard**: 100 requests/minute
- **Premium**: 1000 requests/minute

---

## 🆘 Troubleshooting

### Issue: Bokun API Returns 401

**Solution**: Check API key is correct and not expired

### Issue: Webhook Not Triggering

**Solution**: 
1. Verify webhook URL in Bokun dashboard
2. Check webhook secret matches
3. Ensure backend is accessible from internet

### Issue: Participant Data Not Syncing

**Solution**:
1. Check Bokun booking has participants
2. Verify API permissions
3. Check data format matches

---

## 📖 Related Documentation

- **PC Setup Guide**: `PC_SETUP_GUIDE.md`
- **System Integration**: `SYSTEM_INTEGRATION_SUMMARY.md`
- **Extension Guide**: `EXTENSION_COMPLETE_GUIDE.md`

---

**Last Updated**: May 22, 2026  
**Version**: 1.0  
**Status**: Ready for Implementation ✅
