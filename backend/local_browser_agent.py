"""
Local Browser Agent — runs on YOUR Windows machine (not Docker)
================================================================
Polls for new snipe tasks from the server, opens Chrome when a slot is found,
navigates to Vatican checkout with form pre-filled, waits for you to solve
Turnstile and click BUY, captures the epay URL, sends it to Telegram.

Browser auto-closes after 20 minutes to save RAM.

Setup (run once):
  pip install playwright requests
  playwright install chromium

Run:
  python local_browser_agent.py

The script polls the server every 10 seconds for new held slots.
When one appears, it opens Chrome automatically.
"""
import asyncio
import json
import os
import sys
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
SERVER_URL = 'https://hydrabot.it'          # your server
BOT_TOKEN = '8385485516:AAF8GjzusdFNBekC8cJrTk5wGVnZtDdhAhY'
ADMIN_CHAT_ID = '6189445236'
POLL_INTERVAL = 10   # seconds between checks
BROWSER_TIMEOUT = 20 * 60  # 20 minutes in seconds
BASE = 'https://tickets.museivaticani.va'

# Profile (same as BuyerProfile in DB)
PROFILE = {
    'first_name': 'Aniile',
    'last_name': 'Skear',
    'email': 'killmongerinheret@gmail.com',
    'phone': '3481716428',
    'city': 'ROMA',
    'country': 'Afghanistan',
    'gender': 'M',
    'birth_date': {'year': 1987, 'month': 'JUN', 'day': 9},
    'language': 'en',
}
# ─────────────────────────────────────────────────────────────────────────────

processed_slots = set()  # track which slots we've already opened


def send_telegram(msg: str):
    """Send message to admin Telegram."""
    try:
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json={'chat_id': ADMIN_CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'},
            timeout=5
        )
    except Exception:
        pass


def get_pending_slots():
    """
    Poll the server for held slots that need browser checkout.
    Returns list of slot dicts.
    """
    try:
        r = requests.get(f'{SERVER_URL}/api/v1/held-slots/', timeout=8)
        if r.status_code == 200:
            return r.json().get('results', [])
    except Exception:
        pass
    return []


