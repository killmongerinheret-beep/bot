"""Debug afternoon time slot - find correct selector"""
import os, sys, django, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import BuyerProfile, Agency
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = 'https://tickets.museivaticani.va'
# Use April 17 17:30 which is also locked by us
DATE = '05/05/2026'
SLOT_TIME = '16:30'
VISITORS = 1

agency = Agency.objects.filter(is_active=True).exclude(plan='system').first()
profile = BuyerProfile.objects.filter(agency=agency).first()

async def debug():
    from playwright.async_api import async_playwright

    rome = ZoneInfo('Europe/Rome')
    day, month, year = DATE.split('/')
    dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
    ts = int(dt.timestamp() * 1000)
    entry_url = f'{BASE}/home/fromtag/{VISITORS}/{ts}/MV-Biglietti/1'
    H_XHR = {'Accept':'application/json','X-Requested-With':'XMLHttpRequest','Referer':f'{BASE}/'}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
        ctx = await browser.new_context(
            locale='it-IT', timezone_id='Europe/Rome',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            viewport={'width': 828, 'height': 915},
        )
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        page = await ctx.new_page()

        await page.goto(entry_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(2000)

        r = await page.request.get(f'{BASE}/api/search/resultPerTag',
            params={'lang':'it','visitorNum':str(VISITORS),'visitDate':DATE,'area':'1','who':'','page':'0','tag':'MV-Biglietti'},
            headers=H_XHR)
        visits = (await r.json()).get('visits', [])
        ticket = next((v for v in visits if 'musei vaticani' in v.get('name','').lower() and 'ingresso' in v.get('name','').lower()), None)
        tid = str(ticket['id']) if ticket else None
        avail = ticket.get('availability') if ticket else 'N/A'
        print(f"Ticket: tid={tid} avail={avail}")

        if not ticket or avail not in ('AVAILABLE','LOW_AVAILABILITY'):
            print("Slot locked by our recap — good! But Playwright needs an available slot.")
            print("The Playwright checkout flow is for BUYING a slot, not for locked ones.")
            print("For locked slots, use the API reservation (needs 2captcha token).")
            await browser.close()
            return

        await page.click(f"[data-cy='bookTicket_{tid}']")
        await page.wait_for_timeout(2000)

        # Get ALL time elements including hidden ones
        all_time_els = await page.evaluate("""
            () => Array.from(document.querySelectorAll("[data-cy='time'] *"))
                .filter(el => /^\\d{2}:\\d{2}$/.test(el.innerText.trim()))
                .map(el => ({
                    text: el.innerText.trim(),
                    cls: el.className,
                    visible: el.offsetParent !== null,
                    parent_cls: el.parentElement ? el.parentElement.className : ''
                }))
        """)
        print(f"\nAll time elements ({len(all_time_els)}):")
        for t in all_time_els:
            print(f"  {t['text']} | visible={t['visible']} | cls={t['cls'][:30]} | parent={t['parent_cls'][:30]}")

        # Check the showGTMobile structure from recording
        mobile_structure = await page.evaluate("""
            () => {
                const mobile = document.querySelector('div.showGTMobile');
                if (!mobile) return 'no showGTMobile';
                const divs = Array.from(mobile.querySelectorAll(':scope > div > div'));
                return divs.map((el, i) => ({
                    index: i,
                    cls: el.className.substring(0,50),
                    text: el.innerText.trim().substring(0,40),
                    visible: el.offsetParent !== null
                }));
            }
        """)
        print(f"\nshowGTMobile > div > div structure:")
        for s in mobile_structure[:10]:
            print(f"  [{s['index']}] cls={s['cls'][:40]} | '{s['text'][:30]}' | visible={s['visible']}")

        await page.screenshot(path='/tmp/afternoon_debug.png')
        print(f"\nScreenshot: /tmp/afternoon_debug.png")
        await browser.close()

asyncio.run(debug())
