#!/usr/bin/env python
"""
Debug March 9, 16, 23 Data Accuracy
Compare bot data vs actual Vatican website
"""
import os
import sys
import django
import asyncio

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, CheckResult
from worker_vatican.hydra_monitor import HydraBot

print("=" * 80)
print("DEBUGGING MARCH DATES ACCURACY")
print("=" * 80)
print()

# Target dates to debug
target_dates = {
    '2026-03-09': 'March 9, 2026',
    '2026-03-16': 'March 16, 2026',
    '2026-03-23': 'March 23, 2026'
}

async def check_date_accuracy(date_str, date_label):
    """Check accuracy for a specific date"""
    print(f"\n{'=' * 80}")
    print(f"CHECKING: {date_label} ({date_str})")
    print("=" * 80)
    
    # Find tasks for this date
    tasks = MonitorTask.objects.filter(
        is_active=True,
        dates__contains=[date_str]
    )
    
    if not tasks.exists():
        # Try DD/MM/YYYY format
        year, month, day = date_str.split('-')
        date_formatted = f"{day}/{month}/{year}"
        tasks = MonitorTask.objects.filter(
            is_active=True,
            dates__contains=[date_formatted]
        )
    
    if not tasks.exists():
        print(f"⚠️ No tasks found for {date_label}")
        return
    
    print(f"\nFound {tasks.count()} task(s) for this date:")
    for task in tasks:
        print(f"  • Task #{task.id}: {task.visitors} visitors, Times: {task.preferred_times}")
    
    # Get fresh data from Vatican website
    print(f"\n🌐 Fetching LIVE data from Vatican website...")
    
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # Test with first task's visitor count
        task = tasks.first()
        visitors = task.visitors
        
        # Convert date format
        year, month, day = date_str.split('-')
        date_formatted = f"{day}/{month}/{year}"
        
        print(f"   Date: {date_formatted}")
        print(f"   Visitors: {visitors}")
        
        try:
            # Resolve dynamic IDs
            resolved_ids = await bot.resolve_all_dynamic_ids(
                page,
                ticket_type=0,  # Standard ticket
                target_date=date_formatted,
                visitors=visitors
            )
            
            print(f"\n✅ Found {len(resolved_ids)} ticket types on Vatican website:")
            for item in resolved_ids:
                print(f"   • ID: {item['id']} - {item['name']}")
            
            if not resolved_ids:
                print(f"   ⚠️ No tickets found on Vatican website for this date!")
                await page.close()
                return
            
            # Use first ticket (Musei Vaticani)
            ticket_id = resolved_ids[0]['id']
            ticket_name = resolved_ids[0]['name']
            
            print(f"\n🎫 Checking availability for: {ticket_name}")
            print(f"   Ticket ID: {ticket_id}")
            
            # Check via click method
            result = await bot.check_via_click(
                page,
                ticket_id=ticket_id,
                ticket_name=ticket_name,
                ticket_index=0,
                visit_date=date_formatted,
                visitors=visitors
            )
            
            live_slots = result.get('slots', [])
            live_slots.sort()
            
            print(f"\n📊 LIVE Vatican Website Data:")
            print(f"   Total slots: {len(live_slots)}")
            if live_slots:
                print(f"   Slots: {', '.join(live_slots[:20])}")
                if len(live_slots) > 20:
                    print(f"          ... and {len(live_slots) - 20} more")
            else:
                print(f"   ❌ NO SLOTS AVAILABLE")
            
        except Exception as e:
            print(f"   ❌ Error fetching live data: {e}")
            import traceback
            traceback.print_exc()
        
        await page.close()
    
    # Compare with bot's stored data
    print(f"\n📦 Bot's Stored Data:")
    
    for task in tasks:
        print(f"\n   Task #{task.id}:")
        print(f"   Visitors: {task.visitors}")
        print(f"   Preferred times: {task.preferred_times}")
        
        # Get latest check result
        latest_result = CheckResult.objects.filter(task=task).order_by('-check_time').first()
        
        if not latest_result:
            print(f"   ⚠️ No check results found")
            continue
        
        # Extract slots from stored data
        details = latest_result.details
        stored_slots = []
        
        if isinstance(details, dict):
            if 'slots' in details:
                stored_slots = details['slots']
            elif 'updates' in details:
                for date, items in details.get('updates', {}).items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and 'slots' in item:
                                stored_slots.extend(item['slots'])
        
        stored_slots = list(set(stored_slots))
        stored_slots.sort()
        
        print(f"   Last checked: {latest_result.check_time}")
        print(f"   Status: {latest_result.status}")
        print(f"   Total slots: {len(stored_slots)}")
        if stored_slots:
            print(f"   Slots: {', '.join(stored_slots[:20])}")
            if len(stored_slots) > 20:
                print(f"          ... and {len(stored_slots) - 20} more")
        else:
            print(f"   ❌ NO SLOTS STORED")
        
        # Compare
        if live_slots and stored_slots:
            # Check if they match
            live_set = set(live_slots)
            stored_set = set(stored_slots)
            
            if live_set == stored_set:
                print(f"\n   ✅ DATA MATCHES PERFECTLY!")
            else:
                missing_in_stored = live_set - stored_set
                extra_in_stored = stored_set - live_set
                
                print(f"\n   ⚠️ DATA MISMATCH DETECTED!")
                if missing_in_stored:
                    print(f"   Missing in bot (on website but not in bot): {len(missing_in_stored)} slots")
                    print(f"      {', '.join(list(missing_in_stored)[:10])}")
                if extra_in_stored:
                    print(f"   Extra in bot (in bot but not on website): {len(extra_in_stored)} slots")
                    print(f"      {', '.join(list(extra_in_stored)[:10])}")
        elif live_slots and not stored_slots:
            print(f"\n   ❌ CRITICAL: Bot shows NO SLOTS but website has {len(live_slots)} slots!")
        elif not live_slots and stored_slots:
            print(f"\n   ⚠️ Bot shows {len(stored_slots)} slots but website shows SOLD OUT")
            print(f"      (Bot data may be stale)")
        else:
            print(f"\n   ℹ️ Both show NO SLOTS (sold out)")

# Run checks for all dates
async def main():
    for date_str, date_label in target_dates.items():
        try:
            await check_date_accuracy(date_str, date_label)
        except Exception as e:
            print(f"\n❌ Error checking {date_label}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 80}")
    print("DEBUGGING COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("  • Compared bot's stored data vs live Vatican website")
    print("  • Identified any mismatches or stale data")
    print("  • Check above for specific issues with each date")
    print()

# Run the async main function
asyncio.run(main())
