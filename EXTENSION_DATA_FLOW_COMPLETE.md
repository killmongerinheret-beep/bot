# Complete Data Flow: Telegram → Backend → Extension

## 🎯 **How Extension Gets Snipe Options**

---

## 📊 **COMPLETE DATA FLOW DIAGRAM**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    1. USER SETS UP VIA TELEGRAM                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            /setprofile      /setparticipants    /snipe
                    │               │               │
                    ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    2. DATA STORED IN DATABASE                           │
│                                                                         │
│  BuyerProfile.objects.create(                                          │
│    agency=agency,                                                      │
│    first_name='John',                                                  │
│    last_name='Doe',                                                    │
│    email='john@example.com',                                          │
│    phone='+393331234567',                                             │
│    city='Roma',                                                        │
│    country='Italy',                                                    │
│    birth_date='1990-01-15',                                           │
│    card_number='4111111111111111',                                    │
│    card_expiry='12/2028',                                             │
│    card_cvv='123',                                                     │
│    card_holder='John Doe',                                            │
│    participants_json='[                                               │
│      {"first_name": "John", "last_name": "Doe"},                     │
│      {"first_name": "Jane", "last_name": "Smith"}                    │
│    ]'                                                                  │
│  )                                                                     │
│                                                                         │
│  MonitorTask.objects.create(                                           │
│    agency=agency,                                                      │
│    tier='hold',  # or 'snipe'                                         │
│    dates=['28/03/2026'],                                              │
│    preferred_times=['10:00'],                                         │
│    visitors=2,                                                         │
│    participants_json='[                                               │
│      {"first_name": "John", "last_name": "Doe"},                     │
│      {"first_name": "Jane", "last_name": "Smith"}                    │
│    ]'  # Task-specific (optional)                                    │
│  )                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    3. WORKER MONITORS VATICAN                           │
│                                                                         │
│  Celery worker runs every 60 seconds:                                  │
│    - Calls Vatican Search API                                          │
│    - Calls Vatican timeavail API                                       │
│    - Detects state change (closed → open)                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    4. SLOT OPENS → CREATE HELDSLOT                      │
│                                                                         │
│  HeldSlot.objects.create(                                              │
│    task=task,                                                          │
│    date='28/03/2026',                                                 │
│    slot_time='10:00',                                                  │
│    slot_id='2026*8776',                                               │
│    ticket_id='2129030053',                                            │
│    ticket_name='Musei Vaticani - Biglietti d\'ingresso',             │
│    visitors=2,                                                         │
│    adult_count=2,                                                      │
│    child_count=0,                                                      │
│    jsessionid='ABC123...',                                            │
│    status='held'                                                       │
│  )                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              5. EXTENSION POLLS BACKEND API                             │
│                                                                         │
│  GET /api/v1/available-slots/                                          │
│  Authorization: Bearer <session_token>                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              6. BACKEND ASSEMBLES COMPLETE DATA                         │
│                                                                         │
│  def get_available_slots(request):                                     │
│    # Get HeldSlot                                                      │
│    held = HeldSlot.objects.get(id=123)                                │
│                                                                         │
│    # Get related task                                                  │
│    task = held.task                                                    │
│                                                                         │
│    # Get agency                                                        │
│    agency = task.agency                                                │
│                                                                         │
│    # Get buyer profile                                                 │
│    buyer_profile = agency.buyer_profile                               │
│                                                                         │
│    # Get participants (priority order):                               │
│    # 1. Task-specific participants                                    │
│    if task.participants_json:                                         │
│      participants = json.loads(task.participants_json)                │
│    # 2. Profile participants (fallback)                               │
│    elif buyer_profile.participants_json:                              │
│      participants = json.loads(buyer_profile.participants_json)       │
│    # 3. Use profile name (last resort)                                │
│    else:                                                               │
│      participants = [{                                                 │
│        'first_name': buyer_profile.first_name,                        │
│        'last_name': buyer_profile.last_name                           │
│      }] * held.visitors                                               │
│                                                                         │
│    # Assemble response                                                 │
│    return {                                                            │
│      'slots': [{                                                       │
│        'id': held.id,                                                  │
│        'date': held.date,                                             │
│        'time': held.slot_time,                                        │
│        'ticket_id': held.ticket_id,                                   │
│        'visitors': held.visitors,                                     │
│        'profile': {                                                    │
│          'first_name': buyer_profile.first_name,                      │
│          'last_name': buyer_profile.last_name,                        │
│          'email': buyer_profile.email,                                │
│          'phone': buyer_profile.phone,                                │
│          'city': buyer_profile.city,                                  │
│          'country': buyer_profile.country,                            │
│          'birth_date': buyer_profile.birth_date,                      │
│          'gender': buyer_profile.gender                               │
│        },                                                              │
│        'participants': participants,                                  │
│        'card': {                                                       │
│          'number': buyer_profile.card_number,                         │
│          'expiry': buyer_profile.card_expiry,                         │
│          'cvv': buyer_profile.card_cvv,                               │
│          'holder': buyer_profile.card_holder                          │
│        }                                                               │
│      }]                                                                │
│    }                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              7. EXTENSION RECEIVES COMPLETE DATA                        │
│                                                                         │
│  Response JSON:                                                        │
│  {                                                                     │
│    "slots": [                                                          │
│      {                                                                 │
│        "id": 123,                                                      │
│        "date": "28/03/2026",                                          │
│        "time": "10:00",                                               │
│        "ticket_id": "2129030053",                                     │
│        "ticket_name": "Musei Vaticani - Biglietti d'ingresso",       │
│        "visitors": 2,                                                  │
│        "adult_count": 2,                                              │
│        "child_count": 0,                                              │
│        "language": null,                                              │
│        "profile": {                                                    │
│          "first_name": "John",                                        │
│          "last_name": "Doe",                                          │
│          "email": "john@example.com",                                │
│          "phone": "+393331234567",                                   │
│          "city": "Roma",                                              │
│          "country": "Italy",                                          │
│          "birth_date": "1990-01-15",                                 │
│          "gender": "M"                                                │
│        },                                                              │
│        "participants": [                                              │
│          {"first_name": "John", "last_name": "Doe"},                 │
│          {"first_name": "Jane", "last_name": "Smith"}                │
│        ],                                                              │
│        "card": {                                                       │
│          "number": "4111111111111111",                               │
│          "expiry": "12/2028",                                         │
│          "cvv": "123",                                                │
│          "holder": "John Doe"                                         │
│        }                                                               │
│      }                                                                 │
│    ],                                                                  │
│    "count": 1                                                          │
│  }                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              8. EXTENSION OPENS INCOGNITO WINDOW                        │
│                                                                         │
│  chrome.windows.create({                                               │
│    url: 'https://tickets.museivaticani.va/home',                      │
│    incognito: true                                                     │
│  });                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              9. EXTENSION SENDS AUTO-BOOKING MESSAGE                    │
│                                                                         │
│  chrome.tabs.sendMessage(tabId, {                                      │
│    action: 'startAutoBooking',                                         │
│    slot: slot,  // Complete data from API                             │
│    config: {                                                           │
│      autoConfirm: true,                                                │
│      autoPay: true                                                     │
│    }                                                                   │
│  });                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              10. CONTENT SCRIPT USES DATA FOR BOOKING                   │
│                                                                         │
│  async function startAutoBookingFlow(config) {                         │
│    const slot = config.slot;                                           │
│                                                                         │
│    // Use ticket_id from slot                                         │
│    await selectTicket({ ticket_id: slot.ticket_id });                 │
│                                                                         │
│    // Use visitors from slot                                          │
│    await selectQuantity(slot.visitors);                               │
│                                                                         │
│    // Use time from slot                                              │
│    await selectTimeSlot(slot.time);                                   │
│                                                                         │
│    // Use profile + participants from slot                            │
│    await fillCheckoutFormWithParticipants(                            │
│      slot.profile,      // John Doe contact info                      │
│      slot.participants, // [John Doe, Jane Smith]                     │
│      slot.visitors      // 2                                          │
│    );                                                                  │
│                                                                         │
│    // Use card from slot                                              │
│    await fillPaymentForm(                                             │
│      slot.card,    // 4111111111111111                                │
│      slot.profile  // john@example.com                                │
│    );                                                                  │
│                                                                         │
│    await clickPayButton();                                            │
│  }                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 **DATA SOURCE PRIORITY**

