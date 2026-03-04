#!/usr/bin/env python3
"""
Direct test of Vatican ticket extraction with proxies
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def test_extraction():
    """Test ticket ID extraction for March 16, 2026"""
    bot = HydraBot(use_proxies=True)
    
    print("=" * 60)
    print("VATICAN TICKET EXTRACTION TEST")
    print("=" * 60)
    print(f"Proxies loaded: {len(bot.proxies)}")
    print()
    
    # Test date that should have tickets
    test_date = "16/03/2026"
    visitors = 1
    ticket_type = 0  # Standard ticket
    
    print(f"Testing: {test_date} for {visitors} visitor(s)")
    print(f"Ticket type: {'Standard' if ticket_type == 0 else 'Guided Tour'}")
    print()
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        try:
            print("Attempting to resolve dynamic IDs...")
            resolved_ids = await bot.resolve_all_dynamic_ids(
                page,
                ticket_type=ticket_type,
                target_date=test_date,
                visitors=visitors
            )
            
            print(f"\n✅ SUCCESS: Found {len(resolved_ids)} tickets")
            print()
            
            if resolved_ids:
                print("Tickets found:")
                for i, ticket in enumerate(resolved_ids, 1):
                    print(f"  {i}. ID: {ticket['id']}")
                    print(f"     Name: {ticket['name']}")
                    print()
            else:
                print("❌ NO TICKETS FOUND")
                print()
                print("Possible reasons:")
                print("1. Vatican hasn't released tickets for this date yet")
                print("2. Cloudflare/bot detection is blocking")
                print("3. Page structure changed")
                print("4. Proxy is being blocked")
                
                # Take screenshot for debugging
                try:
                    await page.screenshot(path="vatican_debug.png")
                    print("\n📸 Screenshot saved: vatican_debug.png")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await page.close()

if __name__ == "__main__":
    asyncio.run(test_extraction())
