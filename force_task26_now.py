#!/usr/bin/env python
"""
Manually force Task #26 check with correct HTML parsing
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
from django.utils import timezone
import json

print("=" * 80)
print("FORCING TASK #26 (March 23) - MANUAL CHECK")
print("=" * 80)
print()

task = MonitorTask.objects.get(id=26)

print(f"Task #{task.id}:")
print(f"  Ticket: {task.ticket_name}")
print(f"  Date: 2026-03-23")
print(f"  Visitors: {task.visitors}")
print(f"  Preferred times: {task.preferred_times}")
print()

async def check_march23():
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        print("🌐 Navigating to Vatican website for March 23...")
        
        # Resolve IDs
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page,
            ticket_type=0,
            target_date="23/03/2026",
            visitors=task.visitors
        )
        
        print(f"✅ Found {len(resolved_ids)} ticket types")
        
        # Find Musei Vaticani
        fresh_id = None
        for item in resolved_ids:
            name = item.get('name', '')
            print(f"   • ID: {item['id']} - {name}")
            
            # Match Musei Vaticani
            if 'musei' in name.lower() and 'vaticani' in name.lower():
                if 'palazzo' not in name.lower() and 'specola' not in name.lower():
                    fresh_id = item['id']
                    print(f"\n✅ MATCHED: {name}")
                    print(f"   Fresh ID: {fresh_id}")
        
        if not fresh_id:
            print("\n❌ Could not find Musei Vaticani ticket!")
            await page.close()
            return None
        
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
            
            # Check preferred times
            preferred = task.preferred_times or []
            found_prefs = [s for s in slots if s in preferred]
            if found_prefs:
                print(f"   ✅ Preferred times found: {', '.join(found_prefs)}")
            else:
                print(f"   ❌ Preferred time {preferred[0] if preferred else 'N/A'} not available")
        else:
            print(f"   ❌ SOLD OUT")
        
        # Save to database
        task.ticket_id = fresh_id
        task.last_checked = timezone.now()
        task.last_status = 'available' if slots else 'sold_out'
        
        # Save result summary for Telegram
        summary_data = {
            "updates": {
                "23/03/2026": [{
                    'id': fresh_id,
                    'name': task.ticket_name,
                    'slots': slots
                }]
            },
            "last_updated": str(timezone.now())
        }
        task.last_result_summary = json.dumps(summary_data)
        task.save()
        
        # Create check result
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
        return slots

# Run check
slots = asyncio.run(check_march23())

print(f"\n{'=' * 80}")
print("TASK #26 CHECK COMPLETE")
print("=" * 80)
print()

if slots:
    print(f"✅ Found {len(slots)} available time slots")
else:
    print("❌ No slots available (sold out)")

print()