### **Participants (3 levels of fallback):**

```python
# Priority 1: Task-specific participants (set via /setparticipants <task_id>)
if task.participants_json:
    participants = json.loads(task.participants_json)

# Priority 2: Profile participants (set via /setparticipants without task_id)
elif buyer_profile.participants_json:
    participants = json.loads(buyer_profile.participants_json)

# Priority 3: Use profile name (last resort)
else:
    participants = [{
        'first_name': buyer_profile.first_name,
        'last_name': buyer_profile.last_name
    }] * visitors
```

### **Profile Data (always from BuyerProfile):**
```python
profile = {
    'first_name': buyer_profile.first_name,
    'last_name': buyer_profile.last_name,
    'email': buyer_profile.email,
    'phone': buyer_profile.phone,
    'city': buyer_profile.city,
    'country': buyer_profile.country,
    'birth_date': buyer_profile.birth_date,
    'gender': buyer_profile.gender
}
```

### **Card Data (always from BuyerProfile):**
```python
card = {
    'number': buyer_profile.card_number,
    'expiry': buyer_profile.card_expiry,
    'cvv': buyer_profile.card_cvv,
    'holder': buyer_profile.card_holder
}
```

---

## 📝 **TELEGRAM COMMANDS**

### **1. Set Profile (Contact + Card Info)**
```
/setprofile

→ Prompts for:
  - First Name
  - Last Name
  - Email
  - Phone
  - City
  - Country
  - Birth Date
  - Gender
  - Card Number
  - Card Expiry
  - Card CVV
  - Card Holder

→ Saves to: BuyerProfile (one per agency)
```

