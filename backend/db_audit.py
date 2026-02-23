import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, Agency, CheckResult

def check_tasks():
    print("--- Agency Status ---")
    for agency in Agency.objects.all():
        print(f"Agency: {agency.name}, Owner: {agency.owner_id}, ID: {agency.id}")
    
    print("\n--- Active Tasks ---")
    active_tasks = MonitorTask.objects.filter(is_active=True)
    if not active_tasks.exists():
        print("No active tasks found!")
        return

    for task in active_tasks:
        print(f"Task ID: {task.id}")
        print(f"  Agency: {task.agency.name}")
        print(f"  Ticket ID: {task.ticket_id}")
        print(f"  Dates: {task.dates} (Type: {type(task.dates)})")
        print(f"  Last Checked: {task.last_checked}")
        print(f"  Last Status: {task.last_status}")
        
        results_count = task.results.count()
        print(f"  Results Count: {results_count}")
        if results_count > 0:
            last_result = task.results.order_by('-check_time').first()
            print(f"  Last Result: {last_result.status} at {last_result.check_time}")

if __name__ == "__main__":
    check_tasks()
