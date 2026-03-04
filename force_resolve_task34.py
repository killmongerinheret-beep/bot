#!/usr/bin/env python
"""
Force resolve Task #34
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.tasks import resolve_and_check_task

print("🔧 Forcing resolution of Task #34...")
result = resolve_and_check_task(34)
print(f"Result: {result}")
