#!/usr/bin/env python
"""
Comprehensive System Verification
Checks all tasks, monitors, queues, and system health
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, CheckResult, Agency, Proxy
from django.utils import timezone
from django_celery_beat.models import PeriodicTask
import redis

print("=" * 80)
print("COMPREHENSIVE SYSTEM VERIFICATION")
print("=" * 80)
print(f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
print()

# ============================================================================
# 1. DOCKER SERVICES STATUS
# ============================================================================
print("1. DOCKER SERVICES")
print("-" * 80)
import subprocess
try:
    result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
    services = result.stdout
    print(services)
except Exception as e:
    print(f"❌ Error checking services: {e}")
print()

# ============================================================================
# 2. REDIS QUEUE STATUS
# ============================================================================
print("2. REDIS QUEUE STATUS")
print("-" * 80)
try:
    redis_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    r = redis.from_url(redis_url)
    
    queues = ['vatican', 'colosseum', 'celery']
    for queue in queues:
        length = r.llen(queue)
        status = "✅ Healthy" if length < 100 else "⚠️ BACKED UP"
        print(f"  {queue:15} {length:6} tasks  {status}")
    
    # Check cache keys
    resolving_keys = r.keys('resolving:*')
    print(f"\n  Active resolution locks: {len(resolving_keys)}")
    
except Exception as e:
    print(f"❌ Error checking Redis: {e}")
print()

# ============================================================================
# 3. PERIODIC TASKS STATUS
# ============================================================================
print("3. PERIODIC TASKS")
print("-" * 80)
try:
    periodic_tasks = PeriodicTask.objects.all()
    for task in periodic_tasks:
        status = "✅" if task.enabled else "❌"
        schedule = task.interval or task.crontab
        last_run = task.last_run_at.strftime('%H:%M:%S') if task.last_run_at else 'Never'
        print(f"  {status} {task.name:35} | {str(schedule):25} | Last: {last_run}")
except Exception as e:
    print(f"❌ Error checking periodic tasks: {e}")
print()

# ============================================================================
# 4. MONITOR TASKS STATUS
# ============================================================================
print("4. MONITOR TASKS STATUS")
print("-" * 80)
try:
    all_tasks = MonitorTask.objects.all()
    active_tasks = all_tasks.filter(is_active=True)
    
    print(f"  Total tasks: {all_tasks.count()}")
    print(f"  Active tasks: {active_tasks.count()}")
    print(f"  Inactive tasks: {all_tasks.filter(is_active=False).count()}")
    print()
    
    # Group by site
    vatican_tasks = active_tasks.filter(site='vatican')
    colosseum_tasks = active_tasks.filter(site='colosseum')
    
    print(f"  Vatican tasks: {vatican_tasks.count()}")
    print(f"  Colosseum tasks: {colosseum_tasks.count()}")
    print()
    
    # Check last_checked status
    now = timezone.now()
    never_checked = active_tasks.filter(last_checked__isnull=True)
    recently_checked = active_tasks.filter(last_checked__gte=now - timedelta(minutes=5))
    stale_checked = active_tasks.filter(last_checked__lt=now - timedelta(hours=1))
    
    print(f"  ✅ Recently checked (< 5 min): {recently_checked.count()}")
    print(f"  ⚠️ Never checked: {never_checked.count()}")
    print(f"  ⚠️ Stale (> 1 hour): {stale_checked.count()}")
    
    if never_checked.exists():
        print("\n  Tasks never checked:")
        for task in never_checked:
            print(f"    • Task #{task.id}: {task.dates[0] if task.dates else 'No date'} - {task.ticket_name}")
            print(f"      ticket_id: {task.ticket_id or 'None'}, visitors: {task.visitors}")
    
except Exception as e:
    print(f"❌ Error checking monitor tasks: {e}")
print()

# ============================================================================
# 5. TASKS WITHOUT TICKET_ID
# ============================================================================
print("5. TASKS WITHOUT TICKET_ID")
print("-" * 80)
try:
    tasks_no_id = active_tasks.filter(ticket_id__isnull=True)
    print(f"  Total: {tasks_no_id.count()}")
    
    if tasks_no_id.exists():
        print("\n  Details:")
        for task in tasks_no_id:
            print(f"    • Task #{task.id}: {task.ticket_name}")
            print(f"      Date: {task.dates[0] if task.dates else 'None'}")
            print(f"      Visitors: {task.visitors}")
            print(f"      Times: {task.preferred_times}")
            print(f"      Last status: {task.last_status}")
            print()
    else:
        print("  ✅ All tasks have ticket_id")
        
except Exception as e:
    print(f"❌ Error: {e}")
print()

# ============================================================================
# 6. RECENT CHECK RESULTS
# ============================================================================
print("6. RECENT CHECK RESULTS (Last 10)")
print("-" * 80)
try:
    recent_results = CheckResult.objects.all().order_by('-check_time')[:10]
    
    for result in recent_results:
        time_str = result.check_time.strftime('%H:%M:%S')
        status_icon = "✅" if result.status == 'available' else "❌" if result.status == 'sold_out' else "⚠️"
        print(f"  {status_icon} Task #{result.task.id:3} | {time_str} | {result.status:10} | {result.task.ticket_name[:40]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
print()

# ============================================================================
# 7. PROXY STATUS
# ============================================================================
print("7. PROXY STATUS")
print("-" * 80)
try:
    proxies = Proxy.objects.all()
    active_proxies = proxies.filter(is_active=True)
    
    print(f"  Total proxies: {proxies.count()}")
    print(f"  Active proxies: {active_proxies.count()}")
    print()
    
    # Check cooldown status
    now = timezone.now()
    on_cooldown = active_proxies.filter(cooldown_until__gt=now)
    available = active_proxies.filter(cooldown_until__isnull=True) | active_proxies.filter(cooldown_until__lte=now)
    
    print(f"  ✅ Available: {available.count()}")
    print(f"  ⏳ On cooldown: {on_cooldown.count()}")
    
    if on_cooldown.exists():
        print("\n  Proxies on cooldown:")
        for proxy in on_cooldown:
            time_left = (proxy.cooldown_until - now).total_seconds() / 60
            print(f"    • {proxy.ip_port[:30]:30} | {time_left:.1f} min left | Failures: {proxy.consecutive_failures}")
    
except Exception as e:
    print(f"❌ Error: {e}")
print()

# ============================================================================
# 8. AGENCIES
# ============================================================================
print("8. AGENCIES")
print("-" * 80)
try:
    agencies = Agency.objects.all()
    print(f"  Total agencies: {agencies.count()}")
    
    for agency in agencies:
        task_count = MonitorTask.objects.filter(agency=agency, is_active=True).count()
        has_telegram = "✅" if agency.telegram_chat_id else "❌"
        print(f"    • {agency.name:30} | Tasks: {task_count:2} | Telegram: {has_telegram}")
        
except Exception as e:
    print(f"❌ Error: {e}")
print()

# ============================================================================
# 9. ERROR DETECTION
# ============================================================================
print("9. ERROR DETECTION")
print("-" * 80)
errors = []

# Check 1: Tasks without ticket_id
tasks_no_id = active_tasks.filter(ticket_id__isnull=True)
if tasks_no_id.count() > 0:
    errors.append(f"⚠️ {tasks_no_id.count()} tasks without ticket_id")

# Check 2: Never checked tasks
never_checked = active_tasks.filter(last_checked__isnull=True)
if never_checked.count() > 0:
    errors.append(f"⚠️ {never_checked.count()} tasks never checked")

# Check 3: Backed up queues
try:
    redis_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    r = redis.from_url(redis_url)
    
    vatican_len = r.llen('vatican')
    if vatican_len > 100:
        errors.append(f"⚠️ Vatican queue backed up: {vatican_len} tasks")
    
    colosseum_len = r.llen('colosseum')
    if colosseum_len > 50:
        errors.append(f"⚠️ Colosseum queue backed up: {colosseum_len} tasks")
        
    celery_len = r.llen('celery')
    if celery_len > 200:
        errors.append(f"⚠️ Celery queue backed up: {celery_len} tasks")
except:
    pass

# Check 4: All proxies on cooldown
try:
    from django.db.models import Q
    available_proxies_check = Proxy.objects.filter(is_active=True).filter(
        Q(cooldown_until__isnull=True) | Q(cooldown_until__lte=timezone.now())
    )
    if available_proxies_check.count() == 0:
        errors.append("❌ CRITICAL: All proxies on cooldown!")
except Exception as e:
    pass

# Check 5: Stale tasks
stale_tasks = active_tasks.filter(last_checked__lt=timezone.now() - timedelta(hours=2))
if stale_tasks.count() > 0:
    errors.append(f"⚠️ {stale_tasks.count()} tasks not checked in 2+ hours")

# Check 6: Error status tasks
error_tasks = active_tasks.filter(last_status='error')
if error_tasks.count() > 0:
    errors.append(f"⚠️ {error_tasks.count()} tasks in error status")

if errors:
    for error in errors:
        print(f"  {error}")
else:
    print("  ✅ No errors detected!")
print()

# ============================================================================
# 10. SYSTEM HEALTH SUMMARY
# ============================================================================
print("10. SYSTEM HEALTH SUMMARY")
print("-" * 80)

health_score = 100

# Deduct points for issues
if tasks_no_id.count() > 0:
    health_score -= 10
if never_checked.count() > 0:
    health_score -= 15
try:
    if vatican_len > 100:
        health_score -= 20
except:
    pass
try:
    if available_proxies_check.count() == 0:
        health_score -= 30
except:
    pass
if stale_tasks.count() > 0:
    health_score -= 10
if error_tasks.count() > 0:
    health_score -= 15

if health_score >= 90:
    status = "✅ EXCELLENT"
    color = "green"
elif health_score >= 70:
    status = "⚠️ GOOD"
    color = "yellow"
elif health_score >= 50:
    status = "⚠️ FAIR"
    color = "orange"
else:
    status = "❌ POOR"
    color = "red"

print(f"  Overall Health Score: {health_score}/100")
print(f"  Status: {status}")
print()

if health_score < 90:
    print("  Recommendations:")
    if tasks_no_id.count() > 0:
        print("    • Wait for ticket_id resolution or manually resolve")
    if never_checked.count() > 0:
        print("    • Check orchestration is running")
    try:
        if vatican_len > 100:
            print("    • Run cleanup_backed_up_queues task")
    except:
        pass
    try:
        if available_proxies_check.count() == 0:
            print("    • Wait for proxy cooldowns to expire")
    except:
        pass
    if stale_tasks.count() > 0:
        print("    • Check worker logs for errors")
    if error_tasks.count() > 0:
        print("    • Review error tasks and fix issues")

print()
print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
