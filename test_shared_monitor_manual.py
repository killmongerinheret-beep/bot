#!/usr/bin/env python3
"""Manually test shared monitor for unchecked tasks"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.tasks import run_shared_vatican_monitor

# Test with the dates that haven't been checked
dates_to_check = ['2026-04-15', '2026-03-04', '2026-03-09']

print(f"Testing shared monitor for {len(dates_to_check)} dates...")
print(f"Dates: {dates_to_check}")
print()

try:
    result = run_shared_vatican_monitor(
        ticket_type=0,
        language=None,
        dates=dates_to_check
    )
    print(f"✅ Result: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
