# Cleanup and Sync Plan - Telegram + Extension

## 🎯 **Goal**

Create a **clean, synchronized flow** between Telegram and Extension by:
1. **Removing** unused/non-functional features
2. **Simplifying** the Telegram commands
3. **Syncing** with Extension workflow
4. **Keeping** only what works

---

## 📊 **Current Commands Analysis**

### **✅ KEEP - Essential for Extension Flow:**

| Command | Purpose | Used By | Status |
|---------|---------|---------|--------|
| `/start` | Main menu | User | ✅ Keep |
| `/setprofile` | Set contact + card | Extension | ✅ Keep |
| `/setparticipants` | Set visitor names | Extension | ✅ Keep |
| `/add` or `/snipe` | Create monitoring task | Extension | ✅ Keep |
| `/snipes` | View active monitors | User | ✅ Keep |
| `/holds` | View held slots | User | ✅ Keep |

---

### **❌ REMOVE - Not Used by Extension:**

| Command | Purpose | Why Remove |
|---------|---------|------------|
| `/pay` | Trigger browser agent | Extension does this automatically |
| `/open` | Open browser manually | Extension does this automatically |
| `/agent` | Control browser agent | Extension replaces this |
| `/stop_recap` | Pause keepalive | Not needed with extension |
| `/resume_recap` | Resume keepalive | Not needed with extension |
| `/setpaymode` | Set payment mode | Extension always auto-pays |
| `/setbrowsergroup` | Set browser trigger | Extension polls API directly |
| `/book` | Manual booking flow | Extension does this automatically |
| `/bulkhold` | Bulk slot locking | Complex, rarely used |
| `/deep_scan` | Scan all visitor counts | Advanced feature, rarely used |
| `/pending` | Approve groups | Admin only, keep separate |

---

### **🔄 SIMPLIFY - Merge/Streamline:**

| Current | Simplified | Reason |
|---------|-----------|--------|
| `/add` + `/snipe` | `/monitor` | One command, clearer name |
| `/snipes` + `/holds` | `/status` | Combined view |
| `/setprofile` | Keep as is | Already simple |
| `/setparticipants` | Keep as is | Already simple |

---

## 🎯 **Simplified Command Structure**

### **CORE COMMANDS (5 total):**

```
1. /start
   → Main menu with buttons

2. /setprofile
   → Set your contact info + card details
   → Used by extension for booking

3. /setparticipants <task_id>
   → Upload visitor names for specific task
   → Used by extension for form filling

4. /monitor
   → Create new monitoring task
   → Backend monitors, extension books

5. /status
   → View active monitors + held slots
   → See what's happening
```

---

## 📋 **Simplified Flow**

### **SETUP (One Time):**

```
Step 1: /start
  → Welcome message
  → Shows main menu

Step 2: /setprofile
  → Enter name, email, phone
  → Enter card details
  → Saved to database

Step 3: Done!
  → Profile ready for all bookings
```

---

### **DAILY USE:**

```
Step 1: /monitor
  → Select date
  → Select time
  → Select visitors
  → Upload participant names
  → Monitoring starts

Step 2: Wait (Automatic)
  → Backend monitors Vatican
  → Extension polls backend
  → Extension books automatically

Step 3: Receive Email
  → Vatican sends confirmation
  → Done!
```

---

### **CHECK STATUS:**

```
/status
  → Shows active monitors
  → Shows held slots
  → Shows recent bookings
```

---

## 🔧 **Implementation Plan**

### **Phase 1: Remove Unused Commands**

**Remove these command handlers:**
```python
# backend/telegram_bot.py

# ❌ Remove:
CommandHandler('pay', pay_cmd)
CommandHandler('open', open_browser_cmd)
CommandHandler('agent', agent_cmd)
CommandHandler('stop_recap', stop_recap_cmd)
CommandHandler('resume_recap', resume_recap_cmd)
CommandHandler('setpaymode', setpaymode_cmd)
CommandHandler('setbrowsergroup', setbrowsergroup_cmd)
CommandHandler('book', book_cmd)
CommandHandler('bulkhold', bulkhold_cmd)
CommandHandler('deep_scan', deep_scan_cmd)
```

**Keep these:**
```python
# ✅ Keep:
CommandHandler('start', start)
CommandHandler('setprofile', setprofile_cmd)
CommandHandler('setparticipants', setparticipants_cmd)
CommandHandler('add', add_cmd)  # Rename to 'monitor'
CommandHandler('snipes', snipes_cmd)  # Rename to 'status'
CommandHandler('holds', holds_cmd)  # Merge into 'status'
CommandHandler('pending', pending_cmd)  # Admin only
```

---

### **Phase 2: Simplify /start Menu**

**Current (Complex):**
```
/start
  ├─ Add Monitor
  ├─ View Monitors
  ├─ Set Profile
  ├─ Set Participants
  ├─ Set Pay Mode
  ├─ Bulk Hold
  ├─ Book Manually
  ├─ Open Browser
  ├─ Agent Control
  └─ ... (too many options)
```

**New (Simple):**
```
/start
  ├─ 🎫 Create Monitor
  ├─ 📊 View Status
  ├─ 👤 Set Profile
  └─ ℹ️ Help
```

---

### **Phase 3: Update Database Models**

**Remove unused fields:**
```python
# backend/monitors/models.py

class MonitorTask:
    # ❌ Remove:
    checkout_method  # Extension always uses browser
    pay_mode  # Extension always auto-pays
    remote_worker_needed  # Extension handles this
    remote_worker_claimed  # Extension handles this
    agent_target  # Extension handles this
    
    # ✅ Keep:
    tier  # 'notify', 'hold', 'snipe'
    participants_json  # Used by extension
    # ... other essential fields
```

