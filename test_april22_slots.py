import asyncio
import sys
sys.path.insert(0, '/app')

from worker_vatican.hydra_monitor import HydraBot

async def check_april22():
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # Resolve dynamic IDs for April 22
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page,
            ticket_type=0,  # Standard ticket
            target_date="22/04/2026",
            visitors=1
        )
        
        print(f"\n✅ Found {len(resolved_ids)} tickets for April 22, 2026\n")
        
        # Find Standard Entry ticket
        standard_ticket = None
        for item in resolved_ids:
            name = item.get('name', '').lower()
            if 'biglietti' in name or 'ingresso' in name or 'standard' in name or 'entry' in name:
                if 'lunch' not in name and 'pranzo' not in name:
                    standard_ticket = item
                    break
        
        if not standard_ticket:
            print("❌ Could not find Standard Entry ticket")
            return
        
        print(f"🎫 Checking: {standard_ticket['name']}")
        print(f"   ID: {standard_ticket['id']}\n")
        
        # Check availability
        result = await bot.check_via_api_direct(
            page,
            ticket_id=standard_ticket['id'],
            ticket_name=standard_ticket['name'],
            visit_date="22/04/2026",
            visitors=1,
            language=None
        )
        
        slots = result.get('slots', [])
        
        if slots:
            print(f"✅ Found {len(slots)} available slots:\n")
            for slot in slots:
                time_str = slot if isinstance(slot, str) else slot.get('time', slot)
                print(f"   • {time_str}")
                
            # Check if 17:00 is available
            has_17 = any('17:00' in str(slot) for slot in slots)
            if has_17:
                print(f"\n✅ 17:00 IS AVAILABLE!")
            else:
                print(f"\n❌ 17:00 is NOT in the available slots")
        else:
            print("❌ No slots available")

if __name__ == "__main__":
    asyncio.run(check_april22())
