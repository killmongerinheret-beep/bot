#!/usr/bin/env python3
"""
Force resolution for tasks without ticket_id
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from monitors.tasks import resolve_and_check_task

def main():
    print("=" * 80)
    print("FIXING TASKS WITHOUT TICKET_ID")
    print("=" * 80)
    
    # Get tasks without ticket_id
    tasks = MonitorTask.objects.filter(ticket_id__isnull=True)
    
    print(f"\nFound {tasks.count()} tasks without ticket_id:")
    for task in tasks:
        print(f"  • Task #{task.id}: {task.dates[0] if task.dates else 'N/A'} - {task.ticket_name}")
    
    if tasks.count() == 0:
        print("\n✅ All tasks have ticket_id!")
        return
    
    print(f"\n🔄 Queuing {tasks.count()} tasks for immediate resolution...")
    
    queued = 0
    for task in tasks:
        try:
            # Reset error status if present
            if task.last_status == 'error':
                task.last_status = 'pending'
                task.save()
                print(f"  ✅ Reset Task #{task.id} from error to pending")
            
            # Queue for resolution
            result = resolve_and_check_task.apply_async(
                args=[task.id],
                queue='vatican',
                priority=9  # High priority
            )
            queued += 1
            print(f"  ✅ Queued Task #{task.id} (Job ID: {result.id})")
        except Exception as e:
            print(f"  ❌ Failed to queue Task #{task.id}: {e}")
    
    print(f"\n✅ Successfully queued {queued}/{tasks.count()} tasks")
    print(f"\n⏱️ Tasks will be processed by worker in 1-5 minutes")
    print(f"\n📊 Monitor progress with:")
    print(f"   docker-compose logs worker_vatican -f | grep -E 'Task #26|Task #29|MONDAY'")

if __name__ == "__main__":
    main()
