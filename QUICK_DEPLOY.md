# ⚡ QUICK DEPLOY - Vatican Bot Frontend

## 🚀 Deploy Now (Choose One):

### Option 1: PowerShell Script (Easiest)
```powershell
.\deploy_frontend.ps1
```

### Option 2: Vercel CLI (Fastest)
```bash
cd frontend
vercel --prod
```

### Option 3: Git Push (Auto)
```bash
git push origin main
```

---

## ✅ After Deployment:

### Test Standard Ticket:
1. Open dashboard
2. New Monitor → Vatican → Standard Entry
3. Verify: No language field shown
4. Submit and check: `language=null` in DB

### Test Guided Tour:
1. New Monitor → Vatican → Guided Tours
2. Verify: Language selector visible
3. Select language and submit
4. Check: `language='ENG'` in DB

### Verify Bot:
```bash
# Check logs
docker-compose logs worker_vatican | grep "Lang:" | tail -10

# Run test
python test_new_monitor_creation.py
```

---

## 📊 Expected Results:

✅ Standard tickets: `Lang: None` in logs  
✅ Guided tours: `Lang: ENG` in logs  
✅ API Status: 200  
✅ Slots found: > 0  

---

## 🆘 If Issues:

1. Clear browser cache (Ctrl+Shift+R)
2. Check Vercel deployment logs
3. Verify backend is running
4. See `VERCEL_DEPLOYMENT_GUIDE.md` for details

---

**Status:** ✅ READY  
**Build:** ✅ SUCCESS  
**Risk:** 🟢 LOW
