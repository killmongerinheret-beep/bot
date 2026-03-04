"""
Force a fresh check of all Vatican tasks to update their status
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from monitors.tasks import run_god_tier_vatican_monitor
from celery import current_app

def force_check_all_vatican_tasks():
    """Force immediate check of all Vatican tasks"""
    
    vatican_tasks = MonitorTask.objects.filter(site='vatican', is_active=True)
    
    print(f"\n{'='*80}")
    print(f"FORCING FRESH CHECK FOR {vatican_tasks.count()} VATICAN TASKS")
    print(f"{'='*80}\n")
    
    for task in vatican_tasks:
        print(f"\nTask {task.id}:")
        print(f"  Dates: {task.dates}")
        print(f"  Visitors: {task.visitors}")
        print(f"  Ticket: {task.ticket_name}")
        print(f"  Current Status: {task.last_status}")
        
        # Queue immediate check for each date
        for date in task.dates:
            print(f"  Queuing check for {date}...")
            
            # Use god-tier monitor with browser fallback
            result = run_god_tier_vatican_monitor.apply_async(
                args=[
                    date,
                    task.ticket_id,
                    task.ticket_name,
                    task.language,
                    [task.id],
                    task.visitors
                ],
                kwargs={'use_browser_fallback': True}
            )
            
            print(f"    Task ID: {result.id}")
    
    print(f"\n{'='*80}")
    print(f"ALL CHECKS QUEUED!")
    print(f"Monitor the worker logs to see results:")
    print(f"  docker-compose logs -f worker_vatican")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    force_check_all_vatican_tasks()
