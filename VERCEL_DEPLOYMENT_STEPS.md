# 🚀 Vercel Deployment Steps

**Current Issue:** Frontend showing "Unknown" status  
**Solution:** Deploy updated frontend to Vercel

---

## 📋 Prerequisites

1. ✅ Frontend built successfully
2. ⚠️  Need to login to Vercel
3. ⚠️  Need to deploy to production

---

## 🔧 Step-by-Step Deployment

### Option 1: Using Vercel CLI (Recommended)

#### Step 1: Login to Vercel
```powershell
cd frontend
vercel login
```

This will:
- Open your browser
- Ask you to login to Vercel
- Generate an authentication token

#### Step 2: Link Project (if not already linked)
```powershell
vercel link
```

Select:
- Your Vercel account
- The existing project: `bot-pl2x`

#### Step 3: Deploy to Production
```powershell
vercel --prod
```

This will:
- Upload your built files
- Deploy to production
- Update https://bot-pl2x.vercel.app/

---

### Option 2: Using Vercel Dashboard (Alternative)

#### Step 1: Push to Git
```powershell
git add .
git commit -m "Fix: Updated frontend with language fixes"
git push
```

#### Step 2: Trigger Deployment
1. Go to https://vercel.com/dashboard
2. Find your project: `bot-pl2x`
3. Click "Deployments"
4. Click "Redeploy" on the latest deployment
5. Or wait for automatic deployment from Git

---

### Option 3: Manual Upload (Quick Fix)

If you need immediate deployment:

#### Step 1: Build Frontend
```powershell
cd frontend
npm run build
```

#### Step 2: Upload via Vercel Dashboard
1. Go to https://vercel.com/dashboard
2. Click your project: `bot-pl2x`
3. Click "Settings" → "General"
4. Scroll to "Build & Development Settings"
5. Verify settings:
   - Framework Preset: `Next.js`
   - Build Command: `npm run build`
   - Output Directory: `.next`

#### Step 3: Trigger New Deployment
1. Go to "Deployments" tab
2. Click "..." menu on latest deployment
3. Click "Redeploy"
4. Select "Use existing Build Cache" = NO
5. Click "Redeploy"

---

## 🔍 What Changed

The following files were updated and need to be deployed:

### 1. TaskModal.tsx
**Change:** Removed hardcoded 'ENG' fallback
```typescript
// Before:
languageValue = selectedLanguage || formData.language || 'ENG';

// After:
languageValue = selectedLanguage || formData.language || null;
```

### 2. All Extraction Logic
**Change:** Improved DOM traversal for ticket extraction
- Searches 10 parent levels (was 5)
- Bidirectional matching (titles ↔ buttons)
- Better handling of complex Angular structures

---

## ✅ Verification After Deployment

### 1. Check Frontend Status
Visit: https://bot-pl2x.vercel.app/

Expected:
- ✅ Tasks should show proper status (not "Unknown")
- ✅ Available slots should be displayed
- ✅ Last checked time should be recent

### 2. Check Task Creation
1. Click "New Monitor"
2. Select "Vatican Museums"
3. Select "Standard Entry (Biglietti)"
4. Add a date
5. Submit

Expected:
- ✅ Language should be `null` (not 'ENG')
- ✅ Task should be created successfully

### 3. Check API Connection
Open browser console (F12) and check:
- ✅ No CORS errors
- ✅ API calls to backend successful
- ✅ Data loading correctly

---

## 🐛 Troubleshooting

### Issue: "Unknown" Status Still Showing

**Cause:** Frontend cache or old deployment

**Solution:**
1. Hard refresh: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
2. Clear browser cache
3. Try incognito/private window
4. Verify deployment timestamp in Vercel dashboard

### Issue: API Connection Failed

**Cause:** Backend URL not configured

**Solution:**
1. Check Vercel environment variables
2. Go to Project Settings → Environment Variables
3. Verify `NEXT_PUBLIC_API_URL` is set to your backend URL
4. Redeploy after updating

### Issue: Build Failed

**Cause:** TypeScript errors or missing dependencies

**Solution:**
```powershell
cd frontend
npm install
npm run build
```

Check for errors and fix them before deploying.

---

## 📊 Current Configuration

### Vercel Project:
- **Name:** bot-pl2x
- **URL:** https://bot-pl2x.vercel.app/
- **Framework:** Next.js 16.1.4
- **Node Version:** 18.x or higher

### Environment Variables Needed:
```
NEXT_PUBLIC_API_URL=<your-backend-url>
```

Example:
```
NEXT_PUBLIC_API_URL=https://your-backend.com/api/v1
```

Or for local backend:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 🚀 Quick Deploy Command

If you're already logged in and linked:

```powershell
cd frontend
npm run build && vercel --prod
```

This will:
1. Build the frontend
2. Deploy to production
3. Update your live site

---

## 📝 Post-Deployment Checklist

After deployment:

- [ ] Visit https://bot-pl2x.vercel.app/
- [ ] Verify tasks show correct status (not "Unknown")
- [ ] Check available slots are displayed
- [ ] Test creating a new monitor
- [ ] Verify language is `null` for standard tickets
- [ ] Check browser console for errors
- [ ] Test on mobile device

---

## 🎯 Expected Result

After successful deployment:

### Before:
```
Task Status: Unknown
Available Slots: Not shown
Last Checked: Never
```

### After:
```
Task Status: Available / Sold Out / Closed
Available Slots: 09:00, 09:30, 10:00... (if available)
Last Checked: 2 minutes ago
```

---

## 💡 Tips

1. **Always build before deploying:**
   ```powershell
   npm run build
   ```
   This catches errors before deployment.

2. **Use production flag:**
   ```powershell
   vercel --prod
   ```
   This deploys to your production URL, not a preview URL.

3. **Check deployment logs:**
   - Go to Vercel dashboard
   - Click on deployment
   - View build logs for errors

4. **Test locally first:**
   ```powershell
   npm run dev
   ```
   Visit http://localhost:3000 to test changes.

---

## 🆘 Need Help?

If deployment fails:

1. Check Vercel dashboard for error messages
2. Review build logs
3. Verify environment variables
4. Test build locally: `npm run build`
5. Check Node.js version compatibility

---

**Ready to deploy?** Run:
```powershell
cd frontend
vercel login
vercel --prod
```

Good luck! 🚀
