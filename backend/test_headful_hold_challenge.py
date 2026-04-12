import asyncio
import os
import sys
import json
import time
from datetime import datetime, timedelta
import requests

# Set up path to include root for worker_vatican and backend
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from monitors.models import BuyerProfile, Agency
from worker_vatican.search_api_monitor import VaticanSearchAPIMonitor
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import argparse
import subprocess
import shutil
import tempfile

#  CONFIG 
VATICAN_BASE = 'https://tickets.museivaticani.va'
VISITORS = 1
ADULTS = 1
CHILDREN = 0
LOOKAHEAD_DAYS = 90
HEARTBEAT_INTERVAL_MS = 300000  # 5 minutes
TARGET_TICKET_NAME = "Musei Vaticani - Biglietti d'ingresso"
PREFERRED_TEST_DATE = "04/05/2026"
PERSISTENT_PROFILE_PATH = r"d:\bot\vatican_chrome_profile"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.178 Safari/537.36"
# 

async def find_available_slot():
    """Iterate through the next 90 days and find the first available slot."""
    monitor = VaticanSearchAPIMonitor()
    
    # Try preferred date first
    dates_to_check = [PREFERRED_TEST_DATE]
    start_date = datetime.now()
    for i in range(LOOKAHEAD_DAYS):
        d = (start_date + timedelta(days=i)).strftime('%d/%m/%Y')
        if d not in dates_to_check:
            dates_to_check.append(d)

    print(f"SEARCHING for any available slot (Preferred: {PREFERRED_TEST_DATE})...")
    
    for date_str in dates_to_check:
        try:
            day, month, year = date_str.split('/')
            current_dt = datetime(int(year), int(month), int(day))
        except Exception:
            continue
            
        # Check if Sunday (Vatican usually closed)
        if current_dt.weekday() == 6:
            continue
            
        sys.stdout.write(f"\r  Checking {date_str}... ")
        sys.stdout.flush()
        
        try:
            success, slots, tid = monitor.check_ticket(
                target_date=date_str,
                ticket_name=TARGET_TICKET_NAME,
                visitors=VISITORS
            )
            
            if success and slots:
                best_slot = slots[0]
                print(f"\nFOUND SLOT! {date_str} at {best_slot.get('time')}")
                return {
                    'date': date_str,
                    'slot_id': best_slot.get('id'),
                    'slot_time': best_slot.get('time'),
                    'ticket_id': tid,
                    'visitors': VISITORS
                }
        except Exception as e:
            print(f"\nERROR checking {date_str}: {e}")
            
        await asyncio.sleep(0.5)
        
    print("\nNo slots found in the next 90 days.")
    return None

