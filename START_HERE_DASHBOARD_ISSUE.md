# Dashboard Shows "Sold Out" - Start Here

## The Issue
Your Vercel dashboard (https://bot-pl2x.vercel.app/) is showing all tickets as "sold out" even though you confirmed March 16 has availability for 1 visitor.

## Quick Fix (1 Command)

```powershell
.\QUICK_FIX_DASHBOARD.ps1
```

This script will:
1. ✅ Diagnose the exact problem
2. ✅ Apply the appropriate fix
3. ✅ Tell you what to do next

---

## What Was Fixed

I've applied a critical fix to the bot code:

**Problem**: The bot was checking with wrong visitor counts (always 2) instead of using the actual task configuration.

**Fix Applied**: Updated the entire call chain to pass the `visitors` parameter correctly.

**Files Changed**:
- `backend/monitors/tasks.py` - 5 changes
- `worker_vatican/god_tier_monitor.py` - 6 changes
- `worker_vatican/hydra_monitor.py` - 3 changes

---

## Possible Causes of "Sold Out" Dashboard

### 1. Bot hasn't run with new code yet
**Solution**: Run `.\QUICK_FIX_DASHBOARD.ps1`

### 2. Bot is finding availability but dashboard not updating
**Symptoms**: 
- Backend API shows data: http://localhost:8000/api/tasks/
- But Vercel dashboard shows sold out

**Causes**:
- Cloudflare tunnel not working
- Wrong API URL in Vercel
- CORS issues

**Solution**: Check tunnel and Vercel configuration

### 3. Tickets genuinely sold out
**Solution**: Verify visitor count in logs with `.\check_logs_windows.ps1`

---

## Diagnostic Scripts

I've created 5 PowerShell scripts to help you:

### 1. Quick Fix (Start Here)
```powershell
.\QUICK_FIX_DASHBOARD.ps1
```
Diagnoses the problem and applies the fix.

### 2. Check Actual Availability
```powershell
.\check_actual_availability.ps1
```
Shows if the bot is actually finding slots or if everything is genuinely sold out.

### 3. Force Fresh Check
```powershell
.\force_check_and_verify.ps1
```
Triggers new checks and verifies backend connection.

### 4. Check Visitor Counts
```powershell
.\check_logs_windows.ps1
```
Verifies the visitor count fix is working in logs.

### 5. Test Task #19
```powershell
.\test_task_19_windows.ps1
```
Specifically tests Task #19 (March 16, 1 visitor).

---

## Expected Results After Fix

### In Logs
You should see:
```
✅ /fromtag/1/1773615600000/MV-Biglietti/1  (1 visitor, not 2!)
✅ visitorNum=1  (in API calls)
✅ Smart Group: 16/03/2026/929041748/None/1v → 1 agencies
✅ Found X slots
```

### In Dashboard
After 2-3 minutes:
- Tasks should show "available" status
- Slot counts should appear
- Last checked time should update

---

## Troubleshooting Flow

```
Run: .\QUICK_FIX_DASHBOARD.ps1
         ↓
    Diagnosis?
         ↓
    ┌────┴────┐
    │         │
NO CHECKS   FOUND     ALL SOLD OUT
    │      SLOTS          │
    ↓         │           ↓
Wait 2-3   Check      Check visitor
minutes    tunnel     count in logs
    │         │           │
    ↓         ↓           ↓
Refresh   Verify     Restart worker
dashboard  Vercel    & force check
          config
```

---

## Manual Verification Steps

### 1. Check if services are running
```powershell
docker-compose ps
```

### 2. Check recent check results
```powershell
.\check_actual_availability.ps1
```

### 3. Test backend API
Open in browser:
```
http://localhost:8000/api/tasks/
```

Should show JSON with task data.

### 4. Test Cloudflare tunnel
Open in browser:
```
https://your-tunnel-url.trycloudflare.com/api/tasks/
```

Should show same JSON as localhost.

### 5. Check Vercel configuration
1. Go to Vercel project settings
2. Environment Variables
3. Verify `NEXT_PUBLIC_API_URL` = tunnel URL

---

## Timeline

After running the quick fix:

- **0-30 sec**: Tasks queued
- **30-90 sec**: Workers processing
- **90-180 sec**: Results saved
- **180+ sec**: Dashboard should update

If still showing sold out after 5 minutes, the issue is dashboard connection, not the bot.

---

## Common Issues

### "Worker not running"
```powershell
docker-compose up -d worker_vatican
```

### "Backend not accessible"
```powershell
docker-compose restart backend
```

### "Tunnel URL changed"
Free Cloudflare tunnels change URL on restart. Update Vercel environment variable.

### "Dashboard not refreshing"
Hard refresh: `Ctrl + Shift + R`

---

## Need More Help?

See detailed guide:
- `DASHBOARD_SOLD_OUT_TROUBLESHOOTING.md`

Or check specific documentation:
- `WINDOWS_DEPLOYMENT_GUIDE.md` - Windows commands
- `FINAL_VERIFICATION_REPORT.md` - Technical details
- `FIXES_APPLIED_SUMMARY.md` - What was changed

---

## Quick Reference

| What | Command |
|------|---------|
| **Start here** | `.\QUICK_FIX_DASHBOARD.ps1` |
| Check if finding slots | `.\check_actual_availability.ps1` |
| Force fresh check | `.\force_check_and_verify.ps1` |
| Check visitor counts | `.\check_logs_windows.ps1` |
| Test Task #19 | `.\test_task_19_windows.ps1` |
| View logs | `docker-compose logs -f worker_vatican` |
| Restart worker | `docker-compose restart worker_vatican` |
| Test backend | http://localhost:8000/api/tasks/ |

---

## Summary

1. Run `.\QUICK_FIX_DASHBOARD.ps1`
2. Follow the specific instructions it gives you
3. Wait 2-3 minutes
4. Refresh dashboard

The fix has been applied to the code. Now we just need to ensure the bot runs with the new code and the dashboard can access the results.
