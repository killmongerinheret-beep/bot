import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from monitors.models import MonitorTask

def main():
    qs = MonitorTask.objects.filter(site='vatican', ticket_type=0).exclude(language__isnull=True)
    count = 0
    for t in qs:
        if t.language:
            t.language = None
            t.save(update_fields=['language'])
            count += 1
    print(f"✅ Cleared language for standard tasks: {count}")

if __name__ == "__main__":
    main()

