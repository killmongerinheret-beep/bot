import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

tasks = MonitorTask.objects.filter(is_active=True, site='vatican')

print(f"\nTotal active Vatican tasks: {tasks.count()}\n")

for t in tasks:
    print(f"Task {t.id}: type={t.ticket_type}, lang={t.language}, dates={t.dates[:2] if len(t.dates) > 2 else t.dates}")
