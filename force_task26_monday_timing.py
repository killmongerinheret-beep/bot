#!/usr/bin/env python3
"""
Force Task #26 (March 23 - Monday) to check with new progressive timing logic
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
    print("FORCE TASK #26 (MARCH 23 - MONDAY) WITH NEW TIMING LOGIC")
    print("=" * 80)
    
    # Get Task #26
    try:
        task = MonitorTask.objects.get(id=26)
        print(f"\n✅ Found Task #{task.id}")
        print(f"   Dates: {task.dates}")
        print(f"   Ticket: {task.ticket_name}")
        print(f"   Current ticket_id: {task.ticket_id}")
        print(f"   Status: {task.last_status}")
        
        # Clear ticket_id to force fresh resolution
        print(f"\n🔄 Clearing ticket_id to force fresh resolution...")
        task.ticket_id = None
        task.save()
        print(f"✅ ticket_id cleared")
        
        # Queue for immediate resolution
        print(f"\n📤 Queuing task for immediate resolution with new Monday timing logic...")
        result = resolve_and_check_task.apply_async(
            args=[task.id],
            queue='vatican',
            priority=9  # High priority
        )
        
        print(f"✅ Task queued successfully!")
        print(f"   Task ID: {result.id}")
        print(f"   Queue: vatican")
        print(f"   Priority: 9 (high)")
        
        print(f"\n⏱️ NEW TIMING LOGIC:")
        print(f"   • Progressive wait: Check every 3s for 'Musei Vaticani'")
        print(f"   • Max wait: 45 seconds")
        print(f"   • Logs exact timing when ticket appears")
        print(f"   • Stops waiting as soon as ticket is found")
        
        print(f"\n📊 Monitor logs with:")
        print(f"   docker-compose logs worker_vatican -f | grep -E 'Monday|Musei|⏱️'")
        
    except MonitorTask.DoesNotExist:
        print(f"❌ Task #26 not found!")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
