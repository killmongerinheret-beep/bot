#!/usr/bin/env python3
"""Debug script to check actual API responses"""

import asyncio
import json
import sys
sys.path.insert(0, '/app')

from curl_cffi.requests import AsyncSession

async def test_api():
    """Test the Vatican API to see actual availability values"""
    
    # Load current session
    session_file = "/app/vatican_session.json"
    try:
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        cookies = {c['name']: c['value'] for c in session_data.get('cookies', [])}
        print(f"Loaded session with cookies: {list(cookies.keys())}")
    except Exception as e:
        print(f"No session file: {e}")
        cookies = {}
    
    # Test date and ticket
    test_cases = [
        {"date": "28/02/2026", "ticket_id": "246508836", "name": "Test Ticket"},
    ]
    
    async with AsyncSession(verify=False, impersonate="chrome120") as s:
        s.cookies.update(cookies)
        s.headers.update({
            "Referer": "https://tickets.museivaticani.va/",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest"
        })
        
        for case in test_cases:
            url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={case['ticket_id']}&visitorNum=3&visitDate={case['date']}"
            print(f"\n{'='*60}")
            print(f"Checking: {case['date']} - Ticket {case['ticket_id']}")
            print(f"URL: {url}")
            
            try:
                resp = await s.get(url, timeout=10)
                print(f"Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    timetable = data.get("timetable", [])
                    print(f"\nTotal slots in timetable: {len(timetable)}")
                    print(f"\nAll availability statuses found:")
                    
                    statuses = {}
                    for t in timetable:
                        status = t.get('availability', 'UNKNOWN')
                        time = t.get('time', 'N/A')
                        statuses[status] = statuses.get(status, 0) + 1
                        if status not in ['SOLD_OUT']:
                            print(f"  {time}: {status}")
                    
                    print(f"\nStatus summary:")
                    for status, count in sorted(statuses.items()):
                        print(f"  {status}: {count} slots")
                        
                    # Show what we would consider "available"
                    available = [t for t in timetable if t.get('availability') != 'SOLD_OUT']
                    print(f"\nSlots NOT marked SOLD_OUT: {len(available)}")
                    
                else:
                    print(f"Error response: {resp.text[:500]}")
                    
            except Exception as e:
                print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
