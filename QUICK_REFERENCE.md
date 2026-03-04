# Vatican Bot - Quick Reference Card

## 🚀 Quick Start

```powershell
# 1. Restart worker (applies fixes)
docker-compose restart worker_vatican

# 2. Check health
.\quick_vatican_check.ps1

# 3. Watch logs
docker-compose logs -f worker_vatican
```

---

## 📋 Mandatory Flow (3 Steps)

### Step 1: Deep Link (Get Cookies + IDs)
```
https://tickets.museivaticani.va/home/fromtag/{visitors}/{timestamp_ms}/{slug}/1
```

**Example:**
```
# 2 visitors, March 28, 2026, standard ticket
https://tickets.museivaticani.va/home/fromtag/2/1774652400000/MV-Biglietti/1
```

### Step 2: Match Ticket by Name
```python
# 3-tier strategy:
# 1. Exact substring match
# 2. Keyword scoring (musei, biglietti, ingresso)
# 3. Smart fallback (first standard ticket)
```

### Step 3: Call API
```
https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={fresh_id}&visitorNum={visitors}&visitDate={DD/MM/YYYY}

# Add visitLang ONLY for guided tours:
&visitLang=ENG
```

---

## ✅ Success Indicators

```
✅ Keyword Match: 'Musei Vaticani' -> ID 2129030053
✅ API Response: 200 - 20 total slots
✅ Found 9 available slots
```

---

## ❌ Failure Indicators

```
❌ No name match for 'Musei Vaticani'
❌ API call failed: Status 500
❌ Falling back to stale ID (Risky)
```

---

## 🔧 Quick Fixes

### Issue: Name matching fails
```powershell
docker cp fix_vatican_ticket_names.py travelagenntbot-backend-1:/app/
docker-compose exec backend python /app/fix_vatican_ticket_names.py
docker-compose restart worker_vatican
```

### Issue: Worker not running
```powershell
docker-compose restart worker_vatican
```

### Issue: API 500 errors
```powershell
# Clear stale IDs
docker-compose exec backend python /app/fix_vatican_ticket_names.py
```

---

## 📊 Monitoring Commands

```powershell
# Health check
.\quick_vatican_check.ps1

# Live logs
docker-compose logs -f worker_vatican

# Recent errors
docker-compose logs --tail=100 worker_vatican | Select-String "ERROR|500"

# Recent successes
docker-compose logs --tail=100 worker_vatican | Select-String "Keyword Match|Found.*slots"

# Compliance check
python verify_vatican_rules_compliance.py
```

---

## 🎯 Key Rules

1. ✅ ALWAYS use dynamic IDs (never hardcoded)
2. ✅ Navigate to deep link FIRST
3. ✅ Match tickets by NAME (not ID)
4. ✅ Use Rome timezone for timestamps
5. ✅ visitLang ONLY for guided tours
6. ✅ Consistent visitor count everywhere

---

## 📚 Documentation

- **Rules:** `.kiro/steering/VATICAN_BOT_RULES.md`
- **Status:** `VATICAN_BOT_STATUS_REPORT.md`
- **Fixes:** `VATICAN_BOT_FIX_APPLIED.md`
- **Compliance:** `VATICAN_RULES_IMPLEMENTATION_STATUS.md`
- **Summary:** `VATICAN_BOT_FINAL_SUMMARY.md`

---

## 🆘 Emergency Commands

```powershell
# Stop everything
docker-compose down

# Start fresh
docker-compose up -d

# Check all services
docker-compose ps

# Full logs
docker-compose logs > full_logs.txt
```

---

**Quick Status Check:**
```powershell
docker-compose ps worker_vatican && echo "✅ Worker is running" || echo "❌ Worker is down"
```
