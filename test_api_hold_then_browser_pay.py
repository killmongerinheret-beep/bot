"""
Modified version of test_headful_hold_challenge.py
===================================================
1. Use browser to get JSESSIONID (2 minutes)
2. Close browser
3. Keep hold alive via API (70 minutes, 50 MB RAM)
4. Open browser again for payment (5 minutes)

RAM savings: 800 MB → 50 MB during holding phase
"""
import asyncio
import requests
import time
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from monitors.models import HeldSlot, MonitorTask
from worker_vatican.search_api_monitor import VaticanSearchAPIMonitor

BASE = 'https://tickets.museivaticani.va'
VISITORS = 1
TARGET_DATE = "04/05/2026"


async def get_jsessionid_with_browser(slot_info):
    """
    Use browser ONLY to get JSESSIONID (2 minutes).
    Then close browser immediately.
    """
    import nodriver as uc
    import subprocess
    
    print(f"\n🌐 Opening browser to get JSESSIONID...")
    
    # Kill existing Chrome
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'],
                   capture_output=True, timeout=5)
    await asyncio.sleep(1)
    
    browser = await uc.start(
        user_data_dir=r'd:\bot\vatican_chrome_profile',
        browser_executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        headless=False,
        lang='it-IT',
    )
    
    tab = browser.main_tab
    
    try:
        # Navigate to Vatican
        from zoneinfo import ZoneInfo
        rome = ZoneInfo('Europe/Rome')
        day, month, year = slot_info['date'].split('/')
        dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
        ts = int(dt.timestamp() * 1000)
        entry_url = f"{BASE}/home/fromtag/{slot_info['visitors']}/{ts}/MV-Biglietti/1"
        
        print(f"   [1] Navigating to {entry_url}")
        await tab.get(entry_url)
        await tab.sleep(4)
        
        # Get JSESSIONID from cookies
        cookies = await tab.browser.cookies.get_all()
        jsessionid = next((c.value for c in cookies 
                          if c.name == 'JSESSIONID' 
                          and 'museivaticani' in (c.domain or '')), None)
        
        if not jsessionid:
            print(f"   ❌ No JSESSIONID found")
            return None
        
        print(f"   ✅ Got JSESSIONID: {jsessionid[:20]}...")
        return jsessionid
    
    finally:
        print(f"   🔒 Closing browser (RAM freed)")
        try:
            browser.stop()
        except:
            pass
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'],
                       capture_output=True, timeout=5)


