import asyncio
import os
import sys
import json
import time
from datetime import datetime, timedelta
import requests
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import argparse
import subprocess
import shutil
import tempfile

# Add root to path for worker_vatican
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

#  CONFIG 
VATICAN_BASE = 'https://tickets.museivaticani.va'
VISITORS = 2
ADULTS = 2
CHILDREN = 0
LOOKAHEAD_DAYS = 90
HEARTBEAT_INTERVAL_MS = 240000  # 4 minutes
TARGET_TICKET_NAME = "Musei Vaticani - Biglietti d'ingresso"
PREFERRED_TEST_DATE = "01/05/2026"
PREFERRED_SLOT_TIME = ""            # empty = take first available slot
PERSISTENT_PROFILE_PATH = r"C:\Users\gotic\AppData\Local\Temp\vatican_chrome_profile"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.178 Safari/537.36"
# 

async def find_available_slot():
    """Check PREFERRED_TEST_DATE first, then scan forward if not found."""
    VATICAN_BASE_URL = 'https://tickets.museivaticani.va'
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': USER_AGENT,
        'Referer': f'{VATICAN_BASE}/',
    }

    # Build date list: preferred date first, then scan forward from it
    try:
        pd_day, pd_month, pd_year = PREFERRED_TEST_DATE.split('/')
        preferred_dt = datetime(int(pd_year), int(pd_month), int(pd_day))
    except Exception:
        preferred_dt = datetime.now()

    dates_to_check = []
    for i in range(LOOKAHEAD_DAYS):
        d = (preferred_dt + timedelta(days=i)).strftime('%d/%m/%Y')
        dates_to_check.append(d)

    print(f"SEARCHING from {PREFERRED_TEST_DATE} (target time: {PREFERRED_SLOT_TIME}, visitors: {VISITORS})...")

    # Init a persistent session (Vatican needs homepage hit first)
    session = requests.Session()
    try:
        session.get(f'{VATICAN_BASE_URL}/home', headers={'User-Agent': USER_AGENT}, timeout=10)
    except Exception:
        pass

    for date_str in dates_to_check:
        try:
            day, month, year = date_str.split('/')
            current_dt = datetime(int(year), int(month), int(day))
        except Exception:
            continue

        if current_dt.weekday() == 6:  # Skip Sundays
            continue

        sys.stdout.write(f"\r  Checking {date_str}... ")
        sys.stdout.flush()

        try:
            # Step 1: get ticket_id
            r = session.get(f'{VATICAN_BASE_URL}/api/search/resultPerTag', params={
                'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': date_str,
                'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
            }, headers=headers, timeout=10)

            if r.status_code != 200:
                await asyncio.sleep(0.3)
                continue

            visits = r.json().get('visits', [])
            ticket = next(
                (v for v in visits
                 if 'musei vaticani' in v.get('name', '').lower()
                 and 'ingresso' in v.get('name', '').lower()),
                None
            )
            if not ticket:
                await asyncio.sleep(0.3)
                continue

            tid = ticket['id']

            # Step 2: get available time slots
            r2 = session.get(f'{VATICAN_BASE_URL}/api/visit/timeavail', params={
                'lang': 'it', 'visitLang': '',
                'visitTypeId': str(tid),
                'visitorNum': str(VISITORS),
                'visitDate': date_str,
            }, headers=headers, timeout=10)

            if r2.status_code != 200:
                await asyncio.sleep(0.3)
                continue

            timetable = r2.json().get('timetable', [])
            available = [
                s for s in timetable
                if s.get('availability') in ('AVAILABLE', 'LOW_AVAILABILITY')
            ]

            if available:
                # Prefer the exact target time if set
                target = next((s for s in available if s.get('time') == PREFERRED_SLOT_TIME), None)
                best = target if target else available[0]
                print(f"\nFOUND SLOT! {date_str} at {best.get('time')}")
                return {
                    'date': date_str,
                    'slot_id': str(best.get('id')),
                    'slot_time': best.get('time'),
                    'ticket_id': str(tid),
                    'visitors': VISITORS,
                }
        except Exception as e:
            print(f"\nERROR checking {date_str}: {e}")

        await asyncio.sleep(0.3)

    print("\nNo slots found in the next 90 days.")
    return None

