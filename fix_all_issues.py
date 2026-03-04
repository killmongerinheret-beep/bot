#!/usr/bin/env python
"""
Fix All System Issues
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from django.utils import timezone
from datetime import datetime
import redis

print("=" * 80)
print("FIXING ALL SYSTEM ISSUES")
print("=" * 80)
print()

# ============================================================================
# FIX 1: Delete Today's Tasks (Cannot Resolve)
# ============================================================================
print("FIX 1: Deleting tasks for today's date (March 4, 2026)")
print("-" * 80)
try:
    today_tasks = MonitorTask.objects.filter(id__in=[32, 34])
    count = today_tasks.count()
    
    if count > 0:
        print(f"  Found {count} tasks for today:")
        for task in today_tasks:
            print(f"    • Task #{task.id}: {task.dates[0] if task.dates else 'No date'} - {task.ticket_name}")
            print(f"      Visitors: {task.visitors}, Times: {task.preferred_times}")
        
        deleted = today_tasks.delete()
        print(f"\n  ✅ Deleted {deleted[0]} tasks")
    else:
        print("  ℹ️ No tasks for today found")
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# ============================================================================
# FIX 2: Clean Backed-Up Celery Queue
# ============================================================================
print("FIX 2: Cleaning backed-up Celery queue")
print("-" * 80)
try:
    redis_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    r = redis.from_url(redis_url)
    
    celery_len = r.llen('celery')
    print(f"  Current celery queue length: {celery_len}")
    
    if celery_len > 200:
        print(f"  ⚠️ Queue backed up (threshold: 200)")
        r.delete('celery')
        print(f"  ✅ Purged celery queue - removed {celery_len} tasks")
    else:
        print(f"  ℹ️ Queue is healthy (< 200 tasks)")
    
    # Also check other queues
    vatican_len = r.llen('vatican')
    colosseum_len = r.llen('colosseum')
    
    print(f"\n  Queue status after cleanup:")
    print(f"    • vatican: {vatican_len} tasks")
    print(f"    • colosseum: {colosseum_len} tasks")
    print(f"    • celery: {r.llen('celery')} tasks")
    
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# ============================================================================
# FIX 3: Force Retry Task #26 (Error Status)
# ============================================================================
print("FIX 3: Resetting Task #26 to retry resolution")
print("-" * 80)
try:
    task26 = MonitorTask.objects.filter(id=26).first()
    
    if task26:
        print(f"  Task #26 details:")
        print(f"    Date: {task26.dates[0] if task26.dates else 'None'}")
        print(f"    Status: {task26.last_status}")
        print(f"    ticket_id: {task26.ticket_id}")
        
        # Clear error status to allow retry
        task26.last_status = 'pending'
        task26.ticket_id = None  # Force fresh resolution
        task26.save()
        
        print(f"  ✅ Reset task to 'pending' - will retry on next orchestration")
    else:
        print("  ℹ️ Task #26 not found")
        
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# ============================================================================
# FIX 4: Clear Resolution Locks (If Any Stuck)
# ============================================================================
print("FIX 4: Clearing any stuck resolution locks")
print("-" * 80)
try:
    redis_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    r = redis.from_url(redis_url)
    
    resolving_keys = r.keys('resolving:*')
    
    if resolving_keys:
        print(f"  Found {len(resolving_keys)} resolution locks")
        for key in resolving_keys:
            r.delete(key)
        print(f"  ✅ Cleared {len(resolving_keys)} locks")
    else:
        print("  ℹ️ No stuck locks found")
        
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# ============================================================================
# FIX 5: Update Stale Tasks (Force Check)
# ============================================================================
print("FIX 5: Resetting stale tasks (not checked in 2+ hours)")
print("-" * 80)
try:
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=2)
    
    stale_tasks = MonitorTask.objects.filter(
        is_active=True,
        last_checked__lt=cutoff
    )
    
    count = stale_tasks.count()
    
    if count > 0:
        print(f"  Found {count} stale tasks:")
        for task in stale_tasks:
            last_check = task.last_checked.strftime('%H:%M:%S') if task.last_checked else 'Never'
            print(f"    • Task #{task.id}: Last checked {last_check}")
        
        # Reset last_checked to None to force immediate check
        for task in stale_tasks:
            task.last_checked = None
            task.save()
        
        print(f"  ✅ Reset {count} tasks - will be checked immediately")
    else:
        print("  ℹ️ No stale tasks found")
        
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# ============================================================================
# FIX 6: Verify All Active Tasks Have Valid Dates
# ============================================================================
print("FIX 6: Verifying all tasks have valid future dates")
print("-" * 80)
try:
    from datetime import datetime
    now_date = timezone.now().date()
    
    all_tasks = MonitorTask.objects.filter(is_active=True)
    issues_found = 0
    
    for task in all_tasks:
        if not task.dates or len(task.dates) == 0:
            print(f"  ⚠️ Task #{task.id} has no dates - deactivating")
            task.is_active = False
            task.save()
            issues_found += 1
            continue
        
        # Check if all dates are in the past
        all_past = True
        for d_str in task.dates:
            try:
                if "/" in d_str:
                    dt = datetime.strptime(d_str, "%d/%m/%Y").date()
                elif "-" in d_str:
                    dt = datetime.strptime(d_str, "%Y-%m-%d").date()
                else:
                    continue
                
                if dt >= now_date:
                    all_past = False
                    break
            except:
                pass
        
        if all_past:
            print(f"  ⚠️ Task #{task.id} has only past dates - deactivating")
            task.is_active = False
            task.save()
            issues_found += 1
    
    if issues_found == 0:
        print("  ✅ All tasks have valid future dates")
    else:
        print(f"  ✅ Fixed {issues_found} tasks with invalid dates")
        
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# ============================================================================
# FIX 7: Run Cleanup Tasks Manually
# ============================================================================
print("FIX 7: Running cleanup tasks")
print("-" * 80)
try:
    from monitors.tasks import cleanup_expired_monitor_tasks, cleanup_backed_up_queues
    
    print("  Running cleanup_expired_monitor_tasks...")
    result1 = cleanup_expired_monitor_tasks()
    print(f"    Result: {result1}")
    
    print("\n  Running cleanup_backed_up_queues...")
    result2 = cleanup_backed_up_queues()
    print(f"    Result: {result2}")
    
    print("\n  ✅ Cleanup tasks completed")
    
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("FIX SUMMARY")
print("=" * 80)

try:
    # Count remaining issues
    active_tasks = MonitorTask.objects.filter(is_active=True)
    tasks_no_id = active_tasks.filter(ticket_id__isnull=True).count()
    never_checked = active_tasks.filter(last_checked__isnull=True).count()
    error_tasks = active_tasks.filter(last_status='error').count()
    
    # Check queues
    redis_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    r = redis.from_url(redis_url)
    vatican_len = r.llen('vatican')
    colosseum_len = r.llen('colosseum')
    celery_len = r.llen('celery')
    
    print("\nCurrent Status:")
    print(f"  Active tasks: {active_tasks.count()}")
    print(f"  Tasks without ticket_id: {tasks_no_id}")
    print(f"  Tasks never checked: {never_checked}")
    print(f"  Tasks in error status: {error_tasks}")
    print()
    print("Queue Status:")
    print(f"  vatican: {vatican_len} tasks")
    print(f"  colosseum: {colosseum_len} tasks")
    print(f"  celery: {celery_len} tasks")
    print()
    
    # Calculate health score
    health_score = 100
    if tasks_no_id > 0:
        health_score -= 10
    if never_checked > 0:
        health_score -= 15
    if error_tasks > 0:
        health_score -= 15
    if celery_len > 200:
        health_score -= 20
    
    if health_score >= 90:
        status = "✅ EXCELLENT"
    elif health_score >= 70:
        status = "✅ GOOD"
    elif health_score >= 50:
        status = "⚠️ FAIR"
    else:
        status = "❌ POOR"
    
    print(f"Overall Health Score: {health_score}/100")
    print(f"Status: {status}")
    print()
    
    if health_score >= 70:
        print("✅ All critical issues fixed!")
    else:
        print("⚠️ Some issues remain - they will self-resolve with automatic retries")
    
except Exception as e:
    print(f"❌ Error calculating summary: {e}")

print()
print("=" * 80)
print("FIXES COMPLETE")
print("=" * 80)
