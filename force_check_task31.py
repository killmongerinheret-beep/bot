#!/usr/bin/env python3
"""Force check Task 31 immediately"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from django.utils import timezone

try:
    task = MonitorTask.objects.get(id=31)
    
    # Reset last_checked to force immediate check
    task.last_checked = None
    task.save()
    
    print(f"✅ Task 31 reset for immediate check")
    print(f"   Date: {task.dates}")
    print(f"   Visitors: {task.visitors}")
    print(f"   The bot will check it within 60 seconds")
    
    # Also trigger orchestration manually
    from monitors.tasks import orchestrate_all_tasks
    result = orchestrate_all_tasks()
    print(f"\n🚀 Orchestration triggered: {result}")
    
except MonitorTask.DoesNotExist:
    print("❌ Task 31 not found!")
except Exception as e:
    print(f"❌ Error: {e}")
