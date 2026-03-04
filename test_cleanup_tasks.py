#!/usr/bin/env python
"""
Test cleanup tasks
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.tasks import cleanup_backed_up_queues, cleanup_expired_monitor_tasks

print("🧪 Testing cleanup tasks...\n")

print("1. Testing cleanup_backed_up_queues:")
result = cleanup_backed_up_queues()
print(f"   Result: {result}\n")

print("2. Testing cleanup_expired_monitor_tasks:")
result = cleanup_expired_monitor_tasks()
print(f"   Result: {result}\n")

print("✅ Tests complete!")
