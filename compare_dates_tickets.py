#!/usr/bin/env python3
"""
Compare tickets available for different dates to see if
Musei Vaticani tickets appear for some dates but not others.
"""

import asyncio
import sys
import os

# Add worker_vatican to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def check_date(bot, browser, date_str, visitors=1):
    """Check what tickets are available for a specific date"""
    page = await browser.new_page()
    
    try:
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page, 
            ticket_type=0,  # Standard
            target_date=date_str,
            visitors=visitors
        )
        
        # Look for Musei Vaticani tickets
        musei_tickets = [t for t in resolved_ids if 'musei vaticani' in t['name'].lower()]
        palazzo_tickets = [t for t in resolved_ids if 'palazzo papale' in t['name'].lower() and 'biglietti' in t['name'].lower()]
        
        return {
            'date': date_str,
            'total': len(resolved_ids),
            'musei_count': len(musei_tickets),
            'palazzo_count': len(palazzo_tickets),
            'musei_tickets': musei_tickets,
            'palazzo_tickets': palazzo_tickets
        }
    finally:
        await page.close()

async def main():
    print("\n" + "="*60)
    print("COMPARING TICKETS ACROSS DIFFERENT DATES")
    print("="*60)
    
    # Dates to check
    dates_to_check = [
        "10/03/2026",  # March 10 (working)
        "23/03/2026",  # March 23 (issue)
        "26/03/2026",  # March 26 (working)
        "22/04/2026",  # April 22 (was issue, now fixed)
    ]
    
    bot = HydraBot(use_proxies=True)
    
    try:
        async with bot.get_browser() as browser:
            results = []
            
            for date in dates_to_check:
                print(f"\n🔍 Checking {date}...")
                result = await check_date(bot, browser, date, visitors=1)
                results.append(result)
            
            # Display results
            print("\n" + "="*60)
            print("RESULTS SUMMARY")
            print("="*60)
            
            for result in results:
                print(f"\n📅 {result['date']}:")
                print(f"   Total tickets: {result['total']}")
                print(f"   Musei Vaticani tickets: {result['musei_count']}")
                print(f"   Palazzo Papale tickets: {result['palazzo_count']}")
                
                if result['musei_tickets']:
                    print(f"\n   ✅ Musei Vaticani tickets found:")
                    for t in result['musei_tickets']:
                        print(f"      - {t['name']} (ID: {t['id']})")
                else:
                    print(f"\n   ❌ NO Musei Vaticani tickets found!")
                
                if result['palazzo_tickets']:
                    print(f"\n   🏰 Palazzo Papale tickets found:")
                    for t in result['palazzo_tickets']:
                        print(f"      - {t['name']} (ID: {t['id']})")
            
            # Analysis
            print("\n" + "="*60)
            print("ANALYSIS")
            print("="*60)
            
            dates_with_musei = [r['date'] for r in results if r['musei_count'] > 0]
            dates_without_musei = [r['date'] for r in results if r['musei_count'] == 0]
            
            if dates_without_musei:
                print(f"\n⚠️  PROBLEM DETECTED:")
                print(f"   Dates WITHOUT Musei Vaticani tickets: {', '.join(dates_without_musei)}")
                print(f"\n   This means:")
                print(f"   1. Vatican Museums may be closed on these dates")
                print(f"   2. OR the bot is navigating to wrong page")
                print(f"   3. OR Vatican website structure changed")
                print(f"\n   The bot is showing 'Palazzo Papale' tickets instead,")
                print(f"   which are for Castel Gandolfo (Pope's summer residence),")
                print(f"   NOT the main Vatican Museums!")
            else:
                print(f"\n✅ All dates have Musei Vaticani tickets")
            
            if dates_with_musei:
                print(f"\n✅ Dates WITH Musei Vaticani tickets: {', '.join(dates_with_musei)}")
    
    finally:
        pass

if __name__ == '__main__':
    asyncio.run(main())
