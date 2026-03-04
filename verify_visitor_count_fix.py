#!/usr/bin/env python
"""
Verification script for visitor count fix
Run this after applying the fixes to verify everything is working correctly
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from monitors.tasks import orchestrate_all_tasks
from datetime import datetime

def verify_task_configuration():
    """Verify that tasks have correct visitor configuration"""
    print("=" * 60)
    print("TASK CONFIGURATION VERIFICATION")
    print("=" * 60)
    
    tasks = MonitorTask.objects.filter(is_active=True, site='vatican')
    
    print(f"\nFound {tasks.count()} active Vatican tasks\n")
    
    for task in tasks:
        print(f"Task #{task.id}: {task.area_name}")
        print(f"  Visitors: {task.visitors}")
        print(f"  Dates: {task.dates}")
        print(f"  Language: {task.language or 'None (Standard)'}")
        print(f"  Ticket Type: {'Standard' if task.ticket_type == 0 else 'Guided'}")
        print(f"  Ticket ID: {task.ticket_id}")
        print(f"  Last Checked: {task.last_checked}")
        print(f"  Last Status: {task.last_status}")
        print()

def verify_critical_tasks():
    """Verify the specific tasks mentioned in the bug report"""
    print("=" * 60)
    print("CRITICAL TASKS VERIFICATION")
    print("=" * 60)
    
    critical_task_ids = [15, 18, 19]
    
    for task_id in critical_task_ids:
        try:
            task = MonitorTask.objects.get(id=task_id)
            print(f"\n✅ Task #{task_id} Found")
            print(f"   Visitors: {task.visitors}")
            print(f"   Dates: {', '.join(task.dates[:3])}{'...' if len(task.dates) > 3 else ''}")
            print(f"   Language: {task.language or 'None'}")
            
            # Check for March 16 specifically
            if '16/03/2026' in task.dates or '2026-03-16' in task.dates:
                print(f"   ⚠️ Contains March 16 - This should show availability for {task.visitors} visitor(s)")
        except MonitorTask.DoesNotExist:
            print(f"\n❌ Task #{task_id} Not Found")

def check_code_changes():
    """Verify that code changes are in place"""
    print("\n" + "=" * 60)
    print("CODE CHANGES VERIFICATION")
    print("=" * 60)
    
    checks = []
    
    # Check 1: orchestrate_all_tasks grouping
    try:
        with open('backend/monitors/tasks.py', 'r') as f:
            content = f.read()
            if 'key = (date, task.ticket_id, task.language or None, task.visitors)' in content:
                checks.append(("✅", "orchestrate_all_tasks() groups by visitors"))
            else:
                checks.append(("❌", "orchestrate_all_tasks() NOT grouping by visitors"))
    except Exception as e:
        checks.append(("❌", f"Could not read tasks.py: {e}"))
    
    # Check 2: run_god_tier_vatican_monitor signature
    try:
        with open('backend/monitors/tasks.py', 'r') as f:
            content = f.read()
            if 'def run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors=' in content:
                checks.append(("✅", "run_god_tier_vatican_monitor() has visitors parameter"))
            else:
                checks.append(("❌", "run_god_tier_vatican_monitor() missing visitors parameter"))
    except Exception as e:
        checks.append(("❌", f"Could not verify god_tier signature: {e}"))
    
    # Check 3: run_smart_vatican_monitor signature
    try:
        with open('backend/monitors/tasks.py', 'r') as f:
            content = f.read()
            if 'def run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors=' in content:
                checks.append(("✅", "run_smart_vatican_monitor() has visitors parameter"))
            else:
                checks.append(("❌", "run_smart_vatican_monitor() missing visitors parameter"))
    except Exception as e:
        checks.append(("❌", f"Could not verify smart_monitor signature: {e}"))
    
    # Check 4: hydra_monitor defaults
    try:
        with open('worker_vatican/hydra_monitor.py', 'r') as f:
            content = f.read()
            if 'async def resolve_all_dynamic_ids(self, page, ticket_type, target_date, visitors=1' in content:
                checks.append(("✅", "resolve_all_dynamic_ids() defaults to 1 visitor"))
            else:
                checks.append(("⚠️", "resolve_all_dynamic_ids() may still default to 2 visitors"))
    except Exception as e:
        checks.append(("❌", f"Could not verify hydra_monitor: {e}"))
    
    print()
    for status, message in checks:
        print(f"{status} {message}")

def trigger_test_check():
    """Trigger a test orchestration"""
    print("\n" + "=" * 60)
    print("TRIGGER TEST CHECK")
    print("=" * 60)
    
    response = input("\nDo you want to trigger orchestrate_all_tasks()? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n🚀 Triggering orchestration...")
        try:
            result = orchestrate_all_tasks()
            print(f"✅ Result: {result}")
            print("\n📋 Check logs with: docker-compose logs -f celery_worker")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("Skipped orchestration trigger")

def main():
    print("\n🔍 Vatican Bot Visitor Count Fix Verification")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        verify_task_configuration()
        verify_critical_tasks()
        check_code_changes()
        trigger_test_check()
        
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        print("\nNext Steps:")
        print("1. Review the output above")
        print("2. If all checks pass, restart Celery workers")
        print("3. Monitor logs for correct visitor counts")
        print("4. Verify Task #19 finds availability for March 16")
        print()
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
