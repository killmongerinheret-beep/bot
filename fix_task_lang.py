#!/usr/bin/env python
"""Fix task language configuration for standard Vatican tickets."""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
sys.path.insert(0, '/app')
os.chdir('/app')

import django
django.setup()

from monitors.models import MonitorTask

# Find all Vatican tasks with language set but looking for standard tickets
tasks = MonitorTask.objects.filter(
    site='vatican',
    language__isnull=False
).exclude(language='')

print(f"Found {tasks.count()} Vatican tasks with language set")

for task in tasks:
    ticket_name = task.ticket_name or ""
    ticket_label = task.ticket_label or ""
    
    # Standard tickets don't have languages - use empty string instead of None
    is_standard = (
        "Biglietti d'ingresso" in ticket_name or
        "Admission" in ticket_name or
        "Standard" in ticket_name or
        "Biglietti d'ingresso" in ticket_label
    )
    
    if is_standard:
        old_lang = task.language
        task.language = ''  # Empty string instead of NULL
        task.save()
        print(f"✅ Fixed Task {task.id}: Cleared language '{old_lang}' for '{ticket_name}'")
    else:
        print(f"ℹ️ Task {task.id}: Kept language '{task.language}' for '{ticket_name}'")

print("\nDone!")