async def run_hold_challenge(slot_info):
    """
    Launch Playwright, fill form, and start heartbeat.
    """
    # Fetch profile (sync_to_async needed for Django ORM in async context)
    from asgiref.sync import sync_to_async
    
    @sync_to_async
    def get_profile():
        # Look for the test user we created or any active agency
        agency = Agency.objects.filter(is_active=True).exclude(plan='system').first()
        if not agency: 
            return {
                'first_name': 'Test', 'last_name': 'User', 'email': 'test@example.com',
                'phone': '123456789', 'city': 'Rome', 'country': 'Italy'
            }
        p = BuyerProfile.objects.filter(agency=agency).first()
        if not p: return None
        return {
            'first_name': p.first_name, 'last_name': p.last_name, 'email': p.email,
            'phone': p.phone, 'city': p.city, 'country': p.country
        }

    if slot_info is None:
        slot_info = {'visitors': 1, 'id': 'setup', 'date': '?', 'slot_time': '?', 'slot_id': 'setup'}
    
    profile_data = await get_profile()
    
    async with async_playwright() as p:
        # Launch REAL Chrome via CDP (Anti-Cloudflare logic)
        chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
        
        # Setup Mode - If slot_info is None, we just open the browser and wait
        is_setup = slot_info is None
        if is_setup:
            print("\nSETUP MODE: Opening browser for manual sign-in/trusted session...")
        else:
            print("\nStarting Headful Hold Challenge...")
        
        from dotenv import load_dotenv
        load_dotenv(os.path.join(root_dir, '.env'))
        oxy_username = os.environ.get('OXYLABS_USERNAME')
        oxy_password = os.environ.get('OXYLABS_PASSWORD')

        @sync_to_async
        def get_proxy():
            from monitors.models import Proxy
            return Proxy.objects.filter(is_active=True).order_by('?').first()

        proxy = await get_proxy()
        proxy_args = []
        if proxy:
            print(f" Using proxy: {proxy.ip_port}")
            p_user = oxy_username if oxy_username else proxy.username
            p_pass = oxy_password if oxy_password else proxy.password
            
            if p_user and p_pass:
                # Generate a dynamic proxy-auth extension for Chrome
                proxy_plugin_dir = os.path.join(tempfile.gettempdir(), 'vatican_proxy_auth_plugin')
                os.makedirs(proxy_plugin_dir, exist_ok=True)
                
                manifest_json = """
                {
                    "version": "1.0.0",
                    "manifest_version": 2,
                    "name": "Chrome Proxy",
                    "permissions": ["proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"],
                    "background": {"scripts": ["background.js"]},
                    "minimum_chrome_version": "22.0.0"
                }
                """
                
                background_js = f"""
                var config = {{
                        mode: "fixed_servers",
                        rules: {{
                        singleProxy: {{
                            scheme: "http",
                            host: "{proxy.ip_port.split(':')[0]}",
                            port: parseInt({proxy.ip_port.split(':')[1]})
                        }},
                        bypassList: ["localhost"]
                        }}
                    }};
                chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
                function callbackFn(details) {{
                    return {{
                        authCredentials: {{
                            username: "{p_user}",
                            password: "{p_pass}"
                        }}
                    }};
                }}
                chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {{urls: ["<all_urls>"]}},
                    ['blocking']
                );
                """
                with open(os.path.join(proxy_plugin_dir, "manifest.json"), "w") as f:
                    f.write(manifest_json)
                with open(os.path.join(proxy_plugin_dir, "background.js"), "w") as f:
                    f.write(background_js)
                    
                proxy_args = [f'--load-extension={proxy_plugin_dir}']
                print(" Generated proxy auth extension to bypass Chrome popup")
            else:
                proxy_args = [f'--proxy-server=http://{proxy.ip_port}']

        print(" Launching real Chrome via CDP to bypass Cloudflare...")
        debug_port = 9222
        
        chrome_cmd = [
            chrome_path,
            f'--remote-debugging-port={debug_port}',
            f'--user-data-dir={PERSISTENT_PROFILE_PATH}',
            '--profile-directory=Default',
            '--no-first-run',
            '--no-default-browser-check',
            '--start-maximized',
            # Anti-detection & Realism flags
            '--disable-blink-features=AutomationControlled',
            '--ignore-gpu-blocklist',
            '--enable-webgl',
            '--enable-accelerated-2d-canvas',
            '--disable-features=IsolateOrigins,site-per-process',
            f'--user-agent={USER_AGENT}',
            'about:blank' if not is_setup else 'https://google.com',
        ] + proxy_args
        
        chrome_proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

        # Build Entry URL - matching recording style
        from zoneinfo import ZoneInfo
        rome = ZoneInfo('Europe/Rome')
        day, month, year = slot_info['date'].split('/')
        dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
        ts = int(dt.timestamp() * 1000)
        # Recording uses /home/visit/{visitors}/{timestamp}/1
        entry_url = f"{VATICAN_BASE}/home/visit/{slot_info['visitors']}/{ts}/1"
        
        # Turnstile auto-solve: just wait for the token to appear
        # Managed Turnstile solves itself in real Chrome — no clicking needed
        # The watchdog just monitors and reports
        stop_watchdog = False
        async def turnstile_watchdog():
            while not stop_watchdog:
                try:
                    # Check if Turnstile token is already solved
                    token = await page.evaluate("""
                        () => {
                            const inp = document.querySelector('input[name="cf-turnstile-response"]');
                            return inp ? inp.value : '';
                        }
                    """)
                    if token and len(token) > 100:
                        print(f"   [TURNSTILE] ✅ Auto-solved! Token prefix: {token[:4]}")
                except Exception:
                    pass
                await asyncio.sleep(5)

        watchdog_task = asyncio.create_task(turnstile_watchdog())

        print(f" [1] Navigating to: {entry_url}")
        await page.goto(entry_url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(3000)

        #  Step 1: Get actual ticket_id via API (Agent Logic) 
        print(" [2] Resolving ticket ID via Search API...")
        headers = { 'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest' }
        r = await page.request.get(f'{VATICAN_BASE}/api/search/resultPerTag',
            params={'lang':'it','visitorNum':str(slot_info['visitors']),'visitDate':slot_info['date'],
                    'area':'1','who':'','page':'0','tag':'MV-Biglietti'},
            headers=headers)
        
        if r.status != 200:
            print(f" Search API failed: {r.status}")
            return

        visits = (await r.json()).get('visits', [])
        ticket = next((v for v in visits if 'musei vaticani' in v.get('name','').lower() and 'ingresso' in v.get('name','').lower()), None)
        if not ticket:
            print(f" Could not find standard entry ticket for {slot_info['date']}")
            return
        
        tid = str(ticket['id'])
        print(f"   found ticket_id: {tid}")

        #  Step 2: Click bookTicket 
        print(" [3] Clicking bookTicket...")
        try:
            # First, we might need to click the ticket image to expand it
            await page.click(f"#ticket_{tid} img", timeout=5000)
            await page.wait_for_timeout(1000)
        except Exception: pass

        try:
            await page.wait_for_selector(f"[data-cy='bookTicket_{tid}']", timeout=8000)
            await page.click(f"[data-cy='bookTicket_{tid}']")
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f" bookTicket click failed: {e}")

        #  Step 3: Set quantity 
        print(f" [4] Setting quantity to {ADULTS} Adults...")
        try:
            await page.wait_for_selector("[data-cy='ticketQuantity']", timeout=10000)
            
            # From recording: open → click first div (reset) → open again → click ticketQuantitySection span
            qty = await page.query_selector("[data-cy='ticketQuantity']")
            if qty: await qty.click(); await page.wait_for_timeout(500)
            
            # Click first div in section (resets)
            await page.evaluate("""
                () => {
                    const sec = document.querySelector("div.ng-touched section > div:nth-of-type(1)");
                    if (sec) sec.click();
                }
            """)
            await page.wait_for_timeout(300)
            
            # Open again
            qty2 = await page.query_selector("[data-cy='ticketQuantity']")
            if qty2: await qty2.click(); await page.wait_for_timeout(500)
            
            # Click the ticketQuantitySection span (= target quantity)
            clicked = await page.evaluate("""
                () => {
                    const span = document.querySelector("[data-cy='ticketQuantitySection'] > span");
                    if (span) { span.click(); return span.innerText.trim(); }
                    const sec = document.querySelector("[data-cy='ticketQuantitySection']");
                    if (sec) { sec.click(); return sec.innerText.trim(); }
                    return null;
                }
            """)
            print(f"   Quantity selected: {clicked}")
            await page.wait_for_timeout(400)
        except Exception as e:
            print(f" Quantity selection failed: {e}")

        #  Step 4: Select time slot 
        slot_time = slot_info['slot_time']
        print(f" [5] Selecting time: {slot_time}...")
        try:
            target_mins = int(slot_time.split(':')[0]) * 60 + int(slot_time.split(':')[1])
            if target_mins >= 14 * 60:
                await page.evaluate("""() => {
                    const tabs = Array.from(document.querySelectorAll('.tab')).filter(el => el.offsetParent !== null);
                    if (tabs.length >= 2) tabs[1].click();
                }""")
                await page.wait_for_timeout(1000)

            await page.evaluate(f"""() => {{
                const els = Array.from(document.querySelectorAll("[data-cy='time'] div.muvaCalendarNumber")).filter(el => el.innerText.trim() === '{slot_time}');
                if (els.length > 0) {{ els[0].scrollIntoView(); els[0].click(); }}
            }}""")
            await page.wait_for_timeout(1500)
        except Exception as e:
            print(f" Time selection failed: {e}")

        #  Step 5: Click PROCEDI 
        print(" [6] Clicking PROCEDI...")
        try:
            for sel in ["[data-cy='bookVisit']", "button:has-text('PROCEDI')"]:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(4000)
                    break
        except Exception as e:
            print(f" Procedi failed: {e}")

        #  Step 6: Fill Checkout Form 
        print(" [7] Filling checkout form...")
        try:
            await page.wait_for_selector("[data-cy='managerSurname']", timeout=15000)
            
            async def fill(sel, val):
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el: await el.fill(str(val))
                except Exception: pass

            await fill("[data-cy='managerSurname']", profile_data['last_name'])
            await fill("[data-cy='managerName']", profile_data['first_name'])
            await fill("[data-cy='managerCity']", profile_data['city'])
            await fill("[data-cy='managerEmail']", profile_data['email'])
            await fill("[data-cy='managerConfirmEmail']", profile_data['email'])
            await fill("[data-cy='managerPhone']", profile_data['phone'])
            
            #  Initial Box Check 
            print(" Checking mandatory boxes...")
            try:
                # Rule 1: Norme Generali (Checkbox 1)
                cb1 = await page.query_selector("#mat-mdc-checkbox-1-input")
                if cb1 and not await cb1.is_checked():
                    await cb1.click(); await page.wait_for_timeout(800)
                    # Close the popup if it appeared
                    close = await page.query_selector("[data-cy='purchase-rules-close-btn'] mat-icon, div.cdk-overlay-container mat-icon")
                    if close: await close.click(); await page.wait_for_timeout(400)
                
                # Rule 4: Marketing (Checkbox 4)
                cb4 = await page.query_selector("#mat-mdc-checkbox-4-input")
                if cb4 and not await cb4.is_checked():
                    await cb4.click(); await page.wait_for_timeout(300)
            except Exception as e:
                print(f" Box check warning: {e}")

            print(f"\n{'='*50}")
            print(" HOLD STABILIZED!")
            print(f"Slot: {slot_info['date']} {slot_info['slot_time']}")
            print(f" Starting Background Heartbeat (every 4 mins)")
            print(f" Checkboxes will be auto-maintained every 30s")
            print(f" Please wait for 70 minutes.")
            print(f"{'='*50}\n")
            
            # Inject Heartbeat  EXACT copy of local_browser_agent.py (proven working)
            adult_count = str(slot_info['visitors'])
            child_count = "0"
            await page.evaluate("""
                (args) => {
                    const { slot_id, ticket_id, visitors, adult_count, child_count } = args;
                    window._vatican_heartbeat = setInterval(() => {
                        console.log(' Sending heartbeat recap...');
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
                                console.log('✅ Heartbeat OK at', t);
                            } else {
                                console.log('⚠️ Heartbeat ALERT:', r.status, 'at', t);
                            }
                        }).catch(e => console.log('❌ Heartbeat error:', e));
                    }, 240000); // 4 minutes

                    // Ensure boxes stay checked every 30s
                    window._box_maintainer = setInterval(() => {
                        const cb1 = document.querySelector("#mat-mdc-checkbox-1-input");
                        const cb4 = document.querySelector("#mat-mdc-checkbox-4-input");
                        if (cb1 && !cb1.checked) {
                            console.log(' Re-checking Rule 1...');
                            cb1.click();
                            setTimeout(() => {
                                const close = document.querySelector("[data-cy='purchase-rules-close-btn'] mat-icon");
                                if (close) { close.click(); console.log(' Closed popup'); }
                            }, 1000);
                        }
                        if (cb4 && !cb4.checked) {
                            console.log(' Re-checking Rule 4...');
                            cb4.click();
                        }
                    }, 30000);
                }
            """, {
                'slot_id': str(slot_info['slot_id']),
                'ticket_id': str(tid),
                'visitors': str(slot_info['visitors']),
                'adult_count': adult_count,
                'child_count': child_count
            })
            
            # Keep hold alive and show clear progress
            print("\n" + "🚀" * 20)
            print(" SESSION LOCKED! DO NOT CLOSE THE BROWSER.")
            print("🚀" * 20 + "\n")
            
            while True:
                elapsed = (time.time() - start_time) / 60
                sys.stdout.write(f"\r  🕒 HOLD ACTIVE: {elapsed:.1f}/70 mins passed... ")
                sys.stdout.flush()
                await asyncio.sleep(10)
                if elapsed >= 70:
                     print(f"\n\n🔥 70 MINUTES REACHED! 🔥")
                     print("You can now solve the captcha on the screen and click BUY.")
        
        except Exception as e:
            print(f"Script failed to reach/fill checkout: {e}")
            print("You might need to finish selection manually, but the script will wait.")
            while True: await asyncio.sleep(60)
        finally:
            # Clean shutdown
            print("\nShutting down watchdog and browser...")
            try: 
                stop_watchdog = True
                if 'watchdog_task' in locals(): watchdog_task.cancel()
            except: pass
            try: subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], capture_output=True)
            except: pass

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