async def open_checkout(slot: dict):
    """
    Open Chrome, navigate to Vatican checkout for this slot.
    Pre-fills form, waits for user to solve Turnstile and click BUY.
    Captures epay URL and sends to Telegram.
    Auto-closes after 20 minutes.
    """
    from playwright.async_api import async_playwright

    date = slot.get('date', '')          # DD/MM/YYYY
    slot_time = slot.get('slot_time', '')
    visitors = slot.get('visitors', 1)
    hold_id = slot.get('id')
    ticket_name = slot.get('ticket_name', 'Vatican Museums')
    total = slot.get('total_price', '?')

    # Get participant names from slot if available
    participants = []
    try:
        notes = json.loads(slot.get('notes') or '{}')
        participants = notes.get('participants', [])
    except Exception:
        pass

    logger.info(f"\n{'='*60}")
    logger.info(f"🎫 SLOT FOUND: {date} {slot_time} | {visitors}v | €{total}")
    logger.info(f"Opening Chrome... (auto-closes in 20 min)")
    logger.info(f"{'='*60}")

    send_telegram(
        f"🌐 *Browser opening for slot:*\n"
        f"📅 {date} {slot_time} | 👥 {visitors}v | €{total}\n"
        f"Solve Turnstile and click BUY when ready."
    )

    from zoneinfo import ZoneInfo
    rome = ZoneInfo('Europe/Rome')
    day, month, year = date.split('/')
    dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
    ts = int(dt.timestamp() * 1000)
    entry_url = f'{BASE}/home/fromtag/{visitors}/{ts}/MV-Biglietti/1'

    H_XHR = {
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{BASE}/',
    }

    epay_result = {}
    start_time = time.time()

    async with async_playwright() as p:
        # Open REAL Chrome — visible on your screen
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--start-maximized',
            ]
        )
        ctx = await browser.new_context(
            locale='it-IT',
            timezone_id='Europe/Rome',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            no_viewport=True,
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            "window.chrome={runtime:{}};"
        )
        page = await ctx.new_page()

        # Capture reservation response
        async def on_response(response):
            if '/api/visit/reservation' in response.url:
                try:
                    data = await response.json()
                    if response.status == 200:
                        epay = data.get('epay', {})
                        epay_result['url'] = epay.get('url', '')
                        epay_result['reference'] = data.get('referenceOrder', '')
                        epay_result['mac'] = epay.get('mac_avvio', '')
                        epay_result['total'] = data.get('total')
                        epay_result['full'] = epay
                        logger.info(f"✅ Reservation: ref={epay_result['reference']}")
                    else:
                        logger.warning(f"Reservation failed: {response.status} {data}")
                except Exception as e:
                    logger.warning(f"Response parse: {e}")

        async def on_request(request):
            if 'epay.catholica.va/pay/public/init/' in request.url:
                import re
                m = re.search(r'/pay/public/init/([^/]+)/([^/;]+)/', request.url)
                if m:
                    epay_result['siv'] = m.group(1)
                    epay_result['mac_redirect'] = m.group(2)
                    epay_result['epay_init_url'] = request.url
                    logger.info(f"🎯 Epay: {request.url[:80]}")

        page.on('response', on_response)
        page.on('request', on_request)

        # ── Navigate ──────────────────────────────────────────────────────────
        logger.info(f"[1] Navigating to {entry_url}")
        await page.goto(entry_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(2000)

        # ── Get ticket_id ─────────────────────────────────────────────────────
        r = await page.request.get(f'{BASE}/api/search/resultPerTag',
            params={'lang':'it','visitorNum':str(visitors),'visitDate':date,
                    'area':'1','who':'','page':'0','tag':'MV-Biglietti'},
            headers=H_XHR)
        if r.status != 200:
            logger.error(f"Search failed: {r.status}")
            await browser.close()
            return

        visits = (await r.json()).get('visits', [])
        ticket = next((v for v in visits
                       if 'musei vaticani' in v.get('name','').lower()
                       and 'ingresso' in v.get('name','').lower()
                       and v.get('availability') in ('AVAILABLE','LOW_AVAILABILITY')), None)
        if not ticket:
            logger.error(f"No standard entry available for {date}")
            await browser.close()
            return

        tid = str(ticket['id'])
        logger.info(f"  ticket_id={tid} | {ticket['availability']}")

        # ── Click bookTicket ──────────────────────────────────────────────────
        logger.info(f"[2] Clicking bookTicket...")
        try:
            await page.wait_for_selector(f"[data-cy='bookTicket_{tid}']", timeout=8000)
            await page.click(f"[data-cy='bookTicket_{tid}']")
            await page.wait_for_timeout(1500)
        except Exception as e:
            logger.warning(f"  bookTicket: {e}")

        # ── Set quantity ──────────────────────────────────────────────────────
        logger.info(f"[3] Setting quantity ({visitors})...")
        try:
            qty = await page.query_selector("[data-cy='ticketQuantity']")
            if qty: await qty.click(); await page.wait_for_timeout(400)
            qty_sec = await page.query_selector("[data-cy='ticketQuantitySection']")
            if qty_sec: await qty_sec.click(); await page.wait_for_timeout(400)
            for _ in range(visitors - 1):
                q2 = await page.query_selector("[data-cy='ticketQuantity']")
                if q2: await q2.click(); await page.wait_for_timeout(300)
                q2s = await page.query_selector("[data-cy='ticketQuantitySection']")
                if q2s: await q2s.click(); await page.wait_for_timeout(300)
        except Exception as e:
            logger.debug(f"  Quantity: {e}")

        # ── Select time slot ──────────────────────────────────────────────────
        logger.info(f"[4] Selecting time {slot_time}...")
        target_mins = int(slot_time.split(':')[0]) * 60 + int(slot_time.split(':')[1])

        # Click POMERIGGIO tab if afternoon
        if target_mins >= 14 * 60:
            await page.evaluate("""
                () => {
                    const tabs = Array.from(document.querySelectorAll('.tab'))
                        .filter(el => el.offsetParent !== null);
                    for (const tab of tabs) {
                        if (tab.innerText.trim().toUpperCase().includes('POMERIGGIO')) {
                            tab.click(); return;
                        }
                    }
                    if (tabs.length >= 2) tabs[1].click();
                }
            """)
            await page.wait_for_timeout(1000)

        all_times = await page.evaluate("""
            () => Array.from(document.querySelectorAll(
                "[data-cy='time'] div.muvaCalendarNumber, [data-cy='time'] div.muvaCalendarDaySoldOut"
            )).map(el => el.innerText.trim()).filter(t => /^\\d{2}:\\d{2}$/.test(t))
        """)

        if all_times:
            exact = slot_time if slot_time in all_times else None
            best = exact or min(all_times, key=lambda t: abs(
                int(t.split(':')[0]) * 60 + int(t.split(':')[1]) - target_mins
            ))
            await page.evaluate(f"""
                () => {{
                    const els = Array.from(document.querySelectorAll(
                        "[data-cy='time'] div.muvaCalendarNumber, [data-cy='time'] div.muvaCalendarDaySoldOut"
                    )).filter(el => el.innerText.trim() === '{best}');
                    if (els.length > 0) {{ els[0].scrollIntoView(); els[0].click(); }}
                }}
            """)
            await page.wait_for_timeout(1500)
            logger.info(f"  Selected: {best}")

        # ── Click PROCEDI ─────────────────────────────────────────────────────
        logger.info(f"[5] Clicking PROCEDI...")
        for sel in ["[data-cy='bookVisit']", "button:has-text('PROCEDI')", "div.bookVisitContainer"]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(4000)
                    break
            except Exception:
                pass

        # Wait for checkout form
        try:
            await page.wait_for_selector("[data-cy='managerSurname']", timeout=15000)
            logger.info(f"  ✅ Checkout form loaded")
        except Exception:
            logger.warning(f"  Checkout form not found — URL: {page.url}")

        # ── Fill form ─────────────────────────────────────────────────────────
        logger.info(f"[6] Filling form...")

        async def fill(sel, val):
            try:
                el = await page.wait_for_selector(sel, timeout=3000)
                if el: await el.triple_click(); await el.fill(str(val))
            except Exception:
                pass

        await fill("[data-cy='managerSurname']", PROFILE['last_name'])
        await fill("[data-cy='managerName']", PROFILE['first_name'])
        await fill("[data-cy='managerCity']", PROFILE['city'])
        await fill("[data-cy='managerEmail']", PROFILE['email'])
        await fill("[data-cy='managerConfirmEmail']", PROFILE['email'])
        await fill("[data-cy='managerPhone']", PROFILE['phone'])

        # Gender
        try:
            await page.click("[data-cy='managerSex']"); await page.wait_for_timeout(400)
            opt = await page.query_selector("[data-cy='managerSexSection']")
            if opt: await opt.click(); await page.wait_for_timeout(300)
        except Exception: pass

        # Country
        try:
            await page.click("[data-cy='managerCountry']"); await page.wait_for_timeout(400)
            opt = await page.query_selector("[data-cy='managerCountrySection']")
            if opt: await opt.click(); await page.wait_for_timeout(300)
        except Exception: pass

        # Birth date
        try:
            bd = PROFILE['birth_date']
            toggle = await page.query_selector("[data-cy='managerBirthDate'] button, [data-cy='dateCalendar']")
            if toggle:
                await toggle.click(); await page.wait_for_timeout(800)
                year_btn = await page.query_selector(f"span.mat-calendar-body-cell-content:has-text('{bd['year']}')")
                if year_btn: await year_btn.click(); await page.wait_for_timeout(500)
                month_btn = await page.query_selector(f"span.mat-calendar-body-cell-content:has-text('{bd['month']}')")
                if month_btn: await month_btn.click(); await page.wait_for_timeout(500)
                day_btn = await page.query_selector(f"span.mat-calendar-body-cell-content:has-text('{bd['day']}')")
                if day_btn: await day_btn.click(); await page.wait_for_timeout(500)
        except Exception as e:
            logger.debug(f"  Birthdate: {e}")

        # Language
        try:
            await page.click("[data-cy='managerLanguage']"); await page.wait_for_timeout(400)
            opt = await page.query_selector("[data-cy='managerLanguageSection']")
            if opt: await opt.click(); await page.wait_for_timeout(300)
        except Exception: pass

        # Participants
        for i in range(visitors):
            p_first = participants[i].get('first_name', PROFILE['first_name']) if i < len(participants) else PROFILE['first_name']
            p_last = participants[i].get('last_name', PROFILE['last_name']) if i < len(participants) else PROFILE['last_name']
            await fill(f"#participantSurname_{i}", p_last)
            await fill(f"#participantName_{i}", p_first)

        # GDPR
        try:
            cb1 = await page.query_selector("#mat-mdc-checkbox-1-input")
            if cb1 and not await cb1.is_checked():
                await cb1.click(); await page.wait_for_timeout(800)
                close = await page.query_selector("[data-cy='purchase-rules-close-btn'] mat-icon")
                if close: await close.click(); await page.wait_for_timeout(400)
        except Exception: pass
        try:
            cb4 = await page.query_selector("#mat-mdc-checkbox-4-input")
            if cb4 and not await cb4.is_checked():
                await cb4.click(); await page.wait_for_timeout(300)
        except Exception: pass

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ FORM FILLED — waiting for you to:")
        logger.info(f"   1. Solve the Turnstile challenge (click the checkbox)")
        logger.info(f"   2. Click ACQUISTA / BUY")
        logger.info(f"   Browser auto-closes in 20 minutes")
        logger.info(f"{'='*60}\n")

        # ── Wait for epay (user solves Turnstile + clicks BUY) ────────────────
        deadline = time.time() + BROWSER_TIMEOUT
        while time.time() < deadline:
            await asyncio.sleep(2)
            remaining = int(deadline - time.time())

            # Check if reservation happened
            if epay_result.get('reference') or epay_result.get('siv'):
                logger.info(f"\n✅ PAYMENT INITIATED!")
                logger.info(f"Reference: {epay_result.get('reference','')}")
                logger.info(f"Epay URL: {epay_result.get('url','')}")

                # Send to Telegram
                ref = epay_result.get('reference','')
                epay_url = epay_result.get('url','')
                send_telegram(
                    f"✅ *Vatican ticket booked!*\n\n"
                    f"📅 {date} {slot_time} | 👥 {visitors}v | €{total}\n"
                    f"🔖 Ref: `{ref}`\n"
                    f"💳 Epay: {epay_url}"
                )

                # Notify server to update hold status
                try:
                    requests.post(f'{SERVER_URL}/api/v1/mark-paid/', json={
                        'hold_id': hold_id, 'reference': ref, 'epay_url': epay_url
                    }, timeout=5)
                except Exception:
                    pass

                # Keep browser open for 2 more minutes so user can complete payment
                logger.info(f"Keeping browser open for 2 more minutes...")
                await asyncio.sleep(120)
                break

            # Check if user navigated to epay
            if 'epay.catholica.va' in page.url:
                logger.info(f"✅ User navigated to epay: {page.url[:80]}")
                send_telegram(f"💳 Payment page opened for {date} {slot_time}")
                await asyncio.sleep(120)
                break

            if remaining % 60 == 0 and remaining > 0:
                logger.info(f"  Waiting for user... {remaining//60}min remaining")

        else:
            logger.warning(f"⏰ 20 minute timeout — closing browser")
            send_telegram(f"⏰ Browser timeout for {date} {slot_time} — no payment detected")

        await browser.close()
        logger.info(f"Browser closed.")


async def main():
    """Main polling loop."""
    logger.info(f"🤖 Local Browser Agent started")
    logger.info(f"Server: {SERVER_URL}")
    logger.info(f"Polling every {POLL_INTERVAL}s for new slots...")
    logger.info(f"Press Ctrl+C to stop\n")

    send_telegram(f"🤖 Local Browser Agent started on your machine")

    while True:
        try:
            slots = get_pending_slots()
            for slot in slots:
                slot_key = f"{slot.get('id')}_{slot.get('date')}_{slot.get('slot_time')}"
                if slot_key not in processed_slots and slot.get('status') in ('held', 'paying'):
                    processed_slots.add(slot_key)
                    logger.info(f"New slot: {slot.get('date')} {slot.get('slot_time')}")
                    await open_checkout(slot)
        except KeyboardInterrupt:
            logger.info("Stopped.")
            break
        except Exception as e:
            logger.error(f"Poll error: {e}")

        await asyncio.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    asyncio.run(main())