### **2. Set Participants (Names for Each Visitor)**
```
/setparticipants [task_id]

→ Upload .txt or .csv file:
  John Doe
  Jane Smith
  Bob Johnson

→ Saves to:
  - If task_id provided: MonitorTask.participants_json (task-specific)
  - If no task_id: BuyerProfile.participants_json (agency-wide)
```

### **3. Create Snipe Task**
```
/snipe

→ Prompts for:
  - Date
  - Time
  - Visitors
  - Ticket Type

→ Creates: MonitorTask with tier='snipe' or 'hold'
```

---

## 🎯 **EXAMPLE FLOW**

### **Step 1: User Sets Up Profile**
```
User: /setprofile
Bot: Enter first name:
User: John
Bot: Enter last name:
User: Doe
Bot: Enter email:
User: john@example.com
...
Bot: ✅ Profile saved!
```

**Database:**
```python
BuyerProfile.objects.create(
    agency=agency,
    first_name='John',
    last_name='Doe',
    email='john@example.com',
    ...
)
```

### **Step 2: User Sets Participants**
```
User: /setparticipants
Bot: Upload .txt file with names
User: [uploads file]
  John Doe
  Jane Smith
Bot: ✅ 2 participants saved!
```

**Database:**
```python
buyer_profile.participants_json = '[
  {"first_name": "John", "last_name": "Doe"},
  {"first_name": "Jane", "last_name": "Smith"}
]'
```

### **Step 3: User Creates Snipe Task**
```
User: /snipe
Bot: Select date:
User: 28/03/2026
Bot: Select time:
User: 10:00
Bot: ✅ Monitoring started!
```

**Database:**
```python
MonitorTask.objects.create(
    agency=agency,
    tier='hold',
    dates=['28/03/2026'],
    preferred_times=['10:00'],
    visitors=2
)
```

### **Step 4: Slot Opens**
```
Worker: Detects slot open
Worker: Creates HeldSlot
```

**Database:**
```python
HeldSlot.objects.create(
    task=task,
    date='28/03/2026',
    slot_time='10:00',
    ...
)
```

### **Step 5: Extension Polls API**
```javascript
// Extension background.js
const response = await fetch('http://localhost:8000/api/v1/available-slots/');
const data = await response.json();

// data.slots[0] contains:
{
  id: 123,
  date: '28/03/2026',
  time: '10:00',
  profile: { first_name: 'John', ... },
  participants: [
    { first_name: 'John', last_name: 'Doe' },
    { first_name: 'Jane', last_name: 'Smith' }
  ],
  card: { number: '4111...', ... }
}
```

### **Step 6: Extension Opens Window & Books**
```javascript
// Extension opens incognito window
chrome.windows.create({ url: '...', incognito: true });

// Content script fills form
fillCheckoutFormWithParticipants(
  slot.profile,      // John Doe
  slot.participants, // [John Doe, Jane Smith]
  slot.visitors      // 2
);

fillPaymentForm(slot.card, slot.profile);
clickPayButton();
```

---

## ✅ **SUMMARY**

### **Where Extension Gets Data:**

| Data Type | Source | Set Via |
|-----------|--------|---------|
| **Profile** | `BuyerProfile` | `/setprofile` |
| **Participants** | `MonitorTask.participants_json` OR `BuyerProfile.participants_json` | `/setparticipants` |
| **Card** | `BuyerProfile` | `/setprofile` |
| **Ticket ID** | `HeldSlot.ticket_id` | Vatican API |
| **Date/Time** | `HeldSlot.date` / `HeldSlot.slot_time` | Vatican API |

### **Data Flow:**
```
Telegram → Database → Backend API → Extension → Vatican Website
```

### **Key Points:**
- ✅ All data comes from **backend API** (`/api/v1/available-slots/`)
- ✅ Backend assembles data from **multiple database tables**
- ✅ Extension receives **complete booking data** in one API call
- ✅ Extension uses data to **complete full booking automatically**

---

## 🎯 **ANSWER TO YOUR QUESTION:**

**"Where does the extension method get the snipe options from?"**

**Answer:** The extension gets ALL snipe options from the **backend API** (`/api/v1/available-slots/`), which assembles data from:

1. **`HeldSlot`** - Slot details (date, time, ticket_id)
2. **`MonitorTask`** - Task settings (visitors, participants)
3. **`BuyerProfile`** - Profile + card data

All of this data is **set via Telegram commands** (`/setprofile`, `/setparticipants`, `/snipe`) and stored in the database. The extension just polls the API and receives everything it needs in one response! 🚀
