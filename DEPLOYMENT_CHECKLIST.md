# Telegram Multi-Tenant Deployment Checklist

## Pre-Deployment Verification ✅

### 1. Code Changes Applied
- [x] TelegramGroup model added to `backend/monitors/models.py`
- [x] Migration 0011 created and ready
- [x] API endpoints added to `backend/monitors/views.py`
- [x] Routes added to `backend/monitors/urls.py`
- [x] Group handlers in `backend/telegram_bot.py` (already present)
- [x] Notification filtering in `backend/monitors/notification_utils.py` (already present)
- [x] Admin dashboard created at `frontend/src/app/admin/telegram-groups/page.tsx`
- [x] Test script created: `test_telegram_groups.py`

### 2. No Syntax Errors
```bash
✅ backend/monitors/views.py - No diagnostics
✅ backend/monitors/urls.py - No diagnostics
✅ backend/telegram_bot.py - No diagnostics
✅ frontend/src/app/admin/telegram-groups/page.tsx - No diagnostics
```

---

## Deployment Steps

### Step 1: Apply Database Migration
```bash
# Run migration
docker-compose exec backend python manage.py migrate monitors

# Verify migration
docker-compose exec backend python manage.py showmigrations monitors
```

Expected output:
```
[X] 0001_initial
[X] 0002_proxy_sitecredential
[X] 0003_agency_is_active
[X] 0004_monitortask_check_interval
[X] 0005_agency_owner_id_proxy_consecutive_failures_and_more
[X] 0006_agency_plan_monitortask_ticket_id_and_more
[X] 0007_fix_owner_id_schema
[X] 0009_alter_monitortask_language
[X] 0010_alter_monitortask_site_alter_sitecredential_site
[X] 0011_telegramgroup  ← NEW
```

### Step 2: Restart Backend Services
```bash
# Restart backend to load new code
docker-compose restart backend

# Restart telegram bot to load new handlers
docker-compose restart telegram_bot

# Restart workers (optional, but recommended)
docker-compose restart worker_vatican
```

### Step 3: Verify Services
```bash
# Check all containers are running
docker-compose ps

# Check backend logs
docker-compose logs backend | tail -20

# Check telegram bot logs
docker-compose logs telegram_bot | tail -20
```

### Step 4: Test Database
```bash
# Run test script
python test_telegram_groups.py
```

Expected output:
```
✓ TelegramGroup model imported successfully
📊 Total Groups in Database: 0
Status Distribution:
  PENDING: 0
  APPROVED: 0
  REJECTED: 0
  SUSPENDED: 0
```

### Step 5: Test API Endpoints
```bash
# Test list endpoint
curl http://localhost:8000/api/v1/telegram-groups/

# Should return: []
```

### Step 6: Rebuild Frontend (if needed)
```bash
cd frontend

# Install dependencies (if new)
npm install

# Start dev server
npm run dev

# Or build for production
npm run build
```

### Step 7: Test Admin Dashboard
1. Open browser: http://localhost:3000/admin/telegram-groups
2. Should see empty dashboard with stats showing 0
3. Verify no console errors

### Step 8: Test Bot Integration
1. Open Telegram
2. Add your bot to a test group
3. Bot should send welcome message
4. Check database: `python test_telegram_groups.py`
5. Should see 1 pending group

### Step 9: Test Approval Flow
1. Open admin dashboard
2. Should see the pending group
3. Click "Approve"
4. Optionally link to agency
5. Confirm approval
6. Bot should send approval message to group
7. Refresh dashboard - status should be "approved"

### Step 10: Test Notification Filtering
```python
# In Django shell
docker-compose exec backend python manage.py shell

from monitors.notification_utils import send_telegram_signal

# Get your group chat_id from database
from monitors.models import TelegramGroup
group = TelegramGroup.objects.first()
print(f"Chat ID: {group.chat_id}")

# Test notification (should work if approved)
send_telegram_signal(group.chat_id, '✅ Test notification - you should see this!')

# Change status to pending
group.status = 'pending'
group.save()

# Test again (should be blocked)
send_telegram_signal(group.chat_id, '❌ You should NOT see this!')
# Check logs: docker-compose logs worker_vatican | grep "Skipping notification"
```

---

## Environment Variables Check

### Required
```bash
# Check if set
docker-compose exec backend env | grep TELEGRAM_BOT_TOKEN
```

### Optional (but recommended)
```bash
# Add to .env file
ADMIN_TELEGRAM_IDS=your_telegram_id,another_admin_id

# Restart services
docker-compose restart telegram_bot
```

