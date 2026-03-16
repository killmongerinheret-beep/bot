# Vercel Deployment - Ready to Deploy ✅

**Date**: March 12, 2026  
**Status**: ALL FILES PREPARED - READY FOR DEPLOYMENT

---

## ✅ WHAT'S BEEN PREPARED

### 1. Frontend Configuration Files ✅
- ✅ `frontend/vercel.json` - Vercel build configuration
- ✅ `frontend/.env.production` - Production environment variables
- ✅ `frontend/.gitignore` - Git ignore rules
- ✅ `frontend/README.md` - Deployment instructions

### 2. Backend CORS Configuration ✅
- ✅ Backend already configured to accept Vercel domains
- ✅ Regex pattern: `^https://.*\.vercel\.app$` (all Vercel deployments)
- ✅ CORS credentials enabled
- ✅ CSRF trusted origins configured

### 3. Deployment Scripts ✅
- ✅ `deploy_to_vercel.bat` - Windows deployment script
- ✅ `deploy_to_vercel.sh` - Linux/Mac deployment script
- ✅ `VERCEL_DEPLOYMENT_GUIDE.md` - Complete guide

---

## 🚀 DEPLOYMENT STEPS (SIMPLE)

### Option 1: Automated Script (Recommended)

**Windows:**
```bash
./deploy_to_vercel.bat
```

**Linux/Mac:**
```bash
chmod +x deploy_to_vercel.sh
./deploy_to_vercel.sh
```

This script will:
1. Install dependencies
2. Build the frontend
3. Initialize git (if needed)
4. Add GitHub remote
5. Commit and push to GitHub

### Option 2: Manual Deployment

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install and build
npm install
npm run build

# 3. Initialize git (if not already)
git init
git branch -M main

# 4. Add GitHub remote
git remote add origin https://github.com/killmongerinheret-beep/bot-front.git

# 5. Commit and push
git add .
git commit -m "Deploy to Vercel"
git push -u origin main --force
```

---

## 🌐 VERCEL DASHBOARD SETUP

After pushing to GitHub:

### Step 1: Import Project
1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "Add New Project"
4. Select repository: `killmongerinheret-beep/bot-front`

### Step 2: Configure Project
- **Framework Preset**: Next.js (auto-detected)
- **Root Directory**: `./` (leave empty)
- **Build Command**: `npm run build` (auto-detected)
- **Output Directory**: `.next` (auto-detected)

### Step 3: Add Environment Variable
Click "Environment Variables" and add:

```
Name: NEXT_PUBLIC_API_URL
Value: http://151.25.69.162:8000/api/v1
```

### Step 4: Deploy
Click "Deploy" and wait 2-3 minutes.

---

## 📋 CONFIGURATION DETAILS

### Frontend Environment (.env.production)
```env
NEXT_PUBLIC_API_URL=http://151.25.69.162:8000/api/v1
```

### Vercel Configuration (vercel.json)
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://151.25.69.162:8000/api/:path*"
    }
  ]
}
```

### Backend CORS (settings.py)
```python
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",  # All Vercel deployments
]
CORS_ALLOW_CREDENTIALS = True
```

---

## 🔗 EXPECTED URLS

### After Deployment
- **Production URL**: `https://bot-front-xxx.vercel.app`
- **Preview URLs**: `https://bot-front-git-branch-xxx.vercel.app`
- **Backend API**: `http://151.25.69.162:8000/api/v1`

### Test URLs
- **Login Page**: `https://bot-front-xxx.vercel.app/`
- **Dashboard**: `https://bot-front-xxx.vercel.app/` (after login)
- **API Health**: `http://151.25.69.162:8000/api/v1/health/`

---

## ✅ POST-DEPLOYMENT CHECKLIST

### Immediate Tests
- [ ] Can access Vercel URL
- [ ] Login page loads correctly
- [ ] Can login with test credentials
- [ ] Dashboard loads after login
- [ ] Can see tasks for logged-in agency
- [ ] Can create new monitor
- [ ] Can delete monitor
- [ ] Logout works correctly

### Test Credentials
```
Username: agency-admin
Password: agency-admin

Username: alpha_travel_agency
Password: alphatravelagency

Username: vatican_bot_agency_1
Password: vaticanbotagency1

Username: vatican_bot_agency_2
Password: vaticanbotagency2
```

### API Tests
- [ ] Login API works: `POST /api/v1/auth/login/`
- [ ] Tasks API works: `GET /api/v1/tasks/`
- [ ] Results API works: `GET /api/v1/results/`
- [ ] Session persists on page refresh
- [ ] CORS headers present in responses

