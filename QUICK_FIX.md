# Quick Fix: Dashboard Shows Wrong Status

## The Problem
✅ Backend has 8 slots available  
❌ Dashboard shows "sold out"

## The Solution (5 minutes)

### 1. Get Cloudflare URL
Look at your cloudflared terminal, find the URL:
```
https://abc-xyz-123.trycloudflare.com
```

### 2. Test It
```powershell
powershell -ExecutionPolicy Bypass -File test_cloudflare_tunnel.ps1
```

### 3. Update Vercel
```
Settings → Environment Variables
NEXT_PUBLIC_API_URL = https://your-url.trycloudflare.com/api/v1
```

### 4. Redeploy
```
Deployments → ... → Redeploy
```

### 5. Clear Cache
```
Ctrl+Shift+Delete or Ctrl+F5
```

## Done!
Dashboard should now show 8 available slots.

---

**Still not working?** Read `FIX_SOLD_OUT_ISSUE.md` for detailed troubleshooting.
