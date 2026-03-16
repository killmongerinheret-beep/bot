# Quick Deploy to Vercel - 3 Steps

## Step 1: Push to GitHub (2 minutes)

**Windows:**
```bash
./deploy_to_vercel.bat
```

**Linux/Mac:**
```bash
chmod +x deploy_to_vercel.sh
./deploy_to_vercel.sh
```

## Step 2: Import to Vercel (1 minute)

1. Go to https://vercel.com
2. Click "Add New Project"
3. Select: `killmongerinheret-beep/bot-front`
4. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=http://151.25.69.162:8000/api/v1
   ```
5. Click "Deploy"

## Step 3: Test (1 minute)

1. Open your Vercel URL: `https://bot-front-xxx.vercel.app`
2. Login with: `agency-admin` / `agency-admin`
3. Verify dashboard loads

## Done! 🎉

Your frontend is now live on Vercel with:
- ✅ Authentication working
- ✅ Multi-tenant isolation
- ✅ Vatican monitoring
- ✅ Real-time updates
- ✅ Automatic deployments on git push

## Need Help?

See `VERCEL_DEPLOYMENT_READY.md` for detailed instructions and troubleshooting.
