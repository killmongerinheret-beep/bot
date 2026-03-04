#!/usr/bin/env python3
"""
Test the new dates (April 4 and May 26) to verify extraction works
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def test_new_dates():
    """Test the new dates"""
    print("\n" + "="*70)
    print("TESTING NEW DATES: APRIL 4 & MAY 26")
    print("="*70)
    
    bot = HydraBot(use_proxies=True)
    
    dates_to_test = [
        ("04/04/2026", "April 4, 2026"),
        ("26/05/2026", "May 26, 2026"),
    ]
    
    async with bot.get_browser() as browser:
        for date, label in dates_to_test:
            print(f"\n{'='*70}")
            print(f"Testing: {label}")
            print(f"{'='*70}")
            
            page = await browser.new_page()
            
            try:
                resolved_ids = await bot.resolve_all_dynamic_ids(
                    page,
                    ticket_type=0,  # Standard tickets
                    target_date=date,
                    visitors=6  # Match the task visitor count
                )
                
                print(f"\n📊 RESULTS:")
                print(f"   Total tickets found: {len(resolved_ids)}")
                
                # Look for the main ticket
                main_ticket = next((t for t in resolved_ids 
                                   if "musei vaticani" in t['name'].lower() 
                                   and "biglietti d'ingresso" in t['name'].lower() 
                                   and "didattiche" not in t['name'].lower()), None)
                
                print(f"\n🎯 MAIN TICKET CHECK:")
                if main_ticket:
                    print(f"   ✅ 'Musei Vaticani - Biglietti d'ingresso' FOUND!")
                    print(f"   Name: {main_ticket['name']}")
                    print(f"   ID: {main_ticket['id']}")
                else:
                    print(f"   ❌ 'Musei Vaticani - Biglietti d'ingresso' NOT FOUND")
                    print(f"   This might indicate an issue with the extraction.")
                
                print(f"\n📋 ALL TICKETS FOUND:")
                for i, ticket in enumerate(resolved_ids[:10], 1):  # Show first 10
                    marker = "✅" if "musei vaticani" in ticket['name'].lower() and "biglietti d'ingresso" in ticket['name'].lower() and "didattiche" not in ticket['name'].lower() else "📍"
                    print(f"   {marker} {ticket['name']}")
                    print(f"      ID: {ticket['id']}")
                
                if len(resolved_ids) > 10:
                    print(f"   ... and {len(resolved_ids) - 10} more tickets")
                
            except Exception as e:
                print(f"\n❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await page.close()

if __name__ == '__main__':
    asyncio.run(test_new_dates())
