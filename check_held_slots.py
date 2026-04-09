#!/usr/bin/env python3
import os
import sys
import django

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from monitors.models import HeldSlot

# Check all held slots
held_slots = HeldSlot.objects.filter(status='held')
print(f"Total held slots: {held_slots.count()}")

for slot in held_slots:
    age_hours = slot.hold_duration_hours()
    print(f"ID: {slot.id}, Date: {slot.date}, Time: {slot.slot_time}, "
          f"Age: {age_hours:.1f}h, Last keepalive: {slot.last_keepalive_at}")
    
    # Check notes for keepalive failures
    if slot.notes:
        import json
        try:
            notes_data = json.loads(slot.notes)
            if 'keepalive_failures' in notes_data:
                print(f"  Keepalive failures: {notes_data['keepalive_failures']}")
        except:
            pass