import asyncio, sys, os, json
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "worker_vatican")
from god_tier_monitor_v2 import GodTierVaticanMonitorV2

async def dump_ids():
    m = GodTierVaticanMonitorV2()
    date_str = "02/03/2026"
    
    if not m.session_cache.get("cookies"):
        await m.refresh_session_with_browser(0, date_str)
        
    id_cache = m.session_cache.get("ids_cache", {})
    all_known = id_cache.get(date_str, id_cache.get("__ALL__", []))
    
    print(f"--- Harvested IDs for {date_str} ---")
    for item in all_known:
        print(f"ID: {item['id']} | Name: {item['name']}")

if __name__ == "__main__":
    asyncio.run(dump_ids())
