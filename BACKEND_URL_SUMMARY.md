# Backend URL Summary for Vercel Dashboard

## ✅ Backend Status: RUNNING

**Local URL**: `http://localhost:8000`  
**API Base**: `/api/v1/`  
**Docker Container**: `travelagenntbot-backend-1`

## 📊 Current Tasks (Live Data)

### Task #18 - ✅ AVAILABLE
- **Date**: March 28, 2026
- **Visitors**: 1
- **Status**: `available`
- **Slots Found**: 9 slots
- **Available Times**: 09:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 14:30, 15:00
- **Last Checked**: 12:18 PM (10 minutes ago)
- **Ticket**: Musei Vaticani - Biglietti d'ingresso

### Task #15 - ❌ SOLD OUT
- **Date**: March 26, 2026
- **Visitors**: 2
- **Status**: `sold_out`
- **Last Checked**: 12:16 PM

### Task #19 - ❌ SOLD OUT
- **Date**: March 16, 2026
- **Visitors**: 1
- **Status**: `sold_out`
- **Last Checked**: 12:16 PM

## 🎯 What You Need to Do

### Step 1: Install ngrok (5 minutes)

Download from: https://ngrok.com/download

**Windows**:
1. Download `ngrok-v3-stable-windows-amd64.zip`
2. Extract to a folder (e.g., `C:\ngrok`)
3. Add to PATH or run from that folder

### Step 2: Start ngrok

Open a new terminal and run:
```bash
ngrok http 8000
```

You'll see output like:
```
Session Status                online
Account                       [your-email]
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Copy this URL**: `https://abc123.ngrok.io`

### Step 3: Test ngrok URL

Open in browser:
```
https://abc123.ngrok.io/api/v1/tasks/
```

You should see JSON with your 3 tasks.

### Step 4: Update Vercel

1. Go to **Vercel Dashboard**: https://vercel.com/dashboard
2. Select your project
3. Click **Settings** (top menu)
4. Click **Environment Variables** (left sidebar)
5. Add or update:
   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://abc123.ngrok.io/api/v1
   ```
   (Replace `abc123` with your actual ngrok URL)
6. Click **Save**

### Step 5: Redeploy Frontend

1. Go to **Deployments** tab
2. Click the **...** menu on the latest deployment
3. Click **Redeploy**
4. Wait for deployment to complete (~2 minutes)

### Step 6: Verify Dashboard

Visit your Vercel app URL. You should now see:

```
┌─────────────────────────────────────────────┐
│ Task #18 - Agency-admin                     │
├─────────────────────────────────────────────┤
│ Date: March 28, 2026                        │
│ Visitors: 1                                 │
│                                             │
│ Status: ✅ AVAILABLE                        │
│ Slots: 9 available                          │
│                                             │
│ Times: 09:30, 10:00, 10:30, 11:00...       │
│                                             │
│ Last Checked: 10 minutes ago                │
└─────────────────────────────────────────────┘
```

## 🔍 Verification Checklist

- [ ] ngrok installed and running
- [ ] ngrok URL copied (https://xxx.ngrok.io)
- [ ] Tested ngrok URL in browser (shows JSON)
- [ ] Updated NEXT_PUBLIC_API_URL in Vercel
- [ ] Redeployed frontend in Vercel
- [ ] Dashboard shows tasks (not "unknown")
- [ ] Task #18 shows "available" with 9 slots
- [ ] Tasks #15 and #19 show "sold_out"

## 🐛 Troubleshooting

### ngrok URL returns 404

**Problem**: Wrong API path  
**Solution**: Make sure URL ends with `/api/v1/tasks/` not `/api/tasks/`

### Dashboard still shows "unknown"

**Problem**: Environment variable not set or frontend not redeployed  
**Solution**: 
1. Check Vercel Settings → Environment Variables
2. Make sure `NEXT_PUBLIC_API_URL` is set
3. Redeploy frontend

### CORS errors in browser console

**Problem**: Backend not allowing Vercel domain  
**Solution**: Add to `backend/core/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "https://*.ngrok.io",
]
```

Then restart:
```bash
docker-compose restart backend
```

### ngrok tunnel closed

**Problem**: ngrok free tier closes after 2 hours  
**Solution**: 
- Restart ngrok (URL will change)
- Update Vercel environment variable with new URL
- Redeploy frontend

**Better solution**: Deploy to Railway/Render for permanent URL

## 📱 API Endpoints Reference

All endpoints use base URL: `https://your-ngrok-url.ngrok.io/api/v1/`

### Get All Tasks
```
GET /api/v1/tasks/
```

Response:
```json
[
  {
    "id": 18,
    "agency_name": "Agency-admin",
    "site": "vatican",
    "dates": ["2026-03-28"],
    "visitors": 1,
    "last_status": "available",
    "last_checked": "2026-02-28T12:18:32.474209Z",
    "latest_check": {
      "status": "available",
      "details": {
        "slots": ["09:30", "10:00", "10:30", ...]
      }
    }
  }
]
```

### Get Single Task
```
GET /api/v1/tasks/{id}/
```

### Get Agencies
```
GET /api/v1/agencies/
```

### Get Check Results
```
GET /api/v1/results/?task={task_id}
```

## 🚀 Next Steps

### For Testing (Now)
✅ Use ngrok - Quick and easy

### For Production (Later)
1. Deploy backend to Railway/Render/DigitalOcean
2. Get permanent URL
3. Update Vercel with permanent URL
4. Set up custom domain (optional)

## 📚 Related Files

- `QUICK_START_VERCEL.md` - Quick start guide
- `VERCEL_DASHBOARD_SETUP.md` - Detailed setup guide
- `DASHBOARD_VERIFICATION_GUIDE.md` - Verification steps
- `get_backend_url.ps1` - PowerShell script to check backend
- `start_ngrok.bat` - Windows batch script to start ngrok

## 💡 Pro Tips

1. **Keep ngrok running**: Don't close the terminal window
2. **Bookmark ngrok URL**: You'll need it if you restart
3. **Monitor logs**: Watch Docker logs to see checks happening
4. **Test locally first**: Always test `localhost:8000` before ngrok
5. **Use ngrok web interface**: Visit `http://localhost:4040` to see requests

## 🎉 Success Criteria

Your dashboard is working correctly when:
- ✅ Tasks show "available" or "sold_out" (not "unknown")
- ✅ Slot counts are displayed
- ✅ Last checked time is recent
- ✅ Available time slots are listed
- ✅ Status updates when you refresh

---

**Current Time**: February 28, 2026, 12:28 PM  
**Backend**: Running in Docker  
**Tasks**: 3 active (1 available, 2 sold out)  
**Next Action**: Install ngrok and get public URL