---

## 🐛 TROUBLESHOOTING

### Issue: API calls fail with CORS error
**Symptoms**: Console shows "CORS policy" error  
**Solution**: Backend CORS is already configured, but if issues persist:
```bash
# Restart backend to apply CORS changes
docker-compose restart backend
```

### Issue: Environment variable not working
**Symptoms**: API calls go to wrong URL  
**Solution**: 
1. Check environment variable in Vercel dashboard
2. Redeploy after adding/changing variables
3. Verify variable name starts with `NEXT_PUBLIC_`

### Issue: Build fails on Vercel
**Symptoms**: Deployment fails during build  
**Solution**:
1. Check build logs in Vercel dashboard
2. Test build locally: `npm run build`
3. Fix TypeScript/ESLint errors
4. Push fixes to GitHub

### Issue: 404 on page refresh
**Symptoms**: Dashboard works, but refresh gives 404  
**Solution**: This shouldn't happen with Next.js App Router, but if it does:
- Verify `vercel.json` is in the repository
- Check Vercel detected Next.js framework
- Ensure no custom routing conflicts

### Issue: Session not persisting
**Symptoms**: Logged out on page refresh  
**Solution**:
- Check browser localStorage is enabled
- Verify session token is being sent in API headers
- Check backend session hasn't expired (7-day limit)

---

## 🔄 CONTINUOUS DEPLOYMENT

Once connected to Vercel:

### Automatic Deployments
- **Push to `main`**: Triggers production deployment
- **Push to other branches**: Creates preview deployment
- **Pull requests**: Creates preview deployment with unique URL

### Manual Deployments
- Go to Vercel dashboard
- Click "Deployments"
- Click "Redeploy" on any previous deployment

---

## 📊 MONITORING

### Vercel Dashboard Provides
- **Build Logs**: See build output and errors
- **Runtime Logs**: See server-side errors
- **Analytics**: Page views, performance metrics
- **Deployment History**: All previous deployments

### Backend Monitoring
```bash
# Check backend logs
docker-compose logs -f backend

# Check worker logs
docker-compose logs -f worker_vatican

# Check all containers
docker-compose ps
```

---

## 🎯 NEXT STEPS AFTER DEPLOYMENT

### 1. Test Everything
- Login with all test accounts
- Create monitors for different ticket types
- Verify notifications work
- Test multi-tenant isolation

### 2. Update Documentation
- Add production URL to README
- Update API documentation
- Document any deployment issues

### 3. Optional Enhancements
- **Custom Domain**: Add custom domain in Vercel
- **SSL for Backend**: Set up HTTPS for backend API
- **Environment Separation**: Create staging environment
- **Monitoring**: Set up error tracking (Sentry, etc.)

### 4. Security Hardening
- Change default passwords
- Enable rate limiting
- Set up API key authentication
- Configure firewall rules

---

## 📝 IMPORTANT NOTES

### Backend API URL
The backend is currently HTTP (not HTTPS):
```
http://151.25.69.162:8000/api/v1
```

**Recommendation**: Set up SSL/HTTPS for production use:
- Use Let's Encrypt for free SSL
- Configure Nginx with SSL
- Update `NEXT_PUBLIC_API_URL` to HTTPS

### Session Security
- Sessions expire after 7 days
- Stored in Redis cache
- Secure tokens (32-byte URL-safe)
- HTTPS recommended for production

### CORS Configuration
- Backend accepts all `*.vercel.app` domains
- Credentials (cookies) enabled
- Preflight requests handled
- No additional configuration needed

---

## 🚀 DEPLOYMENT COMMAND SUMMARY

```bash
# Quick deployment (Windows)
./deploy_to_vercel.bat

# Quick deployment (Linux/Mac)
chmod +x deploy_to_vercel.sh
./deploy_to_vercel.sh

# Then go to Vercel dashboard and import project
```

---

## ✅ SYSTEM STATUS

**Frontend**: ✅ READY FOR DEPLOYMENT  
**Backend**: ✅ CORS CONFIGURED  
**Scripts**: ✅ CREATED  
**Documentation**: ✅ COMPLETE  
**Configuration**: ✅ VERIFIED

**Next Action**: Run deployment script and import to Vercel!

---

**Last Updated**: March 12, 2026  
**Prepared By**: Kiro AI Assistant  
**Status**: READY TO DEPLOY ✅
