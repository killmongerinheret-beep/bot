"""
Debug script — opens Vatican page and dumps the exact DOM selectors
for the PRENOTA button so we can fix the agent.
"""
import asyncio
import subprocess
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

DATE = '13/05/2026'
VISITORS = 1
BASE = 'https://tickets.museivaticani.va'
CHROME_PROFILE = r"d:\bot\vatican_chrome_profile"
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

# Get fresh ticket_id
s = requests.Session()
s.get(f'{BASE}/home', timeout=8)
r = s.get(f'{BASE}/api/search/resultPerTag', params={
    'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': DATE,
    'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
}, headers={'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}, timeout=10)
ticket = next((v for v in r.json().get('visits', [])
               if 'musei vaticani' in v.get('name', '').lower()
               and 'ingresso' in v.get('name', '').lower()), None)
TID = str(ticket['id']) if ticket else 'UNKNOWN'
print(f"ticket_id from API: {TID}")

rome = ZoneInfo('Europe/Rome')
day, month, year = DATE.split('/')
ts = int(datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome).timestamp() * 1000)
entry_url = f'{BASE}/home/visit/{VISITORS}/{ts}/1'
print(f"URL: {entry_url}")


async def debug():
    import nodriver as uc

    # Kill leftover
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], capture_output=True)
    await asyncio.sleep(1)
    lockfile = os.path.join(CHROME_PROFILE, 'lockfile')
    if os.path.exists(lockfile):
        try: os.remove(lockfile)
        except: pass

    browser = await uc.start(
        user_data_dir=CHROME_PROFILE,
        browser_executable_path=CHROME_PATH,
        headless=False,
        lang='it-IT',
    )
    tab = browser.main_tab

    await tab.get(f'{BASE}/home')
    await tab.sleep(3)
    await tab.get(entry_url)
    await tab.sleep(5)

    print("\n=== DOM DEBUG ===")

    # 1. What ticket IDs exist in the DOM?
    dom_ids = await tab.evaluate("""
        Array.from(document.querySelectorAll('[id^="ticket_"]')).map(el => ({
            id: el.id,
            tag: el.tagName,
            classes: el.className.substring(0, 60)
        }))
    """)
    print(f"\n[ticket_ elements]: {dom_ids}")

    # 2. What data-cy attributes exist?
    data_cy = await tab.evaluate("""
        Array.from(document.querySelectorAll('[data-cy]')).map(el => el.getAttribute('data-cy')).filter(Boolean)
    """)
    print(f"\n[data-cy values]: {data_cy}")

    # 3. What do PRENOTA buttons look like?
    prenota = await tab.evaluate("""
        Array.from(document.querySelectorAll('button, a')).filter(el =>
            el.innerText && el.innerText.trim().toUpperCase().includes('PRENOTA')
        ).map(el => ({
            tag: el.tagName,
            text: el.innerText.trim(),
            id: el.id,
            dataCy: el.getAttribute('data-cy'),
            classes: el.className.substring(0, 80),
            parentId: el.parentElement?.id,
            parentDataCy: el.parentElement?.getAttribute('data-cy')
        }))
    """)
    print(f"\n[PRENOTA buttons]: {prenota}")

    # 4. Check if ticket_id from API matches DOM
    tid_in_dom = await tab.evaluate(f"!!document.querySelector('#ticket_{TID}')")
    print(f"\n[#ticket_{TID} in DOM]: {tid_in_dom}")

    # 5. Check bookTicket data-cy
    book_btn = await tab.evaluate(f"!!document.querySelector(\"[data-cy='bookTicket_{TID}']\")")
    print(f"\n[[data-cy='bookTicket_{TID}'] in DOM]: {book_btn}")

    # 6. All visible buttons text
    buttons = await tab.evaluate("""
        Array.from(document.querySelectorAll('button')).filter(el => el.offsetParent !== null).map(el => ({
            text: el.innerText.trim().substring(0, 40),
            dataCy: el.getAttribute('data-cy'),
            id: el.id
        }))
    """)
    print(f"\n[Visible buttons]: {buttons}")

    print("\n=== Keeping browser open for 60s — inspect manually ===")
    await tab.sleep(60)
    browser.stop()


asyncio.run(debug())