def hold_via_api(slot_info, jsessionid):
    """
    Call /api/visit/recap to hold the slot (no browser).
    """
    print(f"\n🔒 Holding slot via API...")
    
    s = requests.Session()
    s.cookies.set('JSESSIONID', jsessionid, domain='.museivaticani.va')
    
    # Get fresh ticket_id
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it',
        'visitorNum': str(slot_info['visitors']),
        'visitDate': slot_info['date'],
        'area': '1',
        'who': '',
        'page': '0',
        'tag': 'MV-Biglietti'
    }, timeout=10)
    
    ticket = next((v for v in r.json().get('visits', [])
                   if 'musei vaticani' in v.get('name', '').lower()
                   and 'ingresso' in v.get('name', '').lower()), None)
    
    if not ticket:
        print(f"   ❌ Ticket not found")
        return None
    
    ticket_id = ticket['id']
    
    # Call recap API
    recap_body = {
        "visitId": str(slot_info['slot_id']),
        "visitTypeId": int(ticket_id),
        "visitorNum": int(slot_info['visitors']),
        "lang": "it",
        "tickets": [
            {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": str(slot_info['visitors'])},
            {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": "0"},
        ],
        "additionalCosts": {
            "service-0": {"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": slot_info['visitors']}
        },
        "services": [
            {"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": slot_info['visitors']}
        ]
    }
    
    r = s.post(f'{BASE}/api/visit/recap', json=recap_body, timeout=10)
    
    if r.status_code != 200:
        print(f"   ❌ Recap failed: {r.status_code}")
        return None
    
    recap_data = r.json()
    recap_id = recap_data.get('recapId') or recap_data.get('id')
    total = recap_data.get('total', 0)
    
    print(f"   ✅ Slot held!")
    print(f"   Recap ID: {recap_id}")
    print(f"   Total: €{total}")
    
    return {
        'jsessionid': jsessionid,
        'recap_id': recap_id,
        'total': total,
        'ticket_id': ticket_id,
    }


def keep_alive_api(slot_info, hold_data, duration_minutes=70):
    """
    Keep hold alive via API recap (no browser).
    RAM usage: ~50 MB
    """
    print(f"\n💓 Keeping hold alive via API (no browser)")
    print(f"   Duration: {duration_minutes} minutes")
    print(f"   Interval: 4 minutes")
    print(f"   RAM: ~50 MB\n")
    
    s = requests.Session()
    s.cookies.set('JSESSIONID', hold_data['jsessionid'], domain='.museivaticani.va')
    
    start_time = time.time()
    recap_count = 0
    
    while True:
        elapsed_min = (time.time() - start_time) / 60
        
        if elapsed_min >= duration_minutes:
            print(f"\n🎉 {duration_minutes} minutes reached!")
            print(f"   Total recaps: {recap_count}")
            break
        
        if recap_count > 0:
            time.sleep(240)  # 4 minutes
        
        # Resolve fresh ticket_id
        r = s.get(f'{BASE}/api/search/resultPerTag', params={
            'lang': 'it',
            'visitorNum': str(slot_info['visitors']),
            'visitDate': slot_info['date'],
            'area': '1',
            'who': '',
            'page': '0',
            'tag': 'MV-Biglietti'
        }, timeout=10)
        
        ticket = next((v for v in r.json().get('visits', [])
                       if 'musei vaticani' in v.get('name', '').lower()
                       and 'ingresso' in v.get('name', '').lower()), None)
        
        if not ticket:
            print(f"   ⚠️ Ticket not found - using cached ID")
            ticket_id = hold_data['ticket_id']
        else:
            ticket_id = ticket['id']
        
        # Re-call recap
        recap_body = {
            "visitId": str(slot_info['slot_id']),
            "visitTypeId": int(ticket_id),
            "visitorNum": int(slot_info['visitors']),
            "lang": "it",
            "tickets": [
                {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": str(slot_info['visitors'])},
                {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": "0"},
            ],
            "additionalCosts": {
                "service-0": {"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": slot_info['visitors']}
            },
            "services": [
                {"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": slot_info['visitors']}
            ]
        }
        
        r = s.post(f'{BASE}/api/visit/recap', json=recap_body, timeout=10)
        
        recap_count += 1
        remaining = duration_minutes - elapsed_min
        
        if r.status_code == 200:
            print(f"   💓 Recap #{recap_count} OK | Remaining: {remaining:.1f} min")
        else:
            print(f"   ⚠️ Recap #{recap_count} failed ({r.status_code}) | Remaining: {remaining:.1f} min")


async def main():
    """
    Flow:
    1. Find slot via API
    2. Open browser to get JSESSIONID (2 min)
    3. Close browser
    4. Hold via API (no browser)
    5. Keep alive via API for 70 min (no browser) - 50 MB RAM
    6. [Future] Open browser for payment (5 min)
    """
    print("="*60)
    print("  Vatican API-Only Holding Test")
    print("  Browser: 2 min (get JSESSIONID) + 5 min (payment)")
    print("  API: 70 min (holding) - 50 MB RAM")
    print("="*60)
    
    # Step 1: Find slot via API
    monitor = VaticanSearchAPIMonitor()
    success, slots, tid = monitor.check_ticket(
        target_date=TARGET_DATE,
        ticket_name="Musei Vaticani - Biglietti d'ingresso",
        visitors=VISITORS
    )
    
    if not success or not slots:
        print(f"❌ No slots found for {TARGET_DATE}")
        return
    
    slot_info = {
        'date': TARGET_DATE,
        'slot_id': slots[0]['id'],
        'slot_time': slots[0]['time'],
        'visitors': VISITORS,
    }
    
    print(f"\n✅ Found slot: {slot_info['date']} {slot_info['slot_time']}")
    
    # Step 2: Get JSESSIONID with browser (2 min)
    jsessionid = await get_jsessionid_with_browser(slot_info)
    if not jsessionid:
        return
    
    print(f"\n{'='*60}")
    print(f"  BROWSER CLOSED")
    print(f"  RAM freed: 800 MB → 50 MB")
    print(f"{'='*60}")
    
    # Step 3: Hold via API (no browser)
    hold_data = hold_via_api(slot_info, jsessionid)
    if not hold_data:
        return
    
    # Step 4: Keep alive for 70 min (no browser)
    keep_alive_api(slot_info, hold_data, duration_minutes=70)
    
    print(f"\n{'='*60}")
    print(f"  HOLD COMPLETE")
    print(f"  Ready for payment (will open browser for 5 min)")
    print(f"{'='*60}")


if __name__ == '__main__':
    asyncio.run(main())
