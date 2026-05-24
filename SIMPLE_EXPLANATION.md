# Simple Explanation: Telegram vs Extension

## 🎯 **The Confusion**

You have **TWO ways** to book Vatican tickets, and they work **together**. Let me explain simply:

---

## 📱 **METHOD 1: Telegram Bot (Backend)**

### **What It Does:**
Monitors Vatican website and **holds slots** when they become available.

### **How It Works:**

```
1. You send commands in Telegram:
   /setprofile → Set your contact info & card
   /setparticipants → Set visitor names
   /snipe → Start monitoring

2. Backend monitors Vatican:
   - Checks every 5-60 seconds
   - Uses proxies (no rate limiting)
   - Detects when slots open

3. When slot opens:
   - Backend HOLDS the slot (55 minutes)
   - Creates HeldSlot in database
   - Sends Telegram notification

4. You have 2 options:
   A) Complete booking via Telegram commands
   B) Let extension complete it automatically
```

### **What You Get:**
- ✅ Slot is **held** for you (55 minutes)
- ✅ You get **Telegram notification**
- ✅ You can **review** before booking
- ✅ You can use **extension** to complete it

---

## 🌐 **METHOD 2: Browser Extension**

### **What It Does:**
Automatically **completes bookings** for slots that backend has held.

### **How It Works:**

```
1. Extension polls backend API:
   GET /api/v1/available-slots/
   (Every 10 seconds)

2. Backend responds with held slots:
   {
     "slots": [
       {
         "date": "28/03/2026",
         "time": "10:00",
         "participants": ["John Doe", "Jane Smith"],
         "card": {...}
       }
     ]
   }

3. Extension opens incognito window:
   - Navigates to Vatican website
   - Selects ticket
   - Selects EXACT time (10:00)
   - Fills form with participants
   - Fills payment with card
   - Clicks PAY button

4. Booking complete!
```

### **What You Get:**
- ✅ **Automatic** booking (no manual work)
- ✅ **Parallel** booking (10+ windows)
- ✅ **Fast** completion (~30 seconds)
- ✅ **Accurate** (exact time & participants)

---

## 🔄 **How They Work TOGETHER**

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPLETE FLOW                            │
└─────────────────────────────────────────────────────────────┘

Step 1: YOU → Telegram Bot
   /setprofile
   /setparticipants 123
   /snipe

Step 2: Telegram Bot → Backend
   Creates MonitorTask in database
   Backend starts monitoring Vatican

Step 3: Backend → Vatican API
   Checks every 5-60 seconds
   Detects when slot opens

Step 4: Backend → Database
   Creates HeldSlot record
   Slot is held for 55 minutes

Step 5: Extension → Backend API
   Polls /api/v1/available-slots/
   Finds HeldSlot

Step 6: Extension → Vatican Website
   Opens incognito window
   Completes full booking
   Uses exact time & participants

Step 7: Extension → Backend API
   Marks slot as booked
   Updates database

Step 8: YOU → Email
   Receives confirmation from Vatican
   Booking complete!
```

---

## 📊 **Simple Comparison**

| Feature | Telegram Bot | Extension |
|---------|--------------|-----------|
| **Setup** | Send commands | Install extension |
| **Monitoring** | Backend does it | Backend does it |
| **Notification** | Telegram message | Desktop notification |
| **Booking** | Manual or API | Automatic |
| **Speed** | Slow (manual) | Fast (30 seconds) |
| **Parallel** | One at a time | 10+ simultaneous |
| **User Action** | Click buttons | None (automatic) |

---

## 🎯 **Which One to Use?**

### **Use BOTH Together (Recommended):**

```
Telegram Bot: Monitoring + Holding
     +
Extension: Automatic Booking
     =
Best Experience!
```

**Why?**
- ✅ Telegram monitors 24/7
- ✅ Backend holds slots
- ✅ Extension books automatically
- ✅ You do nothing!

---

### **Use Only Telegram (Manual):**

```
Telegram Bot: Monitoring + Holding + Manual Booking
```

**When?**
- You don't have browser extension
- You want to review before booking
- You prefer manual control

**How?**
1. Telegram notifies you
2. You click link in Telegram
3. You complete booking manually

---

### **Use Only Extension (Not Recommended):**

```
Extension: Monitoring + Booking
```

**Why Not?**
- ❌ Extension can't monitor 24/7
- ❌ Extension gets rate limited
- ❌ Extension needs browser open
- ❌ Less reliable

---

## 🎮 **Step-by-Step Guide**

### **SETUP (One Time):**

#### **1. Setup Telegram Bot:**
```
/start
/setprofile
  → Enter your name, email, phone, card
