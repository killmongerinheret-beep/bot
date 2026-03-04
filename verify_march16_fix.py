#!/usr/bin/env python3
"""
Verify that the fix works for March 16
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def verify_fix():
    """Verify the fix works"""
    print("\n" + "="*70)
    print("VERIFYING FIX FOR MARCH 16")
    print("="*70)
    
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # Test March 16 (the problematic date)
        print(f"\n🔍 Testing March 16, 2026...")
        
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page,
            ticket_type=0,  # Standard tickets
            target_date="16/03/2026",
            visitors=1
        )
        
        print(f"\n📊 RESULTS:")
        print(f"   Total tickets found: {len(resolved_ids)}")
        
        # Look for the main ticket
        main_ticket = next((t for t in resolved_ids if "musei vaticani" in t['name'].lower() and "biglietti d'ingresso" in t['name'].lower() and "didattiche" not in t['name'].lower()), None)
        
        print(f"\n🎯 MAIN TICKET CHECK:")
        if main_ticket:
            print(f"   ✅ 'Musei Vaticani - Biglietti d'ingresso' FOUND!")
            print(f"   Name: {main_ticket['name']}")
            print(f"   ID: {main_ticket['id']}")
            print(f"\n   🎉 FIX SUCCESSFUL! Bot can now find the ticket!")
        else:
            print(f"   ❌ 'Musei Vaticani - Biglietti d'ingresso' NOT FOUND")
            print(f"   Fix did not work as expected.")
        
        print(f"\n📋 ALL TICKETS FOUND:")
        for i, ticket in enumerate(resolved_ids, 1):
            marker = "✅" if "musei vaticani" in ticket['name'].lower() and "biglietti d'ingresso" in ticket['name'].lower() and "didattiche" not in ticket['name'].lower() else "📍"
            print(f"   {marker} {ticket['name']}")
            print(f"      ID: {ticket['id']}")
        
        await page.close()

if __name__ == '__main__':
    asyncio.run(verify_fix())
