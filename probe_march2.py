import asyncio, sys, os, json
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "worker_vatican")
from god_tier_monitor_v2 import GodTierVaticanMonitorV2

async def probe_march2():
    # Force UTF-8 for stdout
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    m = GodTierVaticanMonitorV2()
    date_str = "02/03/2026"
    pax = 2
    
    print(f"--- Exhaustive Search for {date_str} (Pax {pax}) ---")
    
    for t_type in [0, 1]:
        type_name = "Standard" if t_type == 0 else "Guided"
        print(f"\n--- Checking {type_name} ---")
        
        # Force refresh to get latest IDs
        await m.refresh_session_with_browser(t_type, date_str, visitors=pax)
        
        results = await m.check_availability(date_str, ticket_type=t_type, visitors=pax, languages=["ITA", "ENG", "FRA", "DEU", "SPA"])
        
        if not results:
            print(f"RESULT: No {type_name} availability found.")
        
        for res in results:
            # Safely print without emojis
            name_safe = res['ticket_name'].replace("\u2705", "").replace("\u274c", "")
            print(f"MATCH: [{res['language']}] {name_safe} (ID: {res['ticket_id']})")
            print(f"   Slots: {', '.join([s['time'] for s in res['slots']])}")

if __name__ == "__main__":
    asyncio.run(probe_march2())
