#!/usr/bin/env python
"""
Update Task #26 to reflect that Musei Vaticani is not available on March 23
"""
import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, CheckResult
from django.utils import timezone

print("=" * 80)
print("UPDATING TASK #26 STATUS")
print("=" * 80)
print()

task = MonitorTask.objects.get(id=26)

print(f"Current Status:")
print(f"  Last status: {task.last_status}")
print(f"  Last checked: {task.last_checked}")
print()

# Update task
task.last_status = 'ticket_unavailable'
task.last_checked = timezone.now()
task.last_result_summary = json.dumps({
    "status": "ticket_unavailable",
    "message": "Musei Vaticani tickets not offered on March 23, 2026",
    "reason": "Vatican website only shows Palazzo Papale, Specola Vaticana, and Borgo Laudato si' for this date",
    "available_alternatives": [
        {
            "name": "Palazzo Papale - Biglietti d'ingresso",
            "id": "583850058",
            "note": "Different venue - requires user confirmation"
        },
        {
            "name": "Specola Vaticana - Visita Guidata Gruppi",
            "id": "713654115",
            "note": "Different venue - guided tour"
        }
    ],
    "recommendation": "Either wait for Vatican to release Musei Vaticani tickets, switch to Palazzo Papale, or choose a different date",
    "last_checked": str(timezone.now())
})
task.save()

# Create check result
CheckResult.objects.create(
    task=task,
    status='ticket_unavailable',
    details={
        "date": "2026-03-23",
        "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
        "message": "Ticket type not available on Vatican website for this date",
        "available_tickets": [
            "Specola Vaticana - Visita Guidata Gruppi",
            "Palazzo Papale - Cupole Astronomiche",
            "Palazzo Papale - Biglietti d'ingresso",
            "Palazzo Papale - Visita Guidata Gruppi",
            "Palazzo Papale - Reparti Chiusi",
            "Borgo Laudato si' - Mezzo Ecologico",
            "Borgo Laudato si' - Passeggiata"
        ]
    }
)

print(f"✅ Updated Status:")
print(f"  Last status: {task.last_status}")
print(f"  Last checked: {task.last_checked}")
print(f"  Message: Musei Vaticani tickets not offered on March 23, 2026")
print()
print("=" * 80)
print("TASK #26 UPDATED")
print("=" * 80)
print()
