#!/usr/bin/env python3
"""Test shared monitor for Task 31's date"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.tasks import run_shared_vatican_monitor

print("Testing shared monitor for Task 31...")
print("Date: 2026-03-29")
print("Ticket Type: 0 (Standard)")
print("Language: None")
print()

try:
    result = run_shared_vatican_monitor(
        ticket_type=0,
        language=None,
        dates=['2026-03-29']
    )
    print(f"✅ Result: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
