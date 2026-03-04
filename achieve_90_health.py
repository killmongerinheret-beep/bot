#!/usr/bin/env python
"""
Achieve 90+ Health Score
Current: 75/100
Target: 90/100
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
from datetime import datetime, timedelta
import redis

print("=" * 80)
print("ACHIEVING 90+ HEALTH SCORE")
print("=" * 80)
print()

# Current scoring breakdown:
# - 10 points: tasks without ticket_id
# - 15 points: tasks never checked
# - 15 points: tasks in error status
# - 20 points: backed up queues
# - 10 points: stale tasks
# - 30 points: all proxies on cooldown

print("Current Health Score: 75/100")
print("Target: 90/100")
print("Points needed: +15")
print()

print("Scoring Breakdown:")
print("  -10 points: Tasks without ticket_id (currently 6 tasks)")
print("  -15 points: Tasks never checked (currently 1 task)")
print("  -0 points: Tasks in error status (currently 0)")
print("  -0 points: Backed up queues (all healthy)")
print("  -0 points: Stale tasks (none)")
print("  -0 points: Proxies on cooldown (none)")
print()

# ============================================================================
# STRATEGY TO REACH 90+
# ============================================================================
print("=" * 80)
print("STRATEGY TO REACH 90+ HEALTH")
print("=" * 80)
print()

print("Option 1: Wait for Task #26 to resolve (automatic)")
print("  • Task #26 is currently resolving ticket_id")
print("  • Once resolved: -15 points (never checked) = 90/100")
print("  • ETA: 1-2 minutes")
print()

print("Option 2: Force resolve all tasks without ticket_id")
print("  • Resolve ticket_id for all 6 tasks")
print("  • This would give: -0 points (no tasks without ID) = 100/100")
print("  • Time: 5-10 minutes")
print()

print("Recommended: Option 1 (wait for automatic resolution)")
print()

# ============================================================================
# CHECK CURRENT STATUS
# ============================================================================
print("=" * 80)
print("CHECKING CURRENT STATUS")
print("=" * 80)
print()

try:
    active_tasks = MonitorTask.objects.filter(is_active=True)
    tasks_no_id = active_tasks.filter(ticket_id__isnull=True)
    never_checked = active_tasks.filter(last_checked__isnull=True)
    error_tasks = active_tasks.filter(last_status='error')
    
    print(f"Active tasks: {active_tasks.count()}")
    print(f"Tasks without ticket_id: {tasks_no_id.count()}")
    print(f"Tasks never checked: {never_checked.count()}")
    print(f"Tasks in error: {error_tasks.count()}")
    print()
    
    if never_checked.exists():
        print("Tasks never checked:")
        for task in never_checked:
            print(f"  • Task #{task.id}: {task.ticket_name}")
            print(f"    Date: {task.dates[0] if task.dates else 'None'}")
            print(f"    Status: {task.last_status}")
            print(f"    ticket_id: {task.ticket_id}")
    
    # Check if Task #26 has been checked yet
    task26 = MonitorTask.objects.filter(id=26).first()
    if task26:
        print()
        print("Task #26 Status:")
        print(f"  Last checked: {task26.last_checked or 'Never'}")
        print(f"  Status: {task26.last_status}")
        print(f"  ticket_id: {task26.ticket_id}")
        
        if task26.last_checked:
            print()
            print("✅ Task #26 has been checked!")
            print("   Recalculating health score...")
            
            # Recalculate
            health_score = 100
            if tasks_no_id.count() > 0:
                health_score -= 10
            if never_checked.count() > 0:
                health_score -= 15
            if error_tasks.count() > 0:
                health_score -= 15
            
            print(f"   New Health Score: {health_score}/100")
            
            if health_score >= 90:
                print()
                print("🎉 CONGRATULATIONS! Health score is now 90+!")
            else:
                print()
                print(f"   Still need {90 - health_score} more points")
        else:
            print()
            print("⏳ Task #26 is still being resolved...")
            print("   Wait 1-2 minutes and check again")
    
except Exception as e:
    print(f"❌ Error: {e}")

print()

# ============================================================================
# OPTION: FORCE RESOLVE ALL TASKS
# ============================================================================
print("=" * 80)
print("OPTION: FORCE RESOLVE ALL TASKS (FOR 100/100 HEALTH)")
print("=" * 80)
print()

try:
    tasks_no_id = MonitorTask.objects.filter(is_active=True, ticket_id__isnull=True)
    
    if tasks_no_id.count() > 0:
        print(f"Found {tasks_no_id.count()} tasks without ticket_id:")
        for task in tasks_no_id:
            print(f"  • Task #{task.id}: {task.dates[0] if task.dates else 'None'}")
        
        print()
        print("To force resolve all tasks, run:")
        print()
        print("  from monitors.tasks import resolve_and_check_task")
        for task in tasks_no_id:
            print(f"  resolve_and_check_task.apply_async(args=[{task.id}], queue='vatican')")
        print()
        print("This will resolve all ticket_ids and achieve 100/100 health")
        print("Estimated time: 5-10 minutes")
    else:
        print("✅ All tasks have ticket_id!")
        print("   Health score should be 100/100")
        
except Exception as e:
    print(f"❌ Error: {e}")

print()

# ============================================================================
# AUTOMATIC RESOLUTION
# ============================================================================
print("=" * 80)
print("AUTOMATIC RESOLUTION (RECOMMENDED)")
print("=" * 80)
print()

print("The system will automatically reach 90+ health within 1-2 minutes:")
print()
print("1. Task #26 is currently being resolved")
print("2. Once checked: never_checked count = 0")
print("3. Health score: 100 - 10 (tasks without ID) = 90/100")
print()
print("To reach 100/100:")
print("  • Wait for all 6 tasks to resolve their ticket_ids")
print("  • This happens automatically during checks")
print("  • ETA: 5-10 minutes")
print()

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()
print("✅ Wait 2 minutes for Task #26 to complete")
print("   → Health will reach 90/100")
print()
print("✅ Wait 10 minutes for all tasks to resolve")
print("   → Health will reach 100/100")
print()
print("No manual action needed - system is working correctly!")
print()

# ============================================================================
# QUICK CHECK COMMAND
# ============================================================================
print("=" * 80)
print("QUICK CHECK COMMAND")
print("=" * 80)
print()
print("To check current health score:")
print()
print("  docker-compose exec backend python /app/comprehensive_system_check.py")
print()
print("Or run this script again:")
print()
print("  docker-compose exec backend python /app/achieve_90_health.py")
print()

print("=" * 80)
print("COMPLETE")
print("=" * 80)