---

### **Phase 4: Simplify Backend API**

**Remove unused endpoints:**
```python
# backend/monitors/views.py

# ❌ Remove:
/api/v1/browser-pending/  # Extension doesn't use
/api/v1/agent-config/  # Extension doesn't use
/api/v1/stop-recap/  # Extension doesn't use
/api/v1/resume-recap/  # Extension doesn't use

# ✅ Keep:
/api/v1/available-slots/  # Extension uses this
/api/v1/holds/  # Extension uses this
/api/v1/tasks/  # Extension uses this
```

---

### **Phase 5: Update Extension**

**Ensure extension only uses:**
```javascript
// Extension only needs:
GET /api/v1/available-slots/  // Poll for held slots
POST /api/v1/holds/{id}/mark-paid  // Mark as booked

// Extension doesn't need:
// ❌ /api/v1/browser-pending/
// ❌ /api/v1/agent-config/
// ❌ Any manual booking endpoints
```

---

## 📝 **New User Guide**

### **Quick Start (3 Steps):**

```
1. Setup Profile (One Time)
   /setprofile
   → Enter your details
   → Enter card info

2. Create Monitor
   /monitor
   → Select date
   → Select time
   → Upload participant names

3. Install Extension
   → Install in Chrome
   → Enable "Backend Listener"
   → Done! Automatic booking enabled
```

---

### **Daily Use:**

```
1. Create monitors for dates you want
   /monitor → 28/03/2026 10:00

2. Extension watches backend
   → Polls every 10 seconds
   → Opens windows automatically
   → Books tickets automatically

3. You receive confirmation emails
   → Check your inbox
   → Done!
```

---

## 🎯 **Benefits of Cleanup**

### **Before (Complex):**
- 15+ commands
- Multiple booking methods
- Confusing workflows
- Unused features
- Hard to maintain

### **After (Simple):**
- 5 core commands ✅
- One booking method (extension) ✅
- Clear workflow ✅
- Only working features ✅
- Easy to maintain ✅

---

## 📊 **Command Comparison**

### **BEFORE:**
```
/start - Main menu
/add - Add monitor
/snipe - Add snipe monitor
/snipes - View snipes
/holds - View holds
/setprofile - Set profile
/setparticipants - Set participants
/setpaymode - Set payment mode
/bulkhold - Bulk hold
/setbrowsergroup - Set browser group
/book - Manual booking
/pay - Trigger payment
/open - Open browser
/agent - Control agent
/stop_recap - Stop keepalive
/resume_recap - Resume keepalive
/deep_scan - Deep scan
/pending - Approve groups (admin)
/cancel - Cancel operation
```
**Total: 19 commands** 😵

---

### **AFTER:**
```
/start - Main menu
/setprofile - Set profile + card
/setparticipants - Set visitor names
/monitor - Create monitoring task
/status - View monitors + holds
/help - Show help
/pending - Approve groups (admin)
/cancel - Cancel operation
```
**Total: 8 commands** ✅

---

## 🔄 **Migration Path**

### **Step 1: Mark as Deprecated**
```python
@deprecated
async def pay_cmd(...):
    await update.message.reply_text(
        "⚠️ This command is deprecated.\n"
        "Use the browser extension for automatic booking.\n"
        "See /help for more info."
    )
```

### **Step 2: Remove After 1 Week**
```python
# Remove deprecated commands after users migrate
```

### **Step 3: Update Documentation**
```markdown
# Old commands removed:
- /pay → Use extension
- /open → Use extension
- /agent → Use extension
- /book → Use extension
```

---

## ✅ **Final Command List**

### **USER COMMANDS:**
```
/start - Main menu
/setprofile - Set your profile + card
/setparticipants <task_id> - Set visitor names
/monitor - Create monitoring task
/status - View active monitors + holds
/help - Show help guide
/cancel - Cancel current operation
```

### **ADMIN COMMANDS:**
```
/pending - Approve Telegram groups
```

---

## 🎯 **Summary**

### **What We're Removing:**
- ❌ Manual booking commands (`/book`, `/pay`, `/open`)
- ❌ Browser agent commands (`/agent`, `/setbrowsergroup`)
- ❌ Keepalive commands (`/stop_recap`, `/resume_recap`)
- ❌ Complex features (`/bulkhold`, `/deep_scan`)
- ❌ Redundant commands (`/setpaymode`)

### **What We're Keeping:**
- ✅ Profile setup (`/setprofile`)
- ✅ Participant setup (`/setparticipants`)
- ✅ Monitoring (`/monitor`)
- ✅ Status viewing (`/status`)
- ✅ Extension integration (automatic booking)

### **Result:**
```
19 commands → 8 commands
Complex flow → Simple flow
Multiple methods → One method (extension)
Confusing → Clear
Hard to maintain → Easy to maintain
```

**Clean, simple, synchronized system!** 🚀

---

## 📚 **Next Steps**

1. **Review this plan** - Confirm what to remove
2. **Implement Phase 1** - Remove unused commands
3. **Implement Phase 2** - Simplify /start menu
4. **Implement Phase 3** - Clean database models
5. **Implement Phase 4** - Clean API endpoints
6. **Test** - Verify extension still works
7. **Document** - Update user guide

**Ready to implement?** Let me know which phase to start with!
