# Fix Now - Manual Commands

The PowerShell scripts are having syntax issues. Just run these commands manually:

## Step 1: Restart Worker

```powershell
docker-compose restart worker_vatican
```

## Step 2: Wait 15 seconds

```powershell
Start-Sleep -Seconds 15
```

## Step 3: Check logs

```powershell
docker-compose logs --tail=30 worker_vatican
```

Look for:
- ❌ If you see "Missing visit_date or visitors" → Go to Step 4
- ✅ If you DON'T see that error → Go to Step 5

## Step 4: If error still present - Recreate container

```powershell
docker-compose stop worker_vatican
docker-compose rm -f worker_vatican
docker-compose up -d worker_vatican
Start-Sleep -Seconds 15
docker-compose logs --tail=30 worker_vatican
```

## Step 5: Trigger check

```powershell
docker-compose exec backend python manage.py shell
```

Then in the shell, type:
```python
from monitors.tasks import orchestrate_all_tasks
orchestrate_all_tasks()
exit()
```

## Step 6: Monitor logs

```powershell
docker-compose logs -f worker_vatican
```

Press `Ctrl+C` to stop.

Look for:
- ✅ `/fromtag/1/...` (correct visitor count)
- ✅ `visitorNum=1` (in API calls)
- ✅ `Smart Group: .../1v`
- ✅ `Found X slots` or availability messages
- ❌ No "Missing visit_date or visitors" errors

## Step 7: Wait and check dashboard

1. Wait 2-3 minutes for checks to complete
2. Open: http://localhost:8000/api/tasks/
3. Check if you see task data with slots
4. Open: https://bot-pl2x.vercel.app/
5. Hard refresh: `Ctrl + Shift + R`

---

## If Dashboard Still Shows Sold Out

The bot is working but dashboard can't connect. Check:

1. **Is Cloudflare tunnel running?**
   ```powershell
   docker-compose ps
   ```
   Look for cloudflare or tunnel service

2. **Test tunnel URL:**
   Open in browser: `https://your-tunnel-url.trycloudflare.com/api/tasks/`
   
   Should show same data as `http://localhost:8000/api/tasks/`

3. **Check Vercel environment variables:**
   - Go to Vercel project settings
   - Environment Variables
   - Verify `NEXT_PUBLIC_API_URL` = your tunnel URL

---

## Quick Summary

```powershell
# Restart worker
docker-compose restart worker_vatican

# Wait
Start-Sleep -Seconds 15

# Check logs
docker-compose logs --tail=30 worker_vatican

# If no error, trigger check
docker-compose exec backend python manage.py shell
# Then: from monitors.tasks import orchestrate_all_tasks; orchestrate_all_tasks(); exit()

# Monitor
docker-compose logs -f worker_vatican
```

That's it! The fix is already in the code, we just need the worker to reload it.
