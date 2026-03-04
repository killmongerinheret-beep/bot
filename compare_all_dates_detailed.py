#!/usr/bin/env python3
"""
Compare what tickets are available on different dates
to see why March 16 and 23 behave differently
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def check_date_tickets(bot, browser, date_str):
    """Check what tickets are available for a specific date"""
    page = await browser.new_page()
    
    try:
        # Navigate and extract IDs
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page, 
            ticket_type=0,  # Standard
            target_date=date_str,
            visitors=1
        )
        
        # Look for Musei Vaticani tickets
        musei_tickets = [t for t in resolved_ids if 'musei vaticani' in t['name'].lower()]
        palazzo_tickets = [t for t in resolved_ids if 'palazzo papale' in t['name'].lower()]
        
        # Find the main entry ticket
        main_ticket = None
        for t in musei_tickets:
            if 'biglietti' in t['name'].lower() and 'ingresso' in t['name'].lower():
                if 'visite' not in t['name'].lower() and 'guidate' not in t['name'].lower():
                    main_ticket = t
                    break
        
        return {
            'date': date_str,
            'total': len(resolved_ids),
            'musei_count': len(musei_tickets),
            'palazzo_count': len(palazzo_tickets),
            'main_ticket': main_ticket,
            'all_tickets': resolved_ids
        }
    finally:
        await page.close()

async def main():
    print("\n" + "="*70)
    print("DETAILED COMPARISON: WHAT TICKETS ARE AVAILABLE ON EACH DATE")
    print("="*70)
    
    dates_to_check = [
        ("10/03/2026", "March 10 (Working)"),
        ("16/03/2026", "March 16 (Issue)"),
        ("23/03/2026", "March 23 (Issue)"),
        ("26/03/2026", "March 26 (Working)"),
    ]
    
    bot = HydraBot(use_proxies=True)
    
    try:
        async with bot.get_browser() as browser:
            results = []
            
            for date, label in dates_to_check:
                print(f"\n🔍 Checking {label}...")
                result = await check_date_tickets(bot, browser, date)
                results.append((label, result))
            
            # Display detailed results
            print("\n" + "="*70)
            print("DETAILED RESULTS")
            print("="*70)
            
            for label, result in results:
                print(f"\n📅 {label}:")
                print(f"   Total tickets: {result['total']}")
                print(f"   Musei Vaticani tickets: {result['musei_count']}")
                print(f"   Palazzo Papale tickets: {result['palazzo_count']}")
                
                if result['main_ticket']:
                    print(f"\n   ✅ MAIN TICKET FOUND:")
                    print(f"      Name: {result['main_ticket']['name']}")
                    print(f"      ID: {result['main_ticket']['id']}")
                else:
                    print(f"\n   ❌ NO MAIN TICKET (Musei Vaticani - Biglietti d'ingresso)")
                
                print(f"\n   All tickets:")
                for i, t in enumerate(result['all_tickets'], 1):
                    marker = "🎫" if 'musei vaticani' in t['name'].lower() else "🏰" if 'palazzo' in t['name'].lower() else "📍"
                    print(f"      {marker} {t['name']}")
            
            # Analysis
            print("\n" + "="*70)
            print("ANALYSIS")
            print("="*70)
            
            working_dates = []
            issue_dates = []
            
            for label, result in results:
                if result['main_ticket']:
                    working_dates.append(label)
                else:
                    issue_dates.append(label)
            
            if issue_dates:
                print(f"\n⚠️  DATES WITHOUT MAIN TICKET:")
                for date in issue_dates:
                    print(f"   • {date}")
                print(f"\n   These dates are showing different ticket types!")
                print(f"   The main 'Musei Vaticani - Biglietti d'ingresso' is NOT available.")
            
            if working_dates:
                print(f"\n✅ DATES WITH MAIN TICKET:")
                for date in working_dates:
                    print(f"   • {date}")
    
    finally:
        pass

if __name__ == '__main__':
    asyncio.run(main())
