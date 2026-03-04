#!/usr/bin/env python
"""
Force Task #26 (March 23) to check NOW
"""
import os
import sys
import django
import asyncio

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from worker_vatican.hydra_monitor import HydraBot

print("=" * 80)
print("FORCING TASK #26 CHECK (March 23, 2026)")
print("=" * 80)
print()

task = MonitorTask.objects.get(id=26)

print(f"Task #{task.id}:")
print(f"  Ticket: {task.ticket_name}")
print(f"  Date: {task.dates}")
print(f"  Visitors: {task.visitors}")
print(f"  Preferred times: {task.preferred_times}")
print()

async def check_task26():
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # Resolve IDs for March 23
        print("🌐 Navigating to Vatican website for March 23...")
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page,
            ticket_type=0,  # Standard ticket
            target_date="23/03/2026",
            visitors=task.visitors
        )
        
        print(f"✅ Found {len(resolved_ids)} ticket types:")
        for item in resolved_ids:
            print(f"   • ID: {item['id']} - {item['name']}")
        
        if not resolved_ids:
            print("❌ No tickets found!")
            await page.close()
            return
        
        # Match by name
        fresh_id = None
        for item in resolved_ids:
            r_name = item.get('name', '').lower()
            if 'musei' in r_name and 'vaticani' in r_name:
                if 'palazzo' not in r_name and 'specola' not in r_name:
                    fresh_id = item['id']
                    print(f"\n✅ Matched: {item['name']}")
                    print(f"   Fresh ID: {fresh_id}")
                    break
        
        if not fresh_id:
            print("❌ Could not match ticket by name!")
            await page.close()
            return
        
        # Check availability
        print(f"\n🎫 Checking availability...")
        result = await bot.check_via_click(
            page,
            ticket_id=fresh_id,
            ticket_name=task.ticket_name,
            ticket_index=0,
            visit_date="23/03/2026",
            visitors=task.visitors
        )
        
        slots = result.get('slots', [])
        print(f"\n📊 LIVE DATA:")
        print(f"   Total slots: {len(slots)}")
        if slots:
            slots.sort()
            print(f"   Slots: {', '.join(slots)}")
        else:
            print(f"   ❌ NO SLOTS AVAILABLE (SOLD OUT)")
        
        # Save to database
        task.ticket_id = fresh_id
        task.last_checked = django.utils.timezone.now()
        task.last_status = 'available' if slots else 'sold_out'
        task.save()
        
        from monitors.models import CheckResult
        CheckResult.objects.create(
            task=task,
            status=task.last_status,
            details={
                'date': '23/03/2026',
                'ticket_id': fresh_id,
                'ticket_name': task.ticket_name,
                'slots': slots
            }
        )
        
        print(f"\n✅ Saved to database:")
        print(f"   ticket_id: {fresh_id}")
        print(f"   status: {task.last_status}")
        print(f"   last_checked: {task.last_checked}")
        
        await page.close()

# Run the check
asyncio.run(check_task26())

print(f"\n{'=' * 80}")
print("TASK #26 CHECK COMPLETE")
print("=" * 80)
print()
