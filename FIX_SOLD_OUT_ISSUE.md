# Fix: Dashboard Shows "Sold Out" But Backend Has Slots

## Current Situation

✅ **Backend**: Working perfectly - Task #18 shows AVAILABLE with 8 slots  
✅ **Cloudflare Tunnel**: Running (PID: 7840)  
❌ **Dashboard**: Shows "sold out" or incorrect status

## Root Cause Analysis

The backend is returning correct data:
```json
{
  "id": 18,
  "last_status": "available",
  "latest_check": {
    "status": "available",
    "details": {
      "slots": ["09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "14:30", "15:00"]
    }
  }
}
```

But the dashboard shows "sold out". This means:

### Possible Issues:

1. **Frontend is caching old data**
2. **Environment variable not set correctly in Vercel**
3. **Frontend is reading wrong field**
4. **CORS blocking the request**
5. **Frontend not redeployed after env change**

## Step-by-Step Fix

### Step 1: Test Your Cloudflare Tunnel

Run this script:
```powershell
powershell -ExecutionPolicy Bypass -File test_cloudflare_tunnel.ps1
```

This will:
- Check if cloudflared is running ✅
- Test local backend ✅
- Ask for your Cloudflare URL
- Test the tunnel
- Show you the exact URL to use in Vercel

### Step 2: Verify Vercel Environment Variable

1. Go to https://vercel.com/dashboard
2. Select your project
3. Click **Settings** (top menu)
4. Click **Environment Variables** (left sidebar)
5. Check if `NEXT_PUBLIC_API_URL` is set

**It should be:**
```
NEXT_PUBLIC_API_URL = https://your-tunnel-url.trycloudflare.com/api/v1
```

**Common mistakes:**
- ❌ Missing `/api/v1` at the end
- ❌ Using `/api/` instead of `/api/v1/`
- ❌ Using `http://` instead of `https://`
- ❌ Using `localhost` URL

### Step 3: Test the URL Manually

Open your browser and go to:
```
https://your-tunnel-url.trycloudflare.com/api/v1/tasks/
```

You should see JSON with your tasks. Check:
- Task #18 should have `"last_status": "available"`
- `latest_check.details.slots` should have 8 items

### Step 4: Redeploy Frontend

**IMPORTANT**: Environment variables only apply to NEW deployments!

1. Go to **Deployments** tab in Vercel
2. Click **...** menu on latest deployment
3. Click **Redeploy**
4. Wait for deployment to complete

### Step 5: Clear Browser Cache

After redeployment:
1. Open your Vercel app
2. Press **Ctrl+Shift+Delete** (Windows) or **Cmd+Shift+Delete** (Mac)
3. Clear cache and cookies
4. Or just do a hard refresh: **Ctrl+F5**

### Step 6: Check Browser Console

1. Open your Vercel app
2. Press **F12** to open DevTools
3. Go to **Console** tab
4. Look for errors:
   - CORS errors
   - Network errors
   - API URL being used

5. Go to **Network** tab
6. Refresh the page
7. Look for API calls to `/api/v1/tasks/`
8. Check the response

## Frontend Code Check

Make sure your frontend is using the environment variable correctly:

### ❌ Wrong:
```typescript
// Hardcoded URL
const API_URL = 'http://localhost:8000/api/v1';
```

### ✅ Correct:
```typescript
// Using environment variable
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
```

### Display Logic

Make sure you're reading the correct field:

```typescript
function TaskCard({ task }) {
  // Use last_status, not status
  const status = task.last_status;
  
  // Get slots from latest_check
  const slots = task.latest_check?.details?.slots || [];
  
  return (
    <div>
      <h3>Task #{task.id}</h3>
      <p>Status: {status}</p>
      <p>Slots: {slots.length}</p>
      {slots.length > 0 && (
        <ul>
          {slots.map(slot => <li key={slot}>{slot}</li>)}
        </ul>
      )}
    </div>
  );
}
```

## Common Issues & Solutions

### Issue 1: Dashboard shows old data

**Symptom**: Dashboard shows "sold out" even after refresh