To get your Telegram ID:
1. Message @userinfobot on Telegram
2. Copy your user ID
3. Add to .env

---

## Rollback Plan (if needed)

### If something goes wrong:

1. **Revert migration**
   ```bash
   docker-compose exec backend python manage.py migrate monitors 0010
   ```

2. **Restore old code**
   ```bash
   git checkout HEAD~1 backend/monitors/views.py
   git checkout HEAD~1 backend/monitors/urls.py
   ```

3. **Restart services**
   ```bash
   docker-compose restart backend telegram_bot
   ```

---

## Post-Deployment Monitoring

### Check Logs Regularly
```bash
# Backend logs
docker-compose logs -f backend

# Telegram bot logs
docker-compose logs -f telegram_bot

# Worker logs
docker-compose logs -f worker_vatican
```

### Monitor Database Growth
```bash
# Check group count
docker-compose exec backend python manage.py shell
>>> from monitors.models import TelegramGroup
>>> TelegramGroup.objects.count()
```

### Monitor API Performance
```bash
# Test API response time
time curl http://localhost:8000/api/v1/telegram-groups/
```

---

## Success Criteria

✅ Migration applied successfully  
✅ All containers running  
✅ No errors in logs  
✅ API endpoints responding  
✅ Admin dashboard loads  
✅ Bot responds when added to group  
✅ Group appears in database  
✅ Approval flow works  
✅ Notifications respect approval status  

---

## Common Issues & Solutions

### Issue: Migration fails
**Solution:**
```bash
# Check database connection
docker-compose exec backend python manage.py dbshell

# Try fake migration if already applied manually
docker-compose exec backend python manage.py migrate monitors 0011 --fake
```

### Issue: Bot doesn't respond
**Solution:**
```bash
# Check bot token
docker-compose exec telegram_bot env | grep TELEGRAM_BOT_TOKEN

# Check bot is running
docker-compose ps telegram_bot

# Restart bot
docker-compose restart telegram_bot

# Check logs
docker-compose logs telegram_bot | grep -i error
```

### Issue: API returns 500 error
**Solution:**
```bash
# Check backend logs
docker-compose logs backend | grep -i error

# Check if migration applied
docker-compose exec backend python manage.py showmigrations monitors

# Restart backend
docker-compose restart backend
```

### Issue: Frontend can't connect to API
**Solution:**
```bash
# Check NEXT_PUBLIC_API_URL in frontend/.env
cat frontend/.env.local

# Should be: NEXT_PUBLIC_API_URL=http://localhost:8000

# Restart frontend
cd frontend && npm run dev
```

---

## Performance Optimization

### Database Indexes (already included in migration)
- `chat_id` - Unique index for fast lookups
- `status` - Index for filtering
- `agency_id` - Foreign key index

### Caching (future enhancement)
```python
# Cache group approval status for 5 minutes
from django.core.cache import cache

def is_group_approved(chat_id):
    cache_key = f'group_approved_{chat_id}'
    result = cache.get(cache_key)
    
    if result is None:
        group = TelegramGroup.objects.filter(chat_id=chat_id).first()
        result = group.is_approved() if group else False
        cache.set(cache_key, result, 300)  # 5 minutes
    
    return result
```

---

## Security Checklist

✅ Admin approval required before notifications  
✅ Audit trail (who added, when, who approved)  
✅ Rejection reasons logged  
✅ Suspension capability  
✅ Per-group notification control  
✅ Agency isolation  
✅ No sensitive data in logs  

---

## Next Steps After Deployment

1. **Monitor for 24 hours**
   - Check logs every few hours
   - Verify notifications working
   - Monitor database growth

2. **Add more groups**
   - Test with multiple groups
   - Test different group types (group, supergroup, channel)
   - Test approval/rejection flow

3. **Gather feedback**
   - Ask users about experience
   - Monitor group activity
   - Track notification delivery

4. **Plan Phase 2 features**
   - Auto-linking to agencies
   - Group settings via bot commands
   - Usage analytics
   - Billing integration

---

## Support & Documentation

- **Implementation Guide:** `TELEGRAM_MULTI_TENANT_COMPLETE.md`
- **Setup Guide:** `TELEGRAM_MULTI_TENANT_SETUP.md`
- **Test Script:** `test_telegram_groups.py`
- **This Checklist:** `DEPLOYMENT_CHECKLIST.md`

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Status:** ⬜ Pending / ⬜ In Progress / ⬜ Complete  
**Issues Found:** _____________  
**Resolution:** _____________
