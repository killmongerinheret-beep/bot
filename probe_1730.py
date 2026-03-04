import asyncio, sys, os, json
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "worker_vatican")
from god_tier_monitor_v2 import GodTierVaticanMonitorV2
from curl_cffi.requests import AsyncSession

async def probe():
    m = GodTierVaticanMonitorV2()
    
    # Ensure we have a fresh session and IDs
    if not m.session_cache.get("cookies"):
        print("No cookies, refreshing session...")
        await m.refresh_session_with_browser(0, "28/03/2026")
    
    ids_cache = m.session_cache.get("ids_cache", {})
    all_ids = ids_cache.get("28/03/2026", ids_cache.get("__ALL__", []))
    
    if not all_ids:
        print("No cached IDs, refreshing...")
        await m.refresh_session_with_browser(0, "28/03/2026")
        ids_cache = m.session_cache.get("ids_cache", {})
        all_ids = ids_cache.get("28/03/2026", ids_cache.get("__ALL__", []))
    
    cookie_dict = {c['name']: c['value'] for c in m.session_cache['cookies']}
    proxy_url = m._get_proxy_url(m.current_proxy) if m.current_proxy else None
    
    rome = ZoneInfo("Europe/Rome")
    dt = datetime(2026, 3, 28, 0, 0, 0, tzinfo=rome)
    ts = int(dt.timestamp() * 1000)
    
    async with AsyncSession(
        verify=False, impersonate="chrome120",
        proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None
    ) as session:
        session.cookies.update(cookie_dict)
        session.headers.update({
            "Referer": "https://tickets.museivaticani.va/",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
        })
        
        print(f"\nProbing March 28 (TS: {ts}) for various visitor counts:")
        
        # We'll check the specific ticket ID from Task 11 and also search ALL IDs for 17:30
        task_ticket_id = "1750097398"
        
        for v_count in [1, 2, 4]:
            print(f"\n--- VISITORS: {v_count} ---")
            for item in all_ids:
                tid = str(item['id'])
                tname = item['name']
                
                # If we have many IDs, skip those clearly unrelated (only for this probe)
                if task_ticket_id not in tid and "Biglietti" not in tname:
                    continue
                
                url = (
                    f"https://tickets.museivaticani.va/api/visit/timeavail"
                    f"?lang=it&visitTypeId={tid}&visitorNum={v_count}&visitDate=28/03/2026"
                )
                
                try:
                    resp = await session.get(url, timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        timetable = data.get("timetable", [])
                        slot1730 = next((s for s in timetable if s.get("time") == "17:30"), None)
                        
                        if slot1730:
                            print(f"[{v_count} pax] {tname} ({tid}) - 17:30 status: {slot1730['availability']}")
                        else:
                            # If 17:30 not in timetable at all
                            pass
                    else:
                        print(f"ERROR {resp.status_code} for {tid}")
                except Exception as e:
                    print(f"FAILED {tid}: {e}")

asyncio.run(probe())
