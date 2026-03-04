#!/usr/bin/env python3
"""
Debug Task #26 - Force immediate execution and watch logs
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

async def test_march23_extraction():
    print("=" * 80)
    print("TESTING MARCH 23 (MONDAY) EXTRACTION WITH NEW CODE")
    print("=" * 80)
    
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        context = await browser.new_context()
        page = await context.new_page()
        
        # Apply stealth
        await bot.apply_stealth(context, page)
        
        print(f"\n🔍 Testing resolve_all_dynamic_ids for March 23, 2026 (Monday)...")
        print(f"   Visitors: 1")
        print(f"   Ticket Type: 0 (Standard)")
        
        ids = await bot.resolve_all_dynamic_ids(
            page=page,
            ticket_type=0,
            target_date="23/03/2026",
            visitors=1,
            force_refresh=True
        )
        
        print(f"\n📊 RESULTS:")
        print(f"   Total IDs extracted: {len(ids)}")
        
        # Check if Musei Vaticani is in the list
        musei_found = False
        for item in ids:
            if 'musei' in item['name'].lower() and 'vaticani' in item['name'].lower() and 'biglietti' in item['name'].lower():
                musei_found = True
                print(f"\n✅ FOUND: Musei Vaticani - Biglietti d'ingresso")
                print(f"   ID: {item['id']}")
                print(f"   Name: {item['name']}")
                break
        
        if not musei_found:
            print(f"\n❌ FAILED: 'Musei Vaticani - Biglietti d'ingresso' NOT FOUND")
            print(f"\n📋 All tickets found:")
            for item in ids:
                print(f"   • ID: {item['id']} | {item['name']}")
        else:
            print(f"\n✅ SUCCESS: Monday extraction working!")
            print(f"\n📋 All {len(ids)} tickets:")
            for item in ids:
                marker = "✅" if 'musei' in item['name'].lower() and 'vaticani' in item['name'].lower() and 'biglietti' in item['name'].lower() else "  "
                print(f"   {marker} ID: {item['id']} | {item['name']}")

if __name__ == "__main__":
    asyncio.run(test_march23_extraction())
