import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

# Fix tasks 25, 26, 27
task_ids = [25, 26, 27]

for task_id in task_ids:
    try:
        task = MonitorTask.objects.get(id=task_id)
        print(f"Task {task.id}:")
        print(f"  BEFORE: type={task.ticket_type}, lang={task.language}")
        
        if task.ticket_type == 0 and task.language is not None:
            task.language = None
            task.save()
            print(f"  AFTER:  type={task.ticket_type}, lang={task.language} ✅ FIXED")
        else:
            print(f"  Already correct")
        print()
    except MonitorTask.DoesNotExist:
        print(f"Task {task_id} not found")

print("✅ All tasks fixed!")
