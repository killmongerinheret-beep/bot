# 🚀 VERCEL DEPLOYMENT GUIDE
**Date:** February 28, 2026  
**Status:** Ready for Deployment

---

## ✅ FRONTEND BUILD STATUS

**Build Command:** `npm run build`  
**Build Status:** ✅ SUCCESS  
**Build Time:** 14.1s  
**Next.js Version:** 16.1.4  
**TypeScript:** ✅ Passed (4.1s)  
**Pages Generated:** 2 (/, /_not-found)

---

## 🎯 WHAT WAS FIXED

The frontend now correctly handles language defaults:

### Before Fix:
```typescript
language: 'ENG'  // ❌ Hardcoded for all tickets
```

### After Fix:
```typescript
language: ''  // ✅ Empty, determined by ticket type

// Standard tickets → language = undefined (null in DB)
// Guided tours → language = 'ENG' | 'ITA' | 'FRA' | 'DEU' | 'SPA'
```

---

## 📋 DEPLOYMENT STEPS

### Option 1: Deploy via Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

3. **Login to Vercel**:
   ```bash
   vercel login
   ```

4. **Deploy to production**:
   ```bash
   vercel --prod
   ```

5. **Verify deployment**:
   - Check the deployment URL provided by Vercel
   - Test creating a new monitor
   - Verify language field behavior

---

### Option 2: Deploy via Vercel Dashboard

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard

2. **Select your project** (or import if first time)

3. **Trigger new deployment**:
   - Click "Deployments" tab
   - Click "Redeploy" button
   - Or push to your Git repository (auto-deploy)

4. **Wait for build to complete**

5. **Verify deployment**:
   - Visit your production URL
   - Test the new monitor creation flow

---

### Option 3: Git Push (Auto-Deploy)

If you have Vercel connected to your Git repository:

1. **Commit changes**:
   ```bash
   git add frontend/src/components/TaskModal.tsx
   git commit -m "fix: Remove hardcoded ENG language default for standard tickets"
   ```

2. **Push to main branch**:
   ```bash
   git push origin main
   ```

3. **Vercel will auto-deploy**:
   - Check Vercel dashboard for deployment status
   - Usually takes 2-3 minutes

---

## 🧪 POST-DEPLOYMENT TESTING

### Test 1: Create Standard Ticket Monitor

1. Open dashboard: `https://your-vercel-url.vercel.app`
2. Login with your credentials
3. Click "New Monitor" button
4. Fill in form:
   - Site: Vatican Museums
   - Area: Standard Entry (Biglietti)
   - Date: Any future date
   - Visitors: 2
5. Submit

**Expected Result:**
- ✅ Monitor created successfully
- ✅ No language field shown for standard tickets
- ✅ Database entry has `language=null`

**Verification Command:**
```bash
# Check the newly created task
docker-compose exec -T backend python -c "
from monitors.models import MonitorTask
task = MonitorTask.objects.latest('id')
print(f'Task ID: {task.id}')
print(f'Ticket Type: {task.ticket_type}')
print(f'Language: {task.language}')
print(f'Area: {task.area_name}')
print(f'Expected: ticket_type=0, language=None')
"
```

---

### Test 2: Create Guided Tour Monitor

1. Open dashboard
2. Click "New Monitor"
3. Fill in form:
   - Site: Vatican Museums
   - Area: Guided Tours (MV-Tour)
   - Language: English (should be visible)
   - Date: Any future date
   - Visitors: 1
4. Submit

**Expected Result:**
- ✅ Monitor created successfully
- ✅ Language selector visible for guided tours
- ✅ Database entry has `language='ENG'`

**Verification Command:**
```bash
# Check the newly created task
docker-compose exec -T backend python -c "
from monitors.models import MonitorTask
task = MonitorTask.objects.latest('id')
print(f'Task ID: {task.id}')
print(f'Ticket Type: {task.ticket_type}')
print(f'Language: {task.language}')
print(f'Area: {task.area_name}')
print(f'Expected: ticket_type=1, language=ENG')
"
```

---

### Test 3: Verify Bot Behavior

After creating a new standard ticket monitor:

```bash
# Check worker logs for the new task
docker-compose logs worker_vatican | grep "Task [NEW_TASK_ID]" | tail -20
```

**Expected in logs:**
- ✅ `Lang: None` (not "Lang: ENG")
- ✅ Deep link: `/MV-Biglietti/1`
- ✅ API URL: `visitLang=` (empty)
- ✅ API Status: 200
- ✅ Slots found: > 0

---

## 🔍 TROUBLESHOOTING

### Issue: Build fails on Vercel

