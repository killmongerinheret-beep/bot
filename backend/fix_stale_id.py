import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

def clear_stale_ids():
    # Find tasks with specific stale ID or just clear all to force rediscovery
    # User's logs showed 213165555
    stale_id = "213165555"
    
    tasks = MonitorTask.objects.filter(ticket_id=stale_id)
    count = tasks.count()
    
    print(f"Found {count} tasks with stale ID {stale_id}")
    
    if count > 0:
        tasks.update(ticket_id=None, ticket_name=None)
        print("✅ Cleared stale IDs. Bot will now auto-discover new IDs on next run.")
        
    # Also check other tasks?
    # Let's list what remains
    print("\nRemaining Tasks with Hardcoded IDs:")
    for t in MonitorTask.objects.exclude(ticket_id__isnull=True).exclude(ticket_id__exact=''):
        print(f"Task {t.id}: {t.ticket_id} ({t.ticket_name})")

if __name__ == '__main__':
    clear_stale_ids()
