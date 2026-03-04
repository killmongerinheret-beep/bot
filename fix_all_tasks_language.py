#!/usr/bin/env python
"""
Fix all standard tickets - remove language
"""
import os
import sys
import django

# Setup Django
backend_path = '/app/backend' if os.path.exists('/app/backend') else os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

print("="*60)
print("Checking All Tasks for Language Issues")
print("="*60)
print()

fixed_count = 0
correct_count = 0

for task in MonitorTask.objects.all():
    print(f"Task #{task.id}:")
    print(f"  Date: {task.dates[0] if task.dates else 'N/A'}")
    print(f"  Ticket Type: {task.ticket_type} ({'Standard' if task.ticket_type == 0 else 'Guided'})")
    print(f"  Ticket Name: {task.ticket_name}")
    print(f"  Language: {task.language}")
    print(f"  Last Status: {task.last_status}")
    
    # Check if fix is needed
    if task.ticket_type == 0 and task.language:
        print(f"  ⚠️  ISSUE: Standard ticket should NOT have language")
        task.language = None
        task.save()
        print(f"  ✅ FIXED: Language set to None")
        fixed_count += 1
    elif task.ticket_type == 1 and not task.language:
        print(f"  ⚠️  WARNING: Guided tour should have a language (ENG/ITA/FRA/DEU/SPA)")
    else:
        print(f"  ✅ Configuration is correct")
        correct_count += 1
    
    print()

print("="*60)
print("Summary")
print("="*60)
print(f"Tasks fixed: {fixed_count}")
print(f"Tasks already correct: {correct_count}")
print()

if fixed_count > 0:
    print("✅ All standard tickets now have language=None")
    print("The bot will check them correctly now.")
else:
    print("✅ All tasks were already configured correctly!")
