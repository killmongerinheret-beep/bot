#!/usr/bin/env python
"""Check WOR agency status and monitoring tasks"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import Agency, MonitorTask, HeldSlot

# Get WOR agency
try:
    wor = Agency.objects.get(name='WOR')
    print(f"✅ WOR Agency Found")
    print(f"   ID: {wor.id}")
    print(f"   Name: {wor.name}")
    print(f"   Active: {wor.is_active}")
    print(f"   Plan: {wor.plan}")
    print(f"   Created: {wor.created_at}")
    print()
    
    # Check monitoring tasks
    all_tasks = MonitorTask.objects.filter(agency=wor)
    active_tasks = all_tasks.filter(is_active=True)
    
    print(f"📊 Monitoring Tasks:")
    print(f"   Total: {all_tasks.count()}")
    print(f"   Active: {active_tasks.count()}")
    print(f"   Inactive: {all_tasks.filter(is_active=False).count()}")
    print()
    
    if active_tasks.exists():
        print(f"🔍 Active Tasks:")
        for task in active_tasks[:10]:
            dates_str = ', '.join(task.dates[:3]) if task.dates else 'No dates'
            if len(task.dates) > 3:
                dates_str += f' ... (+{len(task.dates)-3} more)'
            print(f"   Task #{task.id}:")
            print(f"     Dates: {dates_str}")
            print(f"     Ticket: {task.ticket_name}")
            print(f"     Visitors: {task.visitors}")
            print(f"     Tier: {task.tier}")
            print(f"     Interval: {task.check_interval}s")
            print(f"     Last status: {task.last_status}")
            print()
    else:
        print(f"⚠️  No active monitoring tasks for WOR")
        print(f"   The bot is running but not monitoring any dates for WOR agency")
        print()
        
        # Check if there are inactive tasks
        inactive = all_tasks.filter(is_active=False)
        if inactive.exists():
            print(f"   Found {inactive.count()} inactive tasks:")
            for task in inactive[:5]:
                print(f"     Task #{task.id}: {task.ticket_name} - Deactivated")
    
    # Check held slots
    held_slots = HeldSlot.objects.filter(task__agency=wor)
    active_holds = held_slots.filter(status='held')
    
    print(f"🔒 Held Slots:")
    print(f"   Total: {held_slots.count()}")
    print(f"   Active: {active_holds.count()}")
    
    if active_holds.exists():
        print(f"\n   Active holds:")
        for hold in active_holds[:5]:
            print(f"     Hold #{hold.id}: {hold.date} {hold.slot_time} | {hold.visitors}v | €{hold.total_price}")
    
    # Check buyer profile
    try:
        profile = wor.buyerprofile
        print(f"\n👤 Buyer Profile:")
        print(f"   Name: {profile.first_name} {profile.last_name}")
        print(f"   Email: {profile.email}")
        print(f"   Phone: {profile.phone}")
    except:
        print(f"\n⚠️  No buyer profile configured for WOR")
    
except Agency.DoesNotExist:
    print(f"❌ WOR agency not found in database")
    print(f"\nAvailable agencies:")
    for agency in Agency.objects.all():
        print(f"   - {agency.name} (Active: {agency.is_active})")
