# 🔐 COMPLETE CREDENTIALS GUIDE

## Issue: Multiple Databases

You're seeing agencies with IDs 3-14, but my scripts found IDs 1-5. This means:

1. **You're looking at PRODUCTION database** (on server)
2. **I'm checking LOCAL/DEV database** (on your machine)

---

## ✅ Solution: Reset ALL Passwords

Run this command to reset ALL user passwords in your current database:

```bash
python reset_all_passwords.py
```

This will set ALL passwords to: **`hydra2026`**

---

## 🎯 For Your Production Agencies (IDs 3-14)

Based on your list, here are the expected credentials after reset:

| ID | Agency Name | Username | Password | Status |
|----|-------------|----------|----------|--------|
| 3 | Vatican Bot Agency 1 | `vatican_bot_agency_1` | `hydra2026` | ✅ |
| 4 | Vatican Bot Agency 2 | `wondersofrome` | `hydra2026` | ✅ |
| 6 | System Admin | `superadmin` | `hydra2026` | ✅ |
| 7 | Agency-admin | *(create user)* | `hydra2026` | ⚠️ No user |
| 9 | Tour_guides | `Tourguides` | `hydra2026` | ✅ |
| 10 | Italy pass | `Italypass` | `hydra2026` | ✅ |
| 11 | Big bus | `bigbus` | `hydra2026` | ✅ |
| 12 | Wondersofrome | `wondersofrome123` | `hydra2026` | ✅ |
| 13 | Mahabur | `Bot123` | `hydra2026` | ✅ |
| 14 | WOR | *(create user)* | `hydra2026` | ⚠️ No user |

---

## 🔧 Create Missing Users

For agencies without users (IDs 7, 14), run:

```python
# Connect to your production database
python backend/manage.py shell

# Then run:
from monitors.models import User, Agency

# For Agency ID 7 (Agency-admin)
agency7 = Agency.objects.get(id=7)
user7 = User.objects.create(
    username='agency_admin',
    email='agency_admin@agency.local',
    agency=agency7,
    is_active=True,
    is_admin=True
)
user7.set_password('hydra2026')
user7.save()
print(f"✅ Created: agency_admin / hydra2026")

# For Agency ID 14 (WOR)
agency14 = Agency.objects.get(id=14)
user14 = User.objects.create(
    username='wor_admin',
    email='wor@agency.local',
    agency=agency14,
    is_active=True,
    is_admin=True
)
user14.set_password('hydra2026')
user14.save()
print(f"✅ Created: wor_admin / hydra2026")
```

---

## 📝 Quick Reference

### All Passwords: `hydra2026`

### Login URLs:
- **Production:** https://hydrabot.it
- **Local:** http://localhost:3000

### Test Login:
```bash
curl -X POST https://hydrabot.it/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"hydra2026"}'
```

---

## 🔍 Verify Your Database

To see which database you're actually using:

```bash
# Check database location
python -c "
import os, sys, django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.conf import settings
print('Database:', settings.DATABASES['default'])
"
```

---

## 🚨 Important Notes

### Telegram Groups ≠ User Accounts

- **Telegram Groups:** Receive notifications (no login)
- **User Accounts:** Login to web interface (have username/password)

### If Telegram Group Members Need Login:

They need separate User accounts created. Telegram groups themselves cannot login.

---

## 📊 Database Confusion Explained

You have **TWO separate databases**:

1. **Local/Dev Database** (`backend/db.sqlite3` on your machine)
   - Has agencies with IDs 1-5
   - Used when running locally

2. **Production Database** (on your server)
   - Has agencies with IDs 3-14
   - Used by live website

**Solution:** Run the password reset script on BOTH:

```bash
# On your local machine
python reset_all_passwords.py

# On your production server (SSH in first)
ssh your-server
cd /path/to/travelagenntbot
python reset_all_passwords.py
```

---

## ✅ Final Checklist

- [ ] Run `reset_all_passwords.py` on LOCAL database
- [ ] Run `reset_all_passwords.py` on PRODUCTION database (via SSH)
- [ ] Create users for agencies without users (IDs 7, 14)
- [ ] Test login with `superadmin` / `hydra2026`
- [ ] Verify all agencies can access web interface
- [ ] Document credentials in secure location

---

**Last Updated:** April 26, 2026  
**All Passwords:** `hydra2026`  
**Status:** Ready to deploy