**Solution**:
1. Clear browser cache
2. Hard refresh (Ctrl+F5)
3. Check if frontend is fetching from correct URL
4. Check Network tab in DevTools

### Issue 2: CORS errors in console

**Symptom**: Console shows "CORS policy blocked"

**Solution**: Add to `backend/core/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "https://*.trycloudflare.com",
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True
```

Restart backend:
```bash
docker-compose restart backend
```

### Issue 3: Environment variable not working

**Symptom**: Frontend still uses localhost

**Solution**:
1. Make sure variable name starts with `NEXT_PUBLIC_`
2. Redeploy after setting variable
3. Check build logs for the variable value

### Issue 4: Cloudflare tunnel URL changes

**Symptom**: Worked before, now doesn't work

**Solution**: Free Cloudflare tunnels get new URLs each time
1. Check current URL in cloudflared terminal
2. Update Vercel environment variable
3. Redeploy

**Better solution**: Use ngrok with auth token for stable URL, or deploy backend to production

### Issue 5: API returns 404

**Symptom**: Network tab shows 404 for API calls

**Solution**: Check the API path
- ✅ Correct: `/api/v1/tasks/`
- ❌ Wrong: `/api/tasks/`

## Verification Checklist

- [ ] Cloudflared is running
- [ ] Local backend returns correct data (`http://localhost:8000/api/v1/tasks/`)
- [ ] Cloudflare tunnel URL works in browser
- [ ] Vercel environment variable is set correctly
- [ ] Environment variable includes `/api/v1` at the end
- [ ] Frontend has been redeployed after env change
- [ ] Browser cache cleared
- [ ] No CORS errors in console
- [ ] Network tab shows successful API calls
- [ ] API response shows `"last_status": "available"`
- [ ] Dashboard displays correct status

## Quick Test Commands

**Test local backend:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/18/" -UseBasicParsing | Select-Object -ExpandProperty Content | python -m json.tool
```

**Test Cloudflare tunnel:**
```powershell
Invoke-WebRequest -Uri "https://your-url.trycloudflare.com/api/v1/tasks/18/" -UseBasicParsing | Select-Object -ExpandProperty Content | python -m json.tool
```

**Check cloudflared process:**
```powershell
Get-Process cloudflared
```

**View cloudflared logs:**
Check the terminal where you ran `cloudflared tunnel --url http://localhost:8000`

## Expected Result

After following these steps, your dashboard should show:

```
┌─────────────────────────────────────────────┐
│ Task #18 - March 28, 2026                   │
├─────────────────────────────────────────────┤
│ Status: ✅ AVAILABLE                        │
│ Slots: 8 available                          │
│                                             │
│ Times:                                      │
│   • 09:30                                   │
│   • 10:00                                   │
│   • 10:30                                   │
│   • 11:00                                   │
│   • 11:30                                   │
│   • 12:00                                   │
│   • 14:30                                   │
│   • 15:00                                   │
│                                             │
│ Last Checked: 2 minutes ago                 │
└─────────────────────────────────────────────┘
```

## Still Not Working?

If you've tried everything and it's still not working:

1. **Share the Cloudflare tunnel URL** - I can test it
2. **Share your Vercel project URL** - I can check the frontend
3. **Check browser console** - Share any error messages
4. **Share Vercel environment variables** - Make sure they're set correctly

## Alternative: Use ngrok Instead

If Cloudflare tunnel is causing issues:

1. Stop cloudflared
2. Install ngrok: https://ngrok.com/download
3. Run: `ngrok http 8000`
4. Copy the HTTPS URL
5. Update Vercel: `NEXT_PUBLIC_API_URL=https://abc.ngrok.io/api/v1`
6. Redeploy

ngrok might be more stable for testing.

## Production Solution

For production, deploy your backend to:
- **Railway**: `railway up` (easiest)
- **Render**: Free tier available
- **DigitalOcean**: $5/month droplet

Then you'll have a permanent URL and won't need tunnels.

---

**Current Status:**
- ✅ Backend: Working (8 slots available)
- ✅ Cloudflared: Running
- ⚠️ Dashboard: Needs verification

**Next Step:** Run `test_cloudflare_tunnel.ps1` to diagnose the issue