async def run_hold_challenge(slot_info):
    """
    Launch Playwright, fill form, and start heartbeat.
    """
    # Hardcoded profile — edit these with your real buyer details
    profile_data = {
        'first_name': 'Mario',
        'last_name': 'Rossi',
        'email': 'mario.rossi@example.com',
        'phone': '+393401234567',
        'city': 'Roma',
        'country': 'Italy',
    }
    
    async with async_playwright() as p:
        # Launch REAL Chrome via CDP (Anti-Cloudflare logic)
        chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
        
        # Setup Mode - If slot_info is None, we just open the browser and wait
        is_setup = slot_info is None
        if is_setup:
            print("\nSETUP MODE: Opening browser for manual sign-in/trusted session...")
        else:
            print("\nStarting Headful Hold Challenge...")
        
        # NO PROXY for browser — Vatican Cloudflare trusts your real IP more than proxy IPs
        # Proxies change fingerprint and lower Cloudflare trust score
        proxy_args = []
        print(" No proxy for browser (better Cloudflare trust with real IP)")

        print(" Launching real Chrome via CDP to bypass Cloudflare...")
        debug_port = 9222

        # Kill any existing Chrome first so we always start fresh from the saved profile
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'],
                       capture_output=True)
        await asyncio.sleep(1)

        chrome_cmd = [
            chrome_path,
            f'--remote-debugging-port={debug_port}',
            f'--user-data-dir={PERSISTENT_PROFILE_PATH}',
            '--profile-directory=Default',
            '--no-first-run',
            '--no-default-browser-check',
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
            '--ignore-gpu-blocklist',
            '--enable-webgl',
            '--enable-accelerated-2d-canvas',
            '--disable-features=IsolateOrigins,site-per-process',
            f'--user-agent={USER_AGENT}',
            'about:blank',
        ]

        chrome_proc = subprocess.Popen(
            chrome_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        await asyncio.sleep(3)

        try:
            browser = await p.chromium.connect_over_cdp(f'http://localhost:{debug_port}')
            # Respect the existing context from the profile, but set locale/UA if needed
            if not browser.contexts:
                ctx = await browser.new_context(
                    locale='it-IT', timezone_id='Europe/Rome',
                    user_agent=USER_AGENT,
                    ignore_https_errors=True
                )
            else:
                ctx = browser.contexts[0]

            page = await ctx.new_page()
            await Stealth().apply_stealth_async(page)
            print("   Connected to real Chrome with Stealth")
            
            if is_setup:
                print("Manual Setup Mode active. Please sign in and established trusted session.")
                print("Once done, close Chrome or press Ctrl+C to end setup.")
                while True: await asyncio.sleep(60)

            # Filter noisy garbage from Cloudflare/Vatican internal scripts
            def console_filter(msg):
                txt = msg.text
                # Suppress known junk patterns
                junk = ["Private Access Token", "401", "xr-spatial-tracking", "600010", 
                        "NaN", "font-size:0", "JSHandle", "/.*.*=.*/", "native code", "cmg/1", "preload"]
                if any(x in txt for x in junk):
                    return
                # Ignore very short or purely technical/regex-looking messages
                if len(txt) < 5 or txt.startswith("/") or "function" in txt:
                    return
                print(f"  [BROWSER] {txt}")

            page.on("console", console_filter)
            
        except Exception as e:
            print(f" CDP failed: {e}. Falling back to standard browser...")
            browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
            ctx = await browser.new_context(
                    locale='it-IT', timezone_id='Europe/Rome',
                    user_agent=USER_AGENT,
                    ignore_https_errors=True
                )
            page = await ctx.new_page()
            await Stealth().apply_stealth_async(page)

        # Build Entry URL — exact format from recording
        # /home/fromtag/{visitors}/{timestamp_ms}/MV-Biglietti/1
        from zoneinfo import ZoneInfo
        rome = ZoneInfo('Europe/Rome')
        day, month, year = slot_info['date'].split('/')
        dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
        ts = int(dt.timestamp() * 1000)
        entry_url = f"{VATICAN_BASE}/home/fromtag/{slot_info['visitors']}/{ts}/MV-Biglietti/1"
        
        stop_watchdog = False
        async def turnstile_watchdog():
            while not stop_watchdog:
                try:
                    token = await page.evaluate("""
                        () => {
                            const inp = document.querySelector('input[name="cf-turnstile-response"]');
                            return inp ? inp.value : '';
                        }
                    """)
                    if token and len(token) > 100:
                        print(f"   [TURNSTILE] token present")
                except Exception:
                    pass
                await asyncio.sleep(5)

        watchdog_task = asyncio.create_task(turnstile_watchdog())

        # STEP 1: Navigate
        print(f" [1] Navigating to: {entry_url}")
        await page.goto(entry_url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(4000)

        # STEP 2: Resolve ticket_id via Search API (IDs change daily)
        print(" [2] Resolving ticket_id via Search API...")
        api_headers = {'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest'}
        r = await page.request.get(f'{VATICAN_BASE}/api/search/resultPerTag',
            params={'lang': 'it', 'visitorNum': str(slot_info['visitors']),
                    'visitDate': slot_info['date'], 'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'},
            headers=api_headers)
        if r.status != 200:
            print(f"  Search API failed: {r.status}")
            return
        visits = (await r.json()).get('visits', [])
        ticket = next((v for v in visits
                       if 'musei vaticani' in v.get('name', '').lower()
                       and 'ingresso' in v.get('name', '').lower()), None)
        if not ticket:
            print(f"  No entry ticket found for {slot_info['date']}")
            return
        tid = str(ticket['id'])
        print(f"   ticket_id: {tid}")

        # STEP 3: Click bookTicket
        print(f" [3] Clicking bookTicket_{tid}...")
        try:
            await page.wait_for_selector(f"[data-cy='bookTicket_{tid}']", timeout=10000)
            await page.click(f"[data-cy='bookTicket_{tid}']")
            await page.wait_for_timeout(2000)
            print("   bookTicket clicked")
        except Exception as e:
            print(f"  bookTicket failed: {e}")

        # STEP 4: Set quantity
        # Recording: open ticketQuantity dropdown then click ticketQuantitySection matching visitor count
        print(f" [4] Setting quantity to {VISITORS}...")
        try:
            await page.wait_for_selector("[data-cy='ticketQuantity']", timeout=8000)
            await page.click("[data-cy='ticketQuantity']")
            await page.wait_for_timeout(600)
            clicked = await page.evaluate(f"""
                () => {{
                    const items = Array.from(document.querySelectorAll("[data-cy='ticketQuantitySection']"));
                    for (const item of items) {{
                        const txt = item.innerText.trim();
                        if (txt === '{VISITORS}' || txt.startsWith('{VISITORS}')) {{
                            item.click();
                            return txt;
                        }}
                    }}
                    const first = document.querySelector("[data-cy='ticketQuantitySection']");
                    if (first) {{ first.click(); return first.innerText.trim(); }}
                    return null;
                }}
            """)
            print(f"   Quantity selected: {clicked}")
            await page.wait_for_timeout(600)
        except Exception as e:
            print(f"  Quantity failed: {e}")

     # Build Entry URL — exact format from recording
        # /home/fromtag/{visitors}/{timestamp_ms}/MV-Biglietti/1
        from zoneinfo import ZoneInfo
        rome = ZoneInfo('Europe/Rome')
        day, month, year = slot_info['date'].split('/')
        dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
        ts = int(dt.timestamp() * 1000)
        entry_url = f"{VATICAN_BASE}/home/fromtag/{slot_info['visitors']}/{ts}/MV-Biglietti/1"
        
        stop_watchdog = False
        async def turnstile_watchdog():
            while not stop_watchdog:
                try:
                    token = await page.evaluate("""
                        () => {
                            const inp = document.querySelector('input[name="cf-turnstile-response"]');
                            return inp ? inp.value : '';
                        }
                    """)
                    if token and len(token) > 100:
                        print(f"   [TURNSTILE] token present")
                except Exception:
                    pass
                await asyncio.sleep(5)

        watchdog_task = asyncio.create_task(turnstile_watchdog())

        # STEP 1: Navigate
        print(f" [1] Navigating to: {entry_url}")
        await page.goto(entry_url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(4000)

        # STEP 2: Resolve ticket_id via Search API (IDs change daily)
        print(" [2] Resolving ticket_id via Search API...")
        api_headers = {'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest'}
        r = await page.request.get(f'{VATICAN_BASE}/api/search/resultPerTag',
            params={'lang': 'it', 'visitorNum': str(slot_info['visitors']),
                    'visitDate': slot_info['date'], 'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'},
            headers=api_headers)
        if r.status != 200:
            print(f"  Search API failed: {r.status}")
            return
        visits = (await r.json()).get('visits', [])
        ticket = next((v for v in visits
                       if 'musei vaticani' in v.get('name', '').lower()
                       and 'ingresso' in v.get('name', '').lower()), None)
        if not ticket:
            print(f"  No entry ticket found for {slot_info['date']}")
            return
        tid = str(ticket['id'])
        print(f"   ticket_id: {tid}")

        # STEP 3: Click bookTicket
        print(f" [3] Clicking bookTicket_{tid}...")
        try:
            await page.wait_for_selector(f"[data-cy='bookTicket_{tid}']", timeout=10000)
            await page.click(f"[data-cy='bookTicket_{tid}']")
            await page.wait_for_timeout(2000)
            print("   bookTicket clicked")
        except Exception as e:
            print(f"  bookTicket failed: {e}")

        # STEP 4: Set quantity
        print(f" [4] Setting quantity to {VISITORS}...")
        try:
            await page.wait_for_selector("[data-cy='ticketQuantity']", timeout=8000)
            await page.click("[data-cy='ticketQuantity']")
            await page.wait_for_timeout(600)
            clicked = await page.evaluate(f"""
                () => {{
                    const items = Array.from(document.querySelectorAll("[data-cy='ticketQuantitySection']"));
                    for (const item of items) {{
                        const txt = item.innerText.trim();
                        if (txt === '{VISITORS}' || txt.startsWith('{VISITORS}')) {{
                            item.click();
                            return txt;
                        }}
                    }}
                    const first = document.querySelector("[data-cy='ticketQuantitySection']");
                    if (first) {{ first.click(); return first.innerText.trim(); }}
                    return null;
                }}
            """)
            print(f"   Quantity selected: {clicked}")
            await page.wait_for_timeout(600)
        except Exception as e:
            print(f"  Quantity failed: {e}")
        slot_time = slot_info['slot_time']
        print(f" [5] Selecting time {slot_time}...")
        try:
            await page.wait_for_timeout(1500)

            async def try_click_time():
                return await page.evaluate(f"""
                    () => {{
                        const cells = Array.from(document.querySelectorAll("[data-cy='time']"));
                        for (const cell of cells) {{
                            const num = cell.querySelector('div.muvaCalendarNumber');
                            const txt = num ? num.innerText.trim() : cell.innerText.trim();
                            if (txt === '{slot_time}') {{
                                cell.scrollIntoView();
                                cell.click();
                                return txt;
                            }}
                        }}
                        return null;
                    }}
                """)

            clicked_time = await try_click_time()
            if not clicked_time:
                print(f"   Not in morning tab, switching to afternoon...")
                await page.evaluate("""() => {
                    const tabs = document.querySelectorAll('div.showGTMobile > div > div');
                    if (tabs.length >= 2) tabs[1].click();
                }""")
                await page.wait_for_timeout(800)
                clicked_time = await try_click_time()

            print(f"   Time clicked: {clicked_time}")
            await page.wait_for_timeout(1500)
        except Exception as e:
            print(f"  Time selection failed: {e}")

        # STEP 6: Click PROCEED
        print(" [6] Clicking PROCEED...")
        try:
            await page.wait_for_selector("[data-cy='bookVisit']", timeout=15000)
            await page.click("[data-cy='bookVisit']")
            await page.wait_for_timeout(5000)
            print("   PROCEED clicked")
        except Exception as e:
            print(f"  PROCEED failed: {e} — trying fallback...")
            try:
                await page.evaluate("""
                    () => {
                        const btn = document.querySelector("[data-cy='bookVisit']") ||
                                    Array.from(document.querySelectorAll('button')).find(b => /proceed|procedi/i.test(b.innerText));
                        if (btn) btn.click();
                    }
                """)
                await page.wait_for_timeout(5000)
            except Exception as e2:
                print(f"  PROCEED fallback also failed: {e2}")

        # STEP 7: Fill checkout form
        print(" [7] Filling checkout form...")
        try:
            await page.wait_for_selector("[data-cy='managerSurname']", timeout=15000)
            print("   Checkout form loaded")

            async def fill(sel, val):
                try:
                    el = await page.wait_for_selector(sel, timeout=4000)
                    if el:
                        await el.click()
                        await el.fill(str(val))
                except Exception as fe:
                    print(f"   fill({sel}) skipped: {fe}")

            await fill("[data-cy='managerSurname']", profile_data['last_name'])
            await fill("[data-cy='managerName']", profile_data['first_name'])
            await fill("[data-cy='managerCity']", profile_data['city'])
            await fill("[data-cy='managerEmail']", profile_data['email'])
            await fill("[data-cy='managerConfirmEmail']", profile_data['email'])
            await fill("[data-cy='managerPhone']", profile_data['phone'])

            # Sex dropdown
            try:
                await page.click("[data-cy='managerSex']")
                await page.wait_for_timeout(400)
                await page.click("[data-cy='managerSexSection']")
                await page.wait_for_timeout(400)
            except Exception:
                pass

            # Country dropdown — pick Italy
            try:
                await page.click("[data-cy='managerCountry']")
                await page.wait_for_timeout(400)
                picked = await page.evaluate("""
                    () => {
                        const items = Array.from(document.querySelectorAll("[data-cy='managerCountrySection']"));
                        const italy = items.find(el => /ital/i.test(el.innerText));
                        if (italy) { italy.click(); return italy.innerText.trim(); }
                        if (items[0]) { items[0].click(); return items[0].innerText.trim(); }
                        return null;
                    }
                """)
                print(f"   Country: {picked}")
                await page.wait_for_timeout(400)
            except Exception:
                pass

            # Birth date — open datepicker, pick year 1990, navigate to June, pick day 15
            try:
                await page.click("mat-sidenav-container span.mat-focus-indicator")
                await page.wait_for_timeout(600)
                year_el = await page.query_selector("text/1990")
                if year_el:
                    await year_el.click()
                    await page.wait_for_timeout(400)
                for _ in range(4):
                    try:
                        await page.click("button.mat-calendar-next-button")
                        await page.wait_for_timeout(200)
                    except Exception:
                        pass
                try:
                    await page.click("text/JUN")
                    await page.wait_for_timeout(400)
                except Exception:
                    pass
                await page.evaluate("""
                    () => {
                        const cells = Array.from(document.querySelectorAll('span.mat-calendar-body-cell-content'));
                        const d = cells.find(el => el.innerText.trim() === '15');
                        if (d) d.click();
                    }
                """)
                await page.wait_for_timeout(400)
            except Exception as e:
                print(f"   Birthdate skipped: {e}")

            # Language dropdown
            try:
                await page.click("[data-cy='managerLanguage']")
                await page.wait_for_timeout(400)
                await page.click("[data-cy='managerLanguageSection']")
                await page.wait_for_timeout(400)
            except Exception:
                pass

            # Participant names — one per visitor (recording shows participantSurname_0, participantName_0, etc.)
            print(f"   Filling {VISITORS} participant(s)...")
            for i in range(VISITORS):
                try:
                    acc = await page.query_selector(f"#participantElement_{i} div.tw-flex-grow > div")
                    if acc:
                        await acc.click()
                        await page.wait_for_timeout(500)
                    await fill(f"#participantSurname_{i}", profile_data['last_name'])
                    await fill(f"#participantName_{i}", profile_data['first_name'])
                    print(f"   Participant {i+1} filled")
                except Exception as pe:
                    print(f"   Participant {i} failed: {pe}")

            # Checkboxes
            print("   Checking mandatory boxes...")
            try:
                cb1 = await page.query_selector("#mat-mdc-checkbox-1-input")
                if cb1 and not await cb1.is_checked():
                    await cb1.click()
                    await page.wait_for_timeout(800)
                    close = await page.query_selector("[data-cy='purchase-rules-close-btn'] mat-icon")
                    if not close:
                        close = await page.query_selector("div.cdk-overlay-container mat-icon")
                    if close:
                        await close.click()
                        await page.wait_for_timeout(400)
                cb4 = await page.query_selector("#mat-mdc-checkbox-4-input")
                if cb4 and not await cb4.is_checked():
                    await cb4.click()
                    await page.wait_for_timeout(300)
            except Exception as e:
                print(f"   Checkbox warning: {e}")

            print(f"\n{'='*50}")
            print(" HOLD STABILIZED!")
            print(f" Slot: {slot_info['date']} {slot_info['slot_time']} x{VISITORS}")
            print(f" Heartbeat every {HEARTBEAT_INTERVAL_MS//1000}s (4 min)")
            print(f"{'='*50}\n")

            # Inject heartbeat + box maintainer
            await page.evaluate("""
                (args) => {
                    const { slot_id, ticket_id, visitors, adult_count, child_count, heartbeat_ms } = args;
                    window._vatican_heartbeat = setInterval(() => {
                        console.log('Sending heartbeat recap...');
                        fetch('/api/visit/recap', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            credentials: 'include',
                            body: JSON.stringify({
                                visitId: slot_id,
                                visitTypeId: parseInt(ticket_id),
                                visitorNum: parseInt(visitors),
                                lang: 'it',
                                tickets: [
                                    { id: 60, name: 'Biglietto Intero', price: 20, quantity: adult_count.toString() },
                                    { id: 61, name: 'Biglietto Ridotto', price: 10, quantity: child_count.toString() }
                                ],
                                additionalCosts: {
                                    'service-0': { id: 58, name: 'Diritti di Prevendita', price: 5, quantity: parseInt(visitors) }
                                },
                                services: [
                                    { id: 58, name: 'Diritti di Prevendita', price: 5, quantity: parseInt(visitors) }
                                ]
                            })
                        }).then(r => {
                            const t = new Date().toLocaleTimeString();
                            if (r.status === 200) {
                                console.log('Heartbeat OK at', t);
                            } else {
                                console.log('Heartbeat status:', r.status, 'at', t);
                            }
                        }).catch(e => console.log('Heartbeat error:', e));
                    }, heartbeat_ms);

                    window._box_maintainer = setInterval(() => {
                        const cb1 = document.querySelector("#mat-mdc-checkbox-1-input");
                        const cb4 = document.querySelector("#mat-mdc-checkbox-4-input");
                        if (cb1 && !cb1.checked) {
                            cb1.click();
                            setTimeout(() => {
                                const close = document.querySelector("[data-cy='purchase-rules-close-btn'] mat-icon");
                                if (close) close.click();
                            }, 1000);
                        }
                        if (cb4 && !cb4.checked) cb4.click();
                    }, 30000);
                }
            """, {
                'slot_id': str(slot_info['slot_id']),
                'ticket_id': str(tid),
                'visitors': str(VISITORS),
                'adult_count': str(ADULTS),
                'child_count': str(CHILDREN),
                'heartbeat_ms': HEARTBEAT_INTERVAL_MS
            })

            print("SESSION LOCKED — DO NOT CLOSE THE BROWSER")
            while True:
                elapsed = (time.time() - start_time) / 60
                sys.stdout.write(f"\r  HOLD ACTIVE: {elapsed:.1f} min elapsed... ")
                sys.stdout.flush()
                await asyncio.sleep(10)
                if elapsed >= 70:
                    print(f"\n\n70 MINUTES — solve captcha and click BUY now!")
                    break

        except Exception as e:
            print(f" Checkout failed: {e}")
            print(" Waiting — finish manually in the browser if needed.")
            while True:
                await asyncio.sleep(60)
        finally:
            stop_watchdog = True
            try:
                watchdog_task.cancel()
            except Exception:
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="Open browser for manual login")
    args = parser.parse_args()

    if args.setup:
        asyncio.run(run_hold_challenge(None))
    else:
        start_time = time.time()
        slot = asyncio.run(find_available_slot())
        if slot:
            asyncio.run(run_hold_challenge(slot))
        else:
            print("No slots found to test.")
