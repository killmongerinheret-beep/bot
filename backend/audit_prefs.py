import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

def audit_tasks():
    tasks = MonitorTask.objects.all()
    print(f"Found {tasks.count()} tasks")
    for t in tasks:
        print(f"\nTask {t.id}:")
        print(f"  Dates: {t.dates}")
        print(f"  Preferred Times: {t.preferred_times}")
        print(f"  Notifications: {t.notification_mode}")
        print(f"  Ticket: {t.ticket_name} (ID: {t.ticket_id})")

if __name__ == '__main__':
    audit_tasks()