**Solution:**
1. Check build logs in Vercel dashboard
2. Ensure all dependencies are in `package.json`
3. Verify Node.js version compatibility
4. Try local build: `npm run build`

---

### Issue: Language still defaults to 'ENG'

**Solution:**
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Check if correct version is deployed
4. Verify deployment URL matches your domain

---

### Issue: New tasks still have wrong language

**Solution:**
1. Check if frontend is actually deployed
2. Verify API endpoint is correct
3. Check browser console for errors
4. Test API directly:
   ```bash
   curl -X POST https://your-backend-url/api/tasks/ \
     -H "Content-Type: application/json" \
     -d '{
       "site": "vatican",
       "area_name": "MV-Biglietti",
       "ticket_type": 0,
       "dates": ["2026-03-15"],
       "visitors": 2,
       "agency": 1
     }'
   ```

---

## 📊 VERIFICATION CHECKLIST

After deployment, verify:

- [ ] Frontend deployed successfully to Vercel
- [ ] Dashboard loads without errors
- [ ] Can create new standard ticket monitor
- [ ] Language field NOT shown for standard tickets
- [ ] Language field IS shown for guided tours
- [ ] New standard tasks have `language=null` in database
- [ ] New guided tour tasks have proper language code
- [ ] Bot processes new tasks correctly
- [ ] Logs show "Lang: None" for standard tickets
- [ ] API calls return 200 responses
- [ ] Slots are detected correctly

---

## 🎯 EXPECTED OUTCOMES

### Database:
```sql
-- New standard ticket task
SELECT id, ticket_type, language, area_name 
FROM monitors_monitortask 
WHERE id = [NEW_TASK_ID];

-- Expected:
-- ticket_type = 0
-- language = NULL
-- area_name = 'MV-Biglietti'
```

### Bot Logs:
```
[INFO] Task 28: Standard Entry (Full Price)
[INFO] Type: 0 (Standard), Lang: None, Visitors: 2
[INFO] Deep Link: /fromtag/2/1774652400000/MV-Biglietti/1
[INFO] API URL: ...visitLang=&visitTypeId=...
[INFO] API Status: 200
[INFO] Found 13 slots
```

### Telegram Message:
```
🎉 TICKETS JUST OPENED!

📅 Date: 15/03/2026
🎫 Ticket: Standard Entry (Full Price)
👥 Visitors: 2
🔍 Method: Smart

🕐 Available Times (13 total):
   • 09:00
   • 09:30
   • 10:00

🔗 [Click Here to Book Now](https://tickets.museivaticani.va/home/fromtag/2/1773622800000/MV-Biglietti/1)
```

---

## 🚨 ROLLBACK PLAN

If deployment causes issues:

### Option 1: Revert in Vercel Dashboard
1. Go to Vercel Dashboard → Deployments
2. Find previous working deployment
3. Click "..." → "Promote to Production"

### Option 2: Git Revert
```bash
git revert HEAD
git push origin main
```

### Option 3: Manual Fix
1. Revert `TaskModal.tsx` to previous version
2. Rebuild: `npm run build`
3. Redeploy: `vercel --prod`

---

## 📝 DEPLOYMENT NOTES

### Environment Variables:
Ensure these are set in Vercel:
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` - Clerk auth key
- Any other required environment variables

### Build Settings:
- Framework: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`
- Node Version: 20.x (recommended)

---

## ✅ SUCCESS CRITERIA

Deployment is successful when:

1. ✅ Frontend builds without errors
2. ✅ Dashboard loads and is responsive
3. ✅ Can create new monitors
4. ✅ Standard tickets: No language field, `language=null` in DB
5. ✅ Guided tours: Language selector visible, proper code in DB
6. ✅ Bot processes new tasks correctly
7. ✅ No "Lang: ENG" in logs for standard tickets
8. ✅ API calls return 200 responses
9. ✅ Availability detection working
10. ✅ Telegram alerts include booking links

---

## 🎉 FINAL STATUS

**Frontend Code:** ✅ FIXED  
**Local Build:** ✅ SUCCESS  
**Ready for Deployment:** ✅ YES  
**Deployment Method:** Choose Option 1, 2, or 3 above  
**Estimated Deployment Time:** 2-5 minutes  
**Testing Required:** Yes (follow post-deployment tests)

---

**Next Steps:**
1. Choose deployment method (CLI, Dashboard, or Git)
2. Deploy to Vercel
3. Run post-deployment tests
4. Verify new monitors are created correctly
5. Monitor bot logs for any issues

---

**Last Updated:** February 28, 2026 16:30 UTC  
**Prepared By:** AI Assistant (Kiro)  
**Status:** 📋 READY FOR DEPLOYMENT

