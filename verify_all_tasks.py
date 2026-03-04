import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

# Get all active tasks
tasks = MonitorTask.objects.filter(is_active=True, site='vatican')

print(f"Vatican Tasks Configuration:\n")
print(f"{'ID':<5} {'Type':<10} {'Language':<10} {'Ticket Name':<40}")
print("=" * 70)

for task in tasks:
    ticket_type_str = "Standard" if task.ticket_type == 0 else "Guided"
    lang_str = task.language if task.language else "None"
    
    # Check if configuration is correct
    is_correct = True
    if task.ticket_type == 0 and task.language is not None:
        is_correct = False
        status = "❌ WRONG"
    elif task.ticket_type == 1 and task.language is None:
        is_correct = False
        status = "⚠️ MISSING LANG"
    else:
        status = "✅ OK"
    
    print(f"{task.id:<5} {ticket_type_str:<10} {lang_str:<10} {task.ticket_name:<40} {status}")

print("\n" + "=" * 70)
print("\nRules:")
print("  • Standard tickets (type=0) should have language=None")
print("  • Guided tours (type=1) should have language set (ENG/ITA/FRA/DEU/SPA)")
