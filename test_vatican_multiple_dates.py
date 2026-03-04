#!/usr/bin/env python3
"""
Test Vatican with multiple dates and with/without proxies
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def test_dates():
    """Test multiple dates"""
    
    # Test dates: today + 7 days, today + 14 days, March 16
    today = datetime.now()
    test_dates = [
        (today + timedelta(days=7)).strftime("%d/%m/%Y"),
        (today + timedelta(days=14)).strftime("%d/%m/%Y"),
        "10/03/2026",  # March 10 (closer)
        "16/03/2026",  # March 16 (original)
    ]
    
    print("=" * 60)
    print("VATICAN MULTI-DATE TEST")
    print("=" * 60)
    print()
    
    for use_proxies in [False, True]:
        proxy_status = "WITH PROXIES" if use_proxies else "WITHOUT PROXIES"
        print(f"\n{'=' * 60}")
        print(f"TESTING {proxy_status}")
        print(f"{'=' * 60}\n")
        
        bot = HydraBot(use_proxies=use_proxies)
        
        async with bot.get_browser() as browser:
            for date_str in test_dates:
                print(f"\n--- Testing {date_str} ---")
                page = await browser.new_page()
                
                try:
                    resolved_ids = await bot.resolve_all_dynamic_ids(
                        page,
                        ticket_type=0,
                        target_date=date_str,
                        visitors=1
                    )
                    
                    if resolved_ids:
                        print(f"✅ SUCCESS: Found {len(resolved_ids)} tickets")
                        for ticket in resolved_ids[:3]:  # Show first 3
                            print(f"   • {ticket['id']}: {ticket['name']}")
                        break  # Found tickets, no need to test more dates
                    else:
                        print(f"❌ No tickets found for {date_str}")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
                finally:
                    await page.close()
        
        # If we found tickets with this proxy setting, we're done
        if resolved_ids:
            print(f"\n✅ CONCLUSION: Tickets found {proxy_status}")
            break
    
    if not resolved_ids:
        print(f"\n❌ CONCLUSION: No tickets found on any date with or without proxies")
        print("This suggests Vatican hasn't released tickets for these dates yet.")

if __name__ == "__main__":
    asyncio.run(test_dates())
