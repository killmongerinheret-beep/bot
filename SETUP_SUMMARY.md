# Vatican Bot 60-Day Monitoring Setup - Complete ✅

## What Was Done

Successfully configured **all 10 agencies** to monitor the next **60 dates** (April 29 - July 7, 2026, excluding Sundays).

## Results

### Agencies Updated:
1. **Agency-admin** - Created new task (ID: 312)
2. **Big bus** - Updated 19 tasks
3. **Italy pass** - Created new task (ID: 313)
4. **Mahabur** - Updated 10 tasks
5. **System Admin** - Created new task (ID: 314)
6. **Tour_guides** - Created new task (ID: 315)
7. **Vatican Bot Agency 1** - Created new task (ID: 316)
8. **Vatican Bot Agency 2** - Created new task (ID: 317)
9. **Wondersofrome** - Updated 61 tasks
10. **WOR** - Updated 6 tasks ✅

### WOR Agency Details:
- **Agency ID**: 14
- **Active Tasks**: 6 tasks
- **Date Coverage**: 60 dates (April 29 - July 7, 2026)
- **Monitoring**: All tasks now check 60 dates every 5 seconds
- **Telegram Group**: -5245239270 (WOR Bot) - correctly assigned

## Monitoring Configuration

Each task is configured with:
- **60 dates** from April 29 to July 7, 2026
- **Sundays excluded** (Vatican closed)
- **Check interval**: 5 seconds (fast monitoring)
- **Notification mode**: available_only (only alerts when tickets become available)
- **Tier**: notify (sends Telegram notifications)

## How to Use the Script

### Run for all agencies:
```bash
# Windows
docker-compose exec backend python setup_60_day_monitoring.py

# Or use the batch file
setup_60_day_monitoring_prod.bat
```

### Run for specific agency:
```bash
docker-compose exec backend python setup_60_day_monitoring.py --agency-id 14
```

### Preview changes (dry-run):
```bash
docker-compose exec backend python setup_60_day_monitoring.py --dry-run
```

### Consolidate multiple tasks into one per agency:
```bash
docker-compose exec backend python setup_60_day_monitoring.py --consolidate
```

### Include Sundays:
```bash
docker-compose exec backend python setup_60_day_monitoring.py --include-sundays
```

## Script Features

✅ **Automatic date generation** - Calculates next 60 dates from today
✅ **Sunday exclusion** - Skips Sundays (Vatican closed)
✅ **Smart updates** - Updates existing tasks or creates new ones
✅ **Consolidation option** - Can merge multiple tasks into one
✅ **Dry-run mode** - Preview changes before applying
✅ **Agency filtering** - Can target specific agencies
✅ **Production-ready** - Runs inside Docker with production database

## Monitoring Status

The bot is now actively monitoring:
- **10 agencies**
- **60 dates** per agency
- **Every 5 seconds**
- **Parallel processing** (all dates checked simultaneously)

Expected notification latency: **5-8 seconds** from ticket release to Telegram alert.

## Files Created

1. `setup_60_day_monitoring.py` - Main script (also copied to backend/)
2. `setup_60_day_monitoring_prod.bat` - Windows batch file for easy execution
3. `setup_60_day_monitoring_prod.sh` - Linux/Mac shell script
4. `SETUP_SUMMARY.md` - This summary document

## Next Steps

The monitoring is now active. To verify it's working:

```bash
# Check recent monitoring activity
docker-compose logs worker_vatican --tail 50

# Check WOR's telegram notifications
docker-compose logs telegram_bot --tail 50 | grep -i "wor"

# View task status in database
docker-compose exec -T db psql -U postgres -d ticketbot -c "SELECT id, last_checked, last_status FROM monitors_monitortask WHERE agency_id = 14 AND is_active = true;"
```

## Maintenance

To update dates in the future, simply run the script again:
```bash
docker-compose exec backend python setup_60_day_monitoring.py
```

The script will automatically:
- Calculate the next 60 dates from the current date
- Update all existing tasks
- Maintain existing configurations (visitors, tier, etc.)

---

**Setup completed**: April 28, 2026 at 15:02 UTC+2
**Script location**: `backend/setup_60_day_monitoring.py`
**Status**: ✅ All agencies configured and monitoring active
