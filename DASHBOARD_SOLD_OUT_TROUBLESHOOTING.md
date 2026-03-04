# Dashboard Shows "Sold Out" - Troubleshooting Guide

## Quick Diagnosis

Run these scripts in order:

### 1. Check if bot is finding availability
```powershell
.\check_actual_availability.ps1
```

This will tell you if the bot is actually finding slots or if everything is genuinely sold out.

### 2. Force a fresh check
```powershell
.\force_check_and_verify.ps1
```

This triggers new checks and verifies the backend connection.

### 3. Check visitor counts in logs
```powershell
.\check_logs_windows.ps1
```

This verifies the visitor count fix is working.

---

## Possible Causes

### Cause 1: Bot hasn't run yet with new code
**Symptom**: Dashboard shows old "sold out" data  
**Solution**: 
```powershell
.\force_check_and_verify.ps1
```
Wait 2-3 minutes, then refresh dashboard.

### Cause 2: Bot is finding availability but dashboard not updating
**Symptom**: `check_actual_availability.ps1` shows "✅ Available" but dashboard shows sold out  
**Possible Issues**:
- Backend API not accessible from Vercel
- Cloudflare tunnel not working
- CORS issues
- Dashboard not refreshing

**Solution**:
1. Test backend API locally:
   ```powershell
   # In browser, go to:
   http://localhost:8000/api/tasks/
   ```
   Should show JSON with task data

2. Check Cloudflare tunnel:
   ```powershell
   docker-compose ps
   # Look for cloudflare or tunnel service
   ```

3. Test tunnel URL:
   ```powershell
   # In browser, go to your tunnel URL:
   https://your-tunnel-url.trycloudflare.com/api/tasks/
   ```
   Should show same JSON as localhost

4. Check Vercel environment variables:
   - Go to Vercel dashboard
   - Settings → Environment Variables
   - Verify `NEXT_PUBLIC_API_URL` points to tunnel URL

### Cause 3: Tickets are genuinely sold out
**Symptom**: `check_actual_availability.ps1` shows "❌ Sold Out" for all checks  
**Possible Issues**:
- Wrong visitor count (checking with 2 instead of 1)
- Wrong dates
- Wrong ticket type

**Solution**:
1. Check visitor count in logs:
   ```powershell
   .\check_logs_windows.ps1
   ```
   Look for `/fromtag/1/...` for 1-visitor tasks

2. Verify Task #19 configuration:
   ```powershell
   .\test_task_19_windows.ps1
   ```

3. If visitor count is wrong, restart worker:
   ```powershell
   docker-compose restart worker_vatican
   ```

### Cause 4: Bot errors
**Symptom**: `check_actual_availability.ps1` shows "⚠️ Errors"  
**Solution**:
```powershell
docker-compose logs --tail=100 worker_vatican
```
Look for error messages and stack traces.

---

## Step-by-Step Troubleshooting

### Step 1: Verify Services Running
```powershell
docker-compose ps
```

Should show:
- ✅ backend (running)
- ✅ worker_vatican (running)
- ✅ db (running)
- ✅ redis (running)

### Step 2: Check Recent Checks
```powershell
.\check_actual_availability.ps1
```

**If shows "No recent checks"**:
- Bot hasn't run yet
- Run: `.\force_check_and_verify.ps1`

**If shows "✅ Available"**:
- Bot IS working!
- Problem is dashboard connection
- Go to Step 4

**If shows "❌ Sold Out"**:
- Check visitor count (Step 3)
- Verify dates are correct
- Check if tickets are genuinely sold out

**If shows "⚠️ Errors"**:
- Check worker logs
- Look for Python errors
- Verify proxy configuration

### Step 3: Verify Visitor Count Fix
```powershell
.\check_logs_windows.ps1
```

Look for:
- ✅ `/fromtag/1/...` for 1-visitor tasks
- ✅ `visitorNum=1` in API calls
- ✅ `Smart Group: .../1v`

**If still seeing `/fromtag/2/...`**:
- Worker didn't restart with new code
- Run: `docker-compose restart worker_vatican`
- Wait 30 seconds
- Run: `.\force_check_and_verify.ps1`

### Step 4: Test Backend API
```powershell
# Open in browser:
http://localhost:8000/api/tasks/
```

**If shows JSON data**:
- ✅ Backend is working
- Check Cloudflare tunnel (Step 5)

**If shows error or doesn't load**:
- Backend not running
- Run: `docker-compose restart backend`
- Check: `docker-compose logs backend`

### Step 5: Test Cloudflare Tunnel
```powershell
# Check if tunnel is running
docker-compose ps | Select-String "cloudflare"

# Or check logs
docker-compose logs cloudflare
```

**If tunnel not found**:
- You might be running tunnel separately
- Check if `cloudflared` is running on your system
- Or you might be using ngrok instead

**Test tunnel URL in browser**:
```
https://your-tunnel-url.trycloudflare.com/api/tasks/
```

**If doesn't work**:
- Tunnel not running
- Tunnel not pointing to backend:8000
- Restart tunnel

### Step 6: Verify Vercel Configuration
1. Go to: https://vercel.com/your-project/settings/environment-variables
2. Check `NEXT_PUBLIC_API_URL` = your tunnel URL
3. If changed, redeploy Vercel app

### Step 7: Check Browser Console
1. Open Vercel dashboard: https://bot-pl2x.vercel.app/
2. Press F12 (Developer Tools)
3. Go to Console tab
4. Look for errors:
   - ❌ CORS errors → Backend CORS settings
   - ❌ Network errors → Tunnel not accessible
   - ❌ 404 errors → Wrong API URL

---

## Common Issues and Fixes

### Issue: "All tasks show sold out"
**Fix**:
1. Run: `.\check_actual_availability.ps1`
2. If bot IS finding slots, problem is dashboard
3. If bot NOT finding slots, check visitor count

### Issue: "Dashboard not updating"
**Fix**:
1. Hard refresh: Ctrl+Shift+R
2. Clear browser cache
3. Check if API URL is correct in Vercel

### Issue: "Worker keeps restarting"
**Fix**:
```powershell
docker-compose logs worker_vatican
```
Look for Python errors, fix them, then:
```powershell
docker-compose restart worker_vatican
```

### Issue: "Tunnel URL keeps changing"
**Fix**:
- Free Cloudflare tunnels change URL on restart
- Use named tunnel (paid) for stable URL
- Or use ngrok with auth token

---

## Quick Reference

| Problem | Command |
|---------|---------|
| Check if bot finding slots | `.\check_actual_availability.ps1` |
| Force fresh check | `.\force_check_and_verify.ps1` |
| Check visitor counts | `.\check_logs_windows.ps1` |
| Test Task #19 | `.\test_task_19_windows.ps1` |
| View worker logs | `docker-compose logs -f worker_vatican` |
| Restart worker | `docker-compose restart worker_vatican` |
| Test backend API | Open `http://localhost:8000/api/tasks/` |
| Check services | `docker-compose ps` |

---

## Expected Timeline

After running `.\force_check_and_verify.ps1`:

- **0-30 seconds**: Tasks queued
- **30-90 seconds**: Workers processing checks
- **90-180 seconds**: Results saved to database
- **180+ seconds**: Dashboard should show updated data

If dashboard still shows sold out after 5 minutes:
1. The issue is dashboard connection, not the bot
2. Check backend API and tunnel
3. Verify Vercel configuration

---

## Need More Help?

1. Run all diagnostic scripts
2. Save the output
3. Check worker logs: `docker-compose logs worker_vatican > worker_logs.txt`
4. Review the output for specific errors
