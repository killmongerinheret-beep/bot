"""
Check what tickets are actually available on March 16, 2026
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def check_march16():
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # Resolve IDs for March 16
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page,
            ticket_type=0,  # Standard tickets
            target_date="16/03/2026",
            visitors=1
        )
        
        await page.close()
        
        print(f"\n{'='*80}")
        print(f"TICKETS AVAILABLE ON MARCH 16, 2026")
        print(f"{'='*80}\n")
        print(f"Total tickets found: {len(resolved_ids)}\n")
        
        for item in resolved_ids:
            ticket_id = item.get('id')
            name = item.get('name', 'Unknown')
            
            # Skip button IDs
            if 'dx_' in str(ticket_id):
                continue
            
            print(f"ID: {ticket_id}")
            print(f"Name: {name}")
            print()

asyncio.run(check_march16())
