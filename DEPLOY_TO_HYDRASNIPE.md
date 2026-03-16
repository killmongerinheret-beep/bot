# Deploy Multi-Tenant Dashboard to hydrasnipe.it 🚀

**Domain:** https://hydrasnipe.it/  
**Public IP:** 151.25.69.162  
**Status:** ✅ READY FOR DEPLOYMENT

---

## 🎯 DEPLOYMENT COMPLETED

### ✅ What's Been Done:

1. **Frontend Built for Production**
   - Static files generated in `frontend/out/` folder
   - API configured to use your public IP (151.25.69.162:8000)
   - Production environment configured

2. **Backend Configured for Public Access**
   - CORS updated to allow hydrasnipe.it domain
   - Docker exposed on 0.0.0.0:8000 (all interfaces)
   - Backend restarted with new configuration

3. **Multi-Tenant System Ready**
   - Agency selection screen
   - Separate dashboards per agency
   - Telegram integration per agency

---

## 📁 DEPLOYMENT FILES READY

### Static Files Location:
```
frontend/out/
├── index.html          (Main page)
├── _next/              (Next.js assets)
├── admin/              (Admin pages)
├── favicon.ico
└── [other assets]
```

**These files are ready to upload to hydrasnipe.it!**

---

## 🚀 DEPLOYMENT STEPS

### Option 1: Upload via FTP/cPanel (Recommended)

1. **Zip the files:**
   ```bash
   cd frontend/out
   # Create a zip of all files
   ```

2. **Upload to hydrasnipe.it:**
   - Login to your hosting control panel (cPanel, etc.)
   - Navigate to File Manager or FTP
   - Go to `public_html` or `www` folder
   - **Backup existing files first!**
   - Upload and extract all files from `frontend/out/`

3. **Test the deployment:**
   - Visit https://hydrasnipe.it/
   - Should show agency selection screen

### Option 2: Upload via FTP Client

```bash
# Using WinSCP, FileZilla, or similar:
# 1. Connect to your hydrasnipe.it server
# 2. Navigate to public_html folder
# 3. Upload all contents of frontend/out/ folder
# 4. Replace existing files
```

---

## 🔧 BACKEND ACCESS CONFIGURATION

### Current Status:
- ✅ Backend running on localhost:8000
- ✅ CORS configured for hydrasnipe.it
- ❓ Public IP access needs verification

### If Public IP Not Accessible:

**Option A: Router Port Forwarding**
1. Access your router admin panel (usually 192.168.1.1)
2. Find "Port Forwarding" or "Virtual Server"
3. Add rule: External Port 8000 → Internal IP:8000
4. Save and restart router

**Option B: Windows Firewall**
```bash
# Allow port 8000 through Windows Firewall
netsh advfirewall firewall add rule name="Django Backend" dir=in action=allow protocol=TCP localport=8000
```

**Option C: Use Cloudflare Tunnel (Alternative)**
```bash
# Install cloudflared
# Create tunnel to expose localhost:8000
cloudflared tunnel --url http://localhost:8000
# Use the generated URL in frontend configuration
```

---

## 🧪 TESTING THE DEPLOYMENT

### 1. Test Frontend
```bash
# Visit https://hydrasnipe.it/
# Should show:
# - Agency selection screen
# - Modern dark UI
# - "Create New Agency" option
```

### 2. Test API Connection
```bash
# Open browser console on hydrasnipe.it
# Check Network tab for API calls
# Should see requests to: http://151.25.69.162:8000/api/v1/
```

### 3. Test Agency Creation
```bash
# 1. Click "Create New Agency"
# 2. Enter agency name
# 3. Should create successfully
# 4. Should redirect to agency dashboard
```

---

## 🔄 FALLBACK OPTIONS

### If Public IP Doesn't Work:

**Option 1: Use Existing Domain Backend**
```typescript
// Update frontend/src/lib/api.ts
if (hostname === 'hydrasnipe.it') {
    return 'https://hydrasnipe.it/api/v1';  // Use same domain
}
```

**Option 2: Use Cloudflare Tunnel**
```bash
# Create tunnel for backend
cloudflared tunnel --url http://localhost:8000
# Update API URL to tunnel URL
```

**Option 3: Deploy Backend to Same Server**
```bash
# Upload backend code to hydrasnipe.it server
# Configure Python/Django on hosting
# Use same domain for both frontend and backend
```

---

## 📊 WHAT USERS WILL SEE

### New Multi-Tenant Experience:

1. **Landing Page:** Agency selection screen
2. **Agency Dashboard:** Separate data per agency
3. **Agency Switcher:** Switch between agencies
4. **Telegram Integration:** Per-agency notifications
5. **Plan Limits:** Free (2 tasks), Pro (10 tasks), Agency (50 tasks)

### Compared to Old System:
- ❌ Old: Single agency, basic UI
- ✅ New: Multi-agency, modern UI, better organization

---

## 🎯 IMMEDIATE NEXT STEPS

### 1. Upload Frontend (5 minutes)
```bash
# 1. Backup current hydrasnipe.it files
# 2. Upload contents of frontend/out/ folder
# 3. Test https://hydrasnipe.it/
```

### 2. Verify Backend Access
```bash
# Test from external network:
curl http://151.25.69.162:8000/api/v1/agencies/
# If fails, configure port forwarding
```

### 3. Test Complete Flow
```bash
# 1. Visit hydrasnipe.it
# 2. Create new agency
# 3. Add monitoring task
# 4. Verify Telegram notifications
```

---

## 🚨 TROUBLESHOOTING

### Frontend Shows Blank Page
- Check browser console for errors
- Verify all files uploaded correctly
- Check index.html exists in root

### API Connection Fails
- Verify backend is running: `docker-compose ps`
- Test local API: `curl http://localhost:8000/api/v1/agencies/`
- Check CORS settings in backend/core/settings.py

### Agencies Not Loading
- Check Network tab in browser
- Verify API URL in console
- Test API endpoint directly

### Telegram Not Working
- Verify bot token in environment
- Check telegram_bot container: `docker-compose logs telegram_bot`
- Test bot manually: `/start` command

---

## 📞 SUPPORT COMMANDS

### Check System Status
```bash
# All containers running
docker-compose ps

# Backend logs
docker-compose logs backend

# API test
curl http://localhost:8000/api/v1/agencies/

# Frontend build
cd frontend && npm run build
```

### Reset if Needed
```bash
# Restart all services
docker-compose restart

# Rebuild frontend
cd frontend && npm run build

# Clear browser cache and test
```

---

## 🎉 DEPLOYMENT SUMMARY

**Status:** ✅ Ready for deployment  
**Files:** Static files built in `frontend/out/`  
**Backend:** Configured for hydrasnipe.it  
**Next Step:** Upload files to hydrasnipe.it server  

**The multi-tenant Vatican monitoring system is ready to replace your existing dashboard!**

---

**Need help with the upload process? Let me know your hosting setup (cPanel, FTP, etc.) and I can provide specific instructions!** 🚀