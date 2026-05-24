# Telegram Notification Status Report

**Date**: May 2, 2026  
**Status**: ⚠️ ISSUES FOUND

## 📊 Summary

- **Total Agencies**: 10
- **Groups with notifications enabled**: 5
- **Active Vatican monitoring tasks**: 154
- **Agencies ready to receive notifications**: 5
- **Agencies with issues**: 5

## ✅ Agencies Ready to Receive Notifications (5)

These agencies are properly configured and will receive notifications:

### 1. Vatican Bot Agency 1
- **Groups**: 3 total, 1 enabled
- **Enabled**: Vatican bot (-5077577076) ✅
- **Disabled**: 2 groups ❌
- **Active Tasks**: 1
- **Status**: ✅ Ready

### 2. Tour_guides
- **Groups**: 1 total, 1 enabled
- **Enabled**: Aby and Hydrasnipe (-5138949221) ✅
- **Active Tasks**: 1
- **Status**: ✅ Ready

### 3. Big bus
- **Groups**: 1 total, 1 enabled
- **Enabled**: Big bus (-5249053606) ✅
- **Active Tasks**: 22
- **Status**: ✅ Ready

### 4. Mahabur
- **Groups**: 1 total, 1 enabled
- **Enabled**: Bot2 (-5284108537) ✅
- **Active Tasks**: 5
- **Status**: ✅ Ready

### 5. WOR
- **Groups**: 1 total, 1 enabled
- **Enabled**: WOR Bot (-5245239270) ✅
- **Active Tasks**: 60
- **Status**: ✅ Ready

## ⚠️ Agencies with Issues (5)

### 1. Italy pass - Notifications Disabled ❌
- **Issue**: Has 1 approved group but notifications are disabled
- **Group**: Italy pasd (-5206664897)
- **Active Tasks**: 1
- **Fix**: Enable notifications for this group

**SQL Fix**:
```sql
UPDATE telegram_groups SET notification_enabled = true WHERE chat_id = '-5206664897';
```

### 2. Vatican Bot Agency 1 - Partial Configuration ⚠️
- **Issue**: Has 3 groups but only 1 has notifications enabled
- **Enabled**: Vatican bot (-5077577076) ✅
- **Disabled**: 
  - Admin Group (-520664897) ❌
  - Aby and Hydrasnipe (-5257636359) ❌
- **Active Tasks**: 1
- **Impact**: Only 1 of 3 groups receives notifications

**SQL Fix** (if you want to enable all groups):
```sql
UPDATE telegram_groups SET notification_enabled = true WHERE chat_id = '-520664897';
UPDATE telegram_groups SET notification_enabled = true WHERE chat_id = '-5257636359';
```

### 3. Vatican Bot Agency 2 - No Groups ❌
- **Issue**: No Telegram groups configured
- **Active Tasks**: 1
- **Fix**: Add bot to Telegram group and approve via /pending

### 4. Wondersofrome - No Groups ❌
- **Issue**: No Telegram groups configured
- **Active Tasks**: 61 (most active!)
- **Fix**: Add bot to Telegram group and approve via /pending

### 5. System Admin & Agency-admin - No Groups ❌
- **Issue**: No Telegram groups configured
- **Active Tasks**: 1 each
- **Fix**: Add bot to Telegram group and approve via /pending (if needed)

## 🔍 Detailed Analysis

### Notification Logic

The bot sends notifications when:
1. ✅ Agency has approved Telegram groups
2. ✅ Groups have `notification_enabled = true`
3. ✅ Agency has active monitoring tasks
4. ✅ Ticket state changes from 'closed' → 'available'
5. ✅ Task notification_mode is not 'silent'

### Why No Recent Notifications?

**Finding**: No availability events in last 24 hours

This means:
- All monitored dates are currently sold out
- No tickets became available in the last 24 hours
- **This is normal** - Vatican tickets are often sold out

When tickets DO become available:
- Bot will detect it within 5 seconds
- Notification will be sent to all enabled groups
- Each group gets max 1 notification per date (deduplication)

### Redis Loading Issue

**Error**: "Redis is loading the dataset in memory"

This confirms the Redis bloat issue we fixed earlier. The Redis cleanup needs to be run:

```bash
# Run the fix
run_redis_fix.bat  # Windows
bash run_redis_fix.sh  # Linux/Mac
```

## 🛠️ Recommended Fixes

### Priority 1: Enable Notifications for Italy pass

```bash
docker-compose exec -T backend python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from monitors.models import TelegramGroup
group = TelegramGroup.objects.get(chat_id='-5206664897')
group.notification_enabled = True
group.save()
print('✅ Enabled notifications for Italy pass')
"
```

### Priority 2: Add Groups for Wondersofrome (61 tasks!)

Wondersofrome has the most active tasks (61) but no Telegram groups!

**Steps**:
1. Add the bot to a Telegram group
2. Admin sends `/pending` to bot
3. Admin approves the group
4. Notifications will start working

### Priority 3: Enable All Groups for Vatican Bot Agency 1 (Optional)

If you want all 3 groups to receive notifications:

```bash
docker-compose exec -T backend python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from monitors.models import TelegramGroup
TelegramGroup.objects.filter(chat_id__in=['-520664897', '-5257636359']).update(notification_enabled=True)
print('✅ Enabled notifications for 2 additional groups')
"
```

### Priority 4: Fix Redis Bloat

Run the Redis cleanup to fix the loading issue:

```bash
run_redis_fix.bat  # Windows
bash run_redis_fix.sh  # Linux/Mac
```

## 📋 Quick Fix Commands

### Enable Italy pass notifications
```bash
docker-compose exec -T backend python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from monitors.models import TelegramGroup
TelegramGroup.objects.filter(chat_id='-5206664897').update(notification_enabled=True)
print('✅ Done')
"
```

### Enable all disabled groups
```bash
docker-compose exec -T backend python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from monitors.models import TelegramGroup
count = TelegramGroup.objects.filter(status='approved', notification_enabled=False).update(notification_enabled=True)
print(f'✅ Enabled {count} groups')
"
```

### Check status again
```bash
docker-compose exec -T backend python backend/check_notification_status.py
```

## ✅ Success Criteria

After applying fixes, you should have:

1. ✅ All approved groups have `notification_enabled = true`
2. ✅ All agencies with active tasks have at least 1 enabled group
3. ✅ Redis is clean (< 10k keys)
4. ✅ Workers are running and checking every 5 seconds

## 🎯 Expected Behavior

Once fixed:

1. **Bot checks Vatican API every 5 seconds**
2. **When tickets become available**:
   - Bot detects state change (closed → available)
   - Sends notification to ALL enabled groups for that agency
   - Each group gets max 1 notification per date
3. **Notification includes**:
   - Date
   - Ticket name
   - Available time slots
   - Direct booking link

## 📞 Testing

To test notifications are working:

1. **Wait for tickets to open** (natural test)
2. **Or create a test task** for a date that's already open
3. **Check Telegram groups** for notification

## 🔄 Monitoring

Check notification status anytime:

```bash
docker-compose exec -T backend python backend/check_notification_status.py
```

Check recent notifications:

```bash
docker-compose logs worker_vatican | grep "TELEGRAM ALERT"
```

Check for errors:

```bash
docker-compose logs worker_vatican | grep -i "error\|failed" | tail -20
```

---

**Summary**: 5 agencies are ready to receive notifications, 1 needs notifications enabled (Italy pass), and 4 need Telegram groups added (especially Wondersofrome with 61 tasks).
