#!/usr/bin/env python3
"""Check Task 31 details"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

try:
    task = MonitorTask.objects.get(id=31)
    print(f"Task 31 Details:")
    print(f"  Date: {task.dates}")
    print(f"  Visitors: {task.visitors}")
    print(f"  Ticket Name: {task.ticket_name}")
    print(f"  Ticket ID: {task.ticket_id}")
    print(f"  Ticket Type: {task.ticket_type}")
    print(f"  Language: {task.language}")
    print(f"  Last Checked: {task.last_checked}")
    print(f"  Last Status: {task.last_status}")
    print(f"  Is Active: {task.is_active}")
    print(f"  Check Interval: {task.check_interval}")
except MonitorTask.DoesNotExist:
    print("Task 31 not found!")