/setparticipants
  → Upload file with visitor names
```

#### **2. Install Extension:**
```
1. Download extension
2. Load in Chrome
3. Configure backend URL: http://localhost:8000
4. Enable "Backend Listener" mode
```

---

### **DAILY USE:**

#### **1. Start Monitoring (Telegram):**
```
/snipe
  → Select date: 28/03/2026
  → Select time: 10:00
  → Select visitors: 2
```

**Result:** Backend starts monitoring

---

#### **2. Wait for Slot (Automatic):**
```
Backend checks Vatican every 5-60 seconds
When slot opens:
  → Backend holds it
  → Telegram notifies you
  → Extension sees it
```

---

#### **3. Booking Happens (Automatic):**
```
Extension:
  → Opens incognito window
  → Selects ticket
  → Selects time 10:00
  → Fills form with participants
  → Fills payment with card
  → Clicks PAY
  → Done in 30 seconds!
```

---

#### **4. Confirmation (Email):**
```
Vatican sends confirmation email
You receive booking reference
Tickets in your inbox!
```

---

## 🔍 **Common Questions**

### **Q: Do I need both Telegram and Extension?**
**A:** No, but **recommended**. Telegram monitors, Extension books automatically.

---

### **Q: Can I use only Telegram?**
**A:** Yes! Telegram can do everything, but booking is manual.

---

### **Q: Can I use only Extension?**
**A:** Not recommended. Extension needs backend to monitor 24/7.

---

### **Q: Where do I set participant names?**
**A:** In Telegram via `/setparticipants <task_id>`

---

### **Q: Where do I set card details?**
**A:** In Telegram via `/setprofile`

---

### **Q: How does Extension know what to book?**
**A:** Extension reads from backend API (gets data from Telegram setup)

---

### **Q: Can I have different participants for different times?**
**A:** Yes! Use `/setparticipants <task_id>` for each task

---

### **Q: What if I want to review before booking?**
**A:** Use "Hold Mode" in extension or book manually via Telegram

---

## 📝 **Data Flow**

```
YOU (Telegram)
    ↓
  Profile Data → Database (BuyerProfile)
  Participants → Database (MonitorTask.participants_json)
  Monitoring Task → Database (MonitorTask)
    ↓
BACKEND (Worker)
    ↓
  Monitors Vatican API
  Detects slot opening
    ↓
  Creates HeldSlot → Database
    ↓
EXTENSION (Browser)
    ↓
  Polls /api/v1/available-slots/
  Gets: date, time, participants, card
    ↓
  Opens incognito window
  Completes booking
    ↓
VATICAN (Website)
    ↓
  Confirms booking
  Sends email
    ↓
YOU (Email)
    ↓
  Receives confirmation
  Done!
```

---

## ✅ **Summary**

### **Telegram Bot:**
- 📱 Setup (profile, participants, monitoring)
- 🔍 Monitoring (24/7, with proxies)
- 🔒 Holding (keeps slot alive)
- 📢 Notification (tells you when found)

### **Extension:**
- 🌐 Automatic booking (no manual work)
- ⚡ Fast (30 seconds)
- 🔄 Parallel (10+ windows)
- 🎯 Accurate (exact time & participants)

### **Together:**
```
Telegram (Setup + Monitor) + Extension (Auto-Book) = Perfect! 🎉
```

---

## 🎯 **Recommended Setup**

```
1. Use Telegram for:
   ✅ Setting profile
   ✅ Setting participants
   ✅ Starting monitoring
   ✅ Getting notifications

2. Use Extension for:
   ✅ Automatic booking
   ✅ Fast completion
   ✅ Parallel bookings

3. Result:
   ✅ You set up once in Telegram
   ✅ Backend monitors 24/7
   ✅ Extension books automatically
   ✅ You receive confirmation email
   ✅ Zero manual work!
```

**This is the BEST way to use the system!** 🚀

---

## 🎉 **Quick Start**

### **5-Minute Setup:**

```bash
# 1. Telegram (2 minutes)
/start
/setprofile → Fill form
/setparticipants → Upload names

# 2. Extension (1 minute)
Install extension
Set backend URL: http://localhost:8000
Enable "Backend Listener"

# 3. Start Monitoring (1 minute)
/snipe → Select date & time

# 4. Wait (Automatic)
Backend monitors
Extension books
You receive email

# Done! 🎉
```

**That's it! Now you understand how both work together!** 🚀
