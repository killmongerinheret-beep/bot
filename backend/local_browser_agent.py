"""
Local Browser Agent — runs on YOUR Windows machine (not Docker)
================================================================
Polls for new snipe tasks from the server, opens Chrome when a slot is found,
navigates to Vatican checkout with form pre-filled, waits for you to solve
Turnstile and click BUY, captures the epay URL, sends it to Telegram.

Browser auto-closes after 20 minutes to save RAM.

Setup (run once in PowerShell):
  python -m pip install playwright requests
  python -m playwright install chromium

Run:
  python local_browser_agent.py
  (or double-click run_agent.bat)

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

# Which Telegram group triggers browser opening (WOR group chat_id)
# Set this to your WOR group chat_id — get it by running /start in the group
# and checking the bot logs, or use /chatid command
TRIGGER_GROUP_CHAT_ID = '-5245239270'  # WOR Bot group

# Profile (same as BuyerProfile in DB)
PROFILE = {
    'first_name': 'Great',
    'last_name': 'Aby',
    'email': 'wondersoffcity@gmail.com',
    'phone': '3517869798',
    'city': 'Roma',
    'country': 'Italy',
    'gender': 'M',
    'birth_date': {'year': 2000, 'month': 'JUL', 'day': 25},
    'language': 'en',
}
# ─────────────────────────────────────────────────────────────────────────────

CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
# Use a dedicated Chrome profile for the agent (separate from your main Chrome)
# This avoids conflicts when Chrome is already running
CHROME_PROFILE = os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Google\Chrome\VaticanAgent')
last_update_id = 0      # Telegram update offset


def send_telegram(chat_id: str, msg: str, reply_markup=None):
    """Send message to a Telegram chat."""
    payload = {'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json=payload, timeout=5
        )
    except Exception:
        pass


def answer_callback(callback_query_id: str, text: str = ''):
    """Answer a Telegram callback query (removes loading spinner)."""
    try:
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery',
            json={'callback_query_id': callback_query_id, 'text': text},
            timeout=5
        )
    except Exception:
        pass


def get_telegram_updates():
    """Poll server for pending browser open requests (button clicks handled by main bot)."""
    try:
        r = requests.get(f'{SERVER_URL}/api/v1/browser-pending/', timeout=8)
        if r.status_code == 200:
            return r.json().get('requests', [])
    except Exception:
        pass
    return []


def get_trigger_group():
    """Get the configured browser trigger group from server."""
    try:
        r = requests.get(f'{SERVER_URL}/api/v1/browser-trigger-group/', timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get('chat_id', TRIGGER_GROUP_CHAT_ID)
    except Exception:
        pass
    return TRIGGER_GROUP_CHAT_ID


def get_pending_slots():
    """Poll the server for held slots that need browser checkout."""
    try:
        r = requests.get(f'{SERVER_URL}/api/v1/held-slots/?status=held', timeout=8)
        if r.status_code == 200:
            return r.json().get('results', [])
    except Exception:
        pass
    return []
    """Poll the server for held slots that need browser checkout."""
    try:
        r = requests.get(f'{SERVER_URL}/api/v1/held-slots/?status=held', timeout=8)
        if r.status_code == 200:
            return r.json().get('results', [])
    except Exception:
        pass
    return []


def notify_slot_with_button(slot: dict):
    """Send slot notification to the trigger group with Open Browser button."""
    date = slot.get('date', '')
    slot_time = slot.get('slot_time', '')
    visitors = slot.get('visitors', 1)
    total = slot.get('total_price', '?')
    hold_id = slot.get('id')

    msg = (
        f"🎫 *Slot Available — Open Browser to Book*\n\n"
        f"📅 {date} {slot_time}\n"
        f"👥 {visitors} visitors | €{total}\n\n"
        f"Click the button to open Chrome on your machine.\n"
        f"Form will be pre-filled — just solve Turnstile and click BUY."
    )
    reply_markup = {
        'inline_keyboard': [[
            {'text': '🌐 Open Browser', 'callback_data': f'open_browser:{hold_id}'}
        ]]
    }
    send_telegram(TRIGGER_GROUP_CHAT_ID, msg, reply_markup)
    logger.info(f"📢 Sent browser button to group {TRIGGER_GROUP_CHAT_ID}")


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

    # Fetch profile from server, fall back to hardcoded PROFILE
    profile_data = PROFILE.copy()
    try:
        r = requests.get(f'{SERVER_URL}/api/v1/buyer-profile/', timeout=5)
        if r.status_code == 200:
            srv = r.json()
            if srv.get('first_name'):
                profile_data.update({
                    'first_name': srv.get('first_name', profile_data['first_name']),
                    'last_name': srv.get('last_name', profile_data['last_name']),
                    'email': srv.get('email', profile_data['email']),
                    'phone': srv.get('phone', profile_data['phone']),
                    'city': srv.get('city', profile_data['city']),
                    'country': srv.get('country', profile_data['country']),
                })
                logger.info(f"  Profile from server: {profile_data['first_name']} {profile_data['last_name']}")
    except Exception:
        pass
    logger.info(f"  Using profile: {profile_data['first_name']} {profile_data['last_name']}")

    send_telegram(
        TRIGGER_GROUP_CHAT_ID,
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
        # Launch REAL Chrome via CDP — Cloudflare cannot detect this
        import subprocess, tempfile, shutil

        # Create a temp profile copied from your real Chrome profile
        # This gives Cloudflare real browser signals (cookies, history, etc.)
        real_profile = os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Google\Chrome\User Data')
        temp_profile = os.path.join(tempfile.gettempdir(), 'vatican_chrome_profile')

        # Copy Default profile if temp doesn't exist yet
        if not os.path.exists(temp_profile):
            try:
                src = os.path.join(real_profile, 'Default')
                dst = os.path.join(temp_profile, 'Default')
                if os.path.exists(src):
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                        'Cache', 'Code Cache', 'GPUCache', 'ShaderCache',
                        'Service Worker', 'CacheStorage', '*.log'
                    ))
                    logger.info(f"  Copied Chrome profile to temp")
            except Exception as e:
                logger.debug(f"  Profile copy: {e}")

        # Launch Chrome with remote debugging on port 9222
        debug_port = 9222
        chrome_proc = subprocess.Popen([
            CHROME_PATH,
            f'--remote-debugging-port={debug_port}',
            f'--user-data-dir={temp_profile}',
            '--profile-directory=Default',
            '--no-first-run',
            '--no-default-browser-check',
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
            'about:blank',
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Wait for Chrome to start
        await asyncio.sleep(2)

        # Connect Playwright to the running Chrome
        try:
            browser = await p.chromium.connect_over_cdp(f'http://localhost:{debug_port}')
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()
            logger.info(f"  Connected to real Chrome via CDP")
        except Exception as e:
            logger.error(f"  CDP connect failed: {e} — falling back to Playwright Chromium")
            chrome_proc.terminate()
            # Fallback to Playwright Chromium
            browser = await p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled',
                      '--start-maximized']
            )
            ctx = await browser.new_context(
                locale='it-IT', timezone_id='Europe/Rome',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 900},
            )
            await ctx.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                "window.chrome={runtime:{},loadTimes:function(){},csi:function(){},app:{isInstalled:false}};"
            )
            page = await ctx.new_page()
            chrome_proc = None

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

        await fill("[data-cy='managerSurname']", profile_data['last_name'])
        await fill("[data-cy='managerName']", profile_data['first_name'])
        await fill("[data-cy='managerCity']", profile_data['city'])
        await fill("[data-cy='managerEmail']", profile_data['email'])
        # Confirm email — click div 7 first (from recording), then fill
        try:
            div7 = await page.query_selector("div.muvaManagerContainer div > div:nth-of-type(7)")
            if div7: await div7.click(); await page.wait_for_timeout(200)
        except Exception: pass
        await fill("[data-cy='managerConfirmEmail']", profile_data['email'])
        await fill("[data-cy='managerPhone']", profile_data['phone'])

        # Gender
        try:
            await page.click("[data-cy='managerSex']"); await page.wait_for_timeout(400)
            opt = await page.query_selector("[data-cy='managerSexSection']")
            if opt: await opt.click(); await page.wait_for_timeout(300)
        except Exception: pass

        # Country — has search field to filter
        try:
            await page.click("[data-cy='managerCountry']"); await page.wait_for_timeout(400)
            search = await page.query_selector("#searchInput_country")
            if search:
                await search.fill(profile_data['country'][:4])
                await page.wait_for_timeout(500)
            opt = await page.query_selector("[data-cy='managerCountrySection']")
            if opt: await opt.click(); await page.wait_for_timeout(300)
        except Exception: pass

        # Birth date
        try:
            bd = profile_data['birth_date']
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
            # Expand participant section if needed (participant 2+ are collapsed)
            if i > 0:
                try:
                    expand = await page.query_selector(f"#participantElement_{i} div.tw-flex-grow > div")
                    if expand: await expand.click(); await page.wait_for_timeout(500)
                except Exception: pass
            p_first = participants[i].get('first_name', profile_data['first_name']) if i < len(participants) else profile_data['first_name']
            p_last = participants[i].get('last_name', profile_data['last_name']) if i < len(participants) else profile_data['last_name']
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
                    TRIGGER_GROUP_CHAT_ID,
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
                send_telegram(TRIGGER_GROUP_CHAT_ID, f"💳 Payment page opened for {date} {slot_time}")
                await asyncio.sleep(120)
                break

            if remaining % 60 == 0 and remaining > 0:
                logger.info(f"  Waiting for user... {remaining//60}min remaining")

        else:
            logger.warning(f"⏰ 20 minute timeout — closing browser")
            send_telegram(TRIGGER_GROUP_CHAT_ID, f"⏰ Browser timeout for {date} {slot_time} — no payment detected")

        await browser.close()
        # Also terminate the Chrome process if we launched it
        try:
            if chrome_proc and chrome_proc.poll() is None:
                chrome_proc.terminate()
        except Exception:
            pass
        logger.info(f"Browser closed.")


async def main():
    """
    Main loop:
    1. Poll server for new held slots → send button to WOR group
    2. Poll Telegram for button clicks → open Chrome
    """
    global last_update_id

    logger.info(f"🤖 Vatican Browser Agent started")
    logger.info(f"Server: {SERVER_URL}")
    logger.info(f"Trigger group: {TRIGGER_GROUP_CHAT_ID}")
    logger.info(f"Polling every {POLL_INTERVAL}s...")
    logger.info(f"Press Ctrl+C to stop\n")

    send_telegram(ADMIN_CHAT_ID, f"🤖 Browser Agent started on your machine\nWaiting for slots in group `{TRIGGER_GROUP_CHAT_ID}`")

    # pending_browser: hold_id → slot dict (waiting for button click)
    pending_browser = {}
    processing_holds = set()  # prevent duplicate browser opens

    while True:
        try:
            # ── Check for new held slots ──────────────────────────────────────
            slots = get_pending_slots()
            for slot in slots:
                hold_id = slot.get('id')
                slot_key = f"{hold_id}_{slot.get('date')}_{slot.get('slot_time')}"
                if slot_key not in processed_slots and slot.get('status') in ('held', 'paying'):
                    processed_slots.add(slot_key)
                    pending_browser[str(hold_id)] = slot
                    notify_slot_with_button(slot)
                    logger.info(f"New slot notified: {slot.get('date')} {slot.get('slot_time')}")

            # ── Check for browser open requests (auto + button clicks) ─────────
            pending_reqs = get_telegram_updates()
            for req in pending_reqs:
                data = req.get('data', '')
                user_name = req.get('user', 'Auto')
                is_auto = req.get('auto', False)

                logger.info(f"📥 {'Auto' if is_auto else 'Button'} browser request from {user_name}")

                if data.startswith('open_browser:'):
                    parts = data.split(':')
                    hold_id = parts[1]

                    # Deduplicate
                    if hold_id in processing_holds:
                        logger.debug(f"Hold #{hold_id} already processing — skip")
                        continue
                    processing_holds.add(hold_id)
                    slot = pending_browser.get(hold_id)

                    # Try to decode embedded slot info (format: open_browser:{id}:{base64})
                    if not slot and len(parts) >= 3:
                        try:
                            import base64
                            slot_info = base64.b64decode(parts[2]).decode()
                            s_parts = slot_info.split('|')
                            slot = {
                                'id': hold_id,
                                'date': s_parts[0],
                                'slot_time': s_parts[1],
                                'slot_id': s_parts[2] if len(s_parts) > 2 else '',
                                'visitors': int(s_parts[3]) if len(s_parts) > 3 else 1,
                                'total_price': s_parts[4] if len(s_parts) > 4 else '?',
                            }
                            logger.info(f"  Decoded slot: {slot['date']} {slot['slot_time']}")
                        except Exception as e:
                            logger.warning(f"  Could not decode slot info: {e}")

                    if not slot:
                        # Last resort: build minimal slot and let agent do full flow
                        slot = {'id': hold_id, 'date': None, 'slot_time': None,
                                'visitors': 1, 'total_price': '?'}
                        logger.warning(f"  Using minimal slot for hold #{hold_id}")

                    send_telegram(TRIGGER_GROUP_CHAT_ID,
                        f"🌐 *{user_name}* clicked Open Browser\n"
                        f"Chrome opening for {slot.get('date','?')} {slot.get('slot_time','?')}...")
                    logger.info(f"Opening Chrome for hold #{hold_id} — {slot.get('date')} {slot.get('slot_time')}")
                    asyncio.create_task(open_checkout(slot))

                elif data.startswith('open_browser_slot:'):
                    import base64
                    # Deduplicate by slot data
                    slot_key = data[:60]
                    if slot_key in processing_holds:
                        logger.debug(f"Slot already processing — skip")
                        continue
                    processing_holds.add(slot_key)
                    try:
                        slot_info = base64.b64decode(data.split(':', 1)[1]).decode()
                        s_parts = slot_info.split('|')
                        date_str = s_parts[0]
                        slot_time_str = s_parts[1]
                        slot_id_str = s_parts[2] if len(s_parts) > 2 else ''
                        visitors_n = int(s_parts[3]) if len(s_parts) > 3 else 1
                        total_str = s_parts[4] if len(s_parts) > 4 else '?'
                        slot = {
                            'date': date_str, 'slot_time': slot_time_str,
                            'slot_id': slot_id_str, 'visitors': visitors_n,
                            'total_price': total_str, 'id': None,
                        }
                        send_telegram(TRIGGER_GROUP_CHAT_ID,
                            f"🌐 *{user_name}* clicked Open Browser\n"
                            f"Chrome opening for {date_str} {slot_time_str}...")
                        logger.info(f"Opening Chrome for {date_str} {slot_time_str}")
                        asyncio.create_task(open_checkout(slot))
                    except Exception as e:
                        logger.error(f"open_browser_slot error: {e}")

        except KeyboardInterrupt:
            logger.info("Stopped.")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    import sys
    # Watchdog: restart on crash
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Agent stopped by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Agent crashed: {e} — restarting in 10s...")
            import time as _t
            _t.sleep(10)
