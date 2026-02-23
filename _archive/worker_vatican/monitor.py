import json
import time
import random
import logging
import socket
from datetime import datetime
from curl_cffi import requests
from collections import OrderedDict

# Safe Cache Import
try:
    from django.core.cache import cache
except ImportError:
    cache = None

# [NEW] Playwright imports for High Accuracy
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Module-level DNS Cache
DNS_CACHE = {}

class VaticanPro:
    def __init__(self, visitors=1, lang='it', proxy=None):
        self.visitors = visitors
        self.lang = lang
        self.proxy = proxy
        self.proxies_list = self._load_all_proxies()
        
        # Initialize curl_cffi session for API checks (Standards)
        stealth_configs = [
            {
                "impersonate": "chrome124",
                "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "platform": '"Windows"',
                "brands": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"'
            }
        ]
        
        cfg = stealth_configs[0]
        self.impersonate = cfg["impersonate"]
        self.session = requests.Session(impersonate=self.impersonate)
        
        if self.proxy:
            self.session.proxies = {"http": self.proxy, "https": self.proxy}
            
        self.base_headers = self.get_stealth_headers(cfg)
        
        # Load harvested session immediately during initialization
        logger.info("🚀 Bot Init: Loading harvested session...")
        if self.load_cached_session():
             logger.info("✅ Harvested session loaded successfully in __init__")
        else:
             logger.warning("⚠️ No harvested session found in Redis during __init__")
        
    def _load_all_proxies(self):
        """Load proxies from 'Proxy lists.json' and 'Webshare 10 proxies.txt'"""
        proxies = []
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. Load from Proxy lists.json (Oxylabs)
        json_path = os.path.join(base_dir, "Proxy lists.json")
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    # Convert to http format. Need credentials from environment if possible, 
                    # otherwise assuming they might be whitelisted or part of entryPoint logic
                    for p in data:
                        proxies.append({
                            "server": f"http://{p['entryPoint']}:{p['port']}",
                            "ip": p['ip'],
                            "country": p.get('countryCode', 'IT')
                        })
                    logger.info(f"✅ Loaded {len(data)} Proxies from JSON")
        except Exception as e:
            logger.warning(f"Error loading Proxy lists.json: {e}")

        # 2. Load from Webshare 10 proxies.txt
        txt_path = os.path.join(base_dir, "Webshare 10 proxies.txt")
        try:
            if os.path.exists(txt_path):
                with open(txt_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and ":" in line and not line.startswith("page."):
                            parts = line.split(':')
                            if len(parts) == 4:
                                proxies.append({
                                    "server": f"http://{parts[0]}:{parts[1]}",
                                    "username": parts[2],
                                    "password": parts[3]
                                })
                    logger.info(f"✅ Loaded proxies from Webshare TXT")
        except Exception as e:
            logger.warning(f"Error loading Webshare proxies: {e}")
            
        return proxies

    def get_rotation_proxy_config(self):
        """Get a random proxy configuration for Playwright"""
        if self.proxies_list:
            p = random.choice(self.proxies_list)
            config = {"server": p["server"]}
            if "username" in p:
                config["username"] = p["username"]
                config["password"] = p["password"]
            return config
        
        if self.proxy:
            # Parse self.proxy if it's in string format
            return {"server": self.proxy}
        return None

    def load_cached_session(self):
        """God Tier: Load pre-warmed cookies from Redis (set by Harvester)"""
        try:
            # Try loading from Redis key 'vatican_cookies' (JSON format from harvester)
            import redis
            import json
            # Try 'redis' first (Docker network), then 'localhost' (Hetzner host/manual run)
            for host in ['redis', 'localhost', '127.0.0.1']:
                try:
                    redis_client = redis.Redis(host=host, port=6379, decode_responses=True, socket_connect_timeout=2)
                    cached_data = redis_client.get('vatican_cookies')
                    if cached_data:
                        data = json.loads(cached_data)
                        
                        # Handle both old (direct dict) and new (wrapped) formats
                        if "cookies" in data and "user_agent" in data:
                            cookies = data["cookies"]
                            ua = data["user_agent"]
                        else:
                            cookies = data
                            ua = None
                            
                        logger.info(f"🚀 GOD TIER: Loaded Harvested Session from {host}")
                        for name, value in cookies.items():
                            self.session.cookies.set(name, value, domain='tickets.museivaticani.va')
                        
                        if ua:
                            self.session.headers["user-agent"] = ua
                            logger.info(f"   Aligned User-Agent: {ua[:50]}...")
                            
                        return True
                except:
                    continue
            
            logger.warning("⚠️ No harvested cookies found in Redis after trying all hosts.")
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
        return False


    def get_stealth_headers(self, cfg):
        # Solution 2: Let curl_cffi handle Chrome fingerprinting automatically
        # Only set headers that are BUSINESS LOGIC (not browser fingerprint)
        headers = OrderedDict()
        headers["authority"] = "tickets.museivaticani.va"
        headers["referer"] = "https://tickets.museivaticani.va/home"
        # Do NOT set User-Agent, sec-ch-ua, etc. - curl_cffi handles them
        return headers

    def format_date(self, date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except:
            return date_str

    def generate_trust_cookies(self, target_id=None):
        """Solution 1: Natural Warming Sequence - Walk the State Machine"""
        logger.info(f"🔥 Starting Natural Session Warming...")
        try:
            # State 1 -> State 2: Homepage (Generates JSESSIONID)
            self.session.get("https://tickets.museivaticani.va/", headers=self.base_headers, timeout=30)
            time.sleep(1)
            
            # State 2 -> State 3: "Visite Guidate" Tag Page (Contextualizes session)
            # This tells the server "I am looking at Guided Tours"
            tag_url = "https://tickets.museivaticani.va/home/fromtag/2/1769382000000/MV-Visite-Guidate/1"
            self.session.get(tag_url, headers=self.base_headers, timeout=30)
            time.sleep(2)  # Give the server time to sync session
            
            # State 3 (CRITICAL): The "Details" Page
            # DYNAMIC: Use target_id if provided, otherwise fallback
            tour_id = target_id if target_id else 1602099201
            details_url = f"https://tickets.museivaticani.va/home/details/{tour_id}"
            self.session.get(details_url, headers=self.base_headers, timeout=30)
            
            logger.info(f"✅ Session Warmed for ID {tour_id}. Cookies: {self.session.cookies.get_dict()}")
        except Exception as e:
            logger.error(f"Pre-warming failed: {e}")

    def get_ticket_type_id(self, date_str, tag="MV-Biglietti"):
        """Step 1: Find the Product ID (e.g., Guided Tour ID)"""
        formatted_date = self.format_date(date_str)
        url = "https://tickets.museivaticani.va/api/search/resultPerTag"
        params = {
            "lang": self.lang,
            "visitorNum": self.visitors,
            "visitDate": formatted_date,
            "area": 1,
            "page": 0,
            "tag": tag
        }
        
        try:
            resp = self.session.get(url, params=params, headers=self.base_headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                visits = data.get('visits', [])
                for visit in visits:
                    # Return the ID if it's not strictly sold out
                    if visit.get('availability') != 'SOLD_OUT':
                        return visit.get('id')
        except Exception as e:
            logger.error(f"Error getting ticket type: {e}")
        return None

    def resolve_language_id(self, date_str, visit_type_id, target_lang_code):
        """
        Step 2 (CRITICAL): Dynamic Language Resolver.
        Asks the API: "For tour ID X on Date Y, what is the ID for French?"
        """
        # SKIP RESOLUTION for known codes if they work directly (User Verification: FRA works)
        if target_lang_code in ['FRA', 'SPA', 'ENG', 'DEU']:
             return target_lang_code

        formatted_date = self.format_date(date_str)
        
        # ... (rest of logic kept as fallback) ...
        # For Vatican, language availability is often checked via this specific logic:
        url = f"https://tickets.museivaticani.va/api/visit/detail/{visit_type_id}"
        params = {
            "lang": self.lang,
            "visitDate": formatted_date,
            "visitorNum": self.visitors
        }
        
        try:
            resp = self.session.get(url, params=params, headers=self.base_headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                available_languages = data.get('languages', [])
                
                # Look for our target (e.g., 'FR' or 'fr')
                for lang in available_languages:
                    # Check code ('FR') or isoCode ('fr-FR')
                    if (lang.get('code', '').upper() == target_lang_code.upper() or 
                        lang.get('isoCode', '').upper() == target_lang_code.upper()):
                        
                        logger.info(f"✅ Resolved Language '{target_lang_code}' -> ID: {lang['id']}")
                        return lang['id']
            # If 404, typical for some hidden tours, just return the code itself as fallback
            elif resp.status_code == 404:
                return target_lang_code
                        
        except Exception as e:
            logger.error(f"Language resolution failed: {e}")
            
        return target_lang_code # Default to returning it as-is if resolution fails

    def check_availability(self, date_str, visit_type_id, visit_language_code=None, tag=None):
        """Step 3: Check Time Slots using the Resolved IDs"""
        formatted_date = self.format_date(date_str)
        url = "https://tickets.museivaticani.va/api/visit/timeavail"
        
        # Match User's EXACT Working Headers
        headers = self.base_headers.copy()
        
        # [FIX] DYNAMIC REFERER: Match the tour category correctly
        # User recording showed /VG-Musei/1 for guided tours
        tag_path = tag if tag else "MV-Biglietti"
        headers["referer"] = f"https://tickets.museivaticani.va/home/fromtag/2/1769382000000/{tag_path}/1"
        
        # Ensure UA is set to Chrome 124 if not already loaded from session
        if "user-agent" not in headers:
            headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        
        headers["accept"] = "application/json, text/plain, */*"
        headers["accept-language"] = "en-US,en;q=0.9,it;q=0.8"  # User's exact value
        
        # User's exact params (lang=it, NOT fr!)
        params = {
            "lang": "it",  # Interface language - always 'it' per user's working request
            "visitorNum": self.visitors,
            "visitDate": formatted_date,
            "visitTypeId": visit_type_id
        }

        # If it's a Guided Tour, we MUST add the language param
        if visit_language_code:
            lang_val = self.resolve_language_id(date_str, visit_type_id, visit_language_code)
            params["visitLang"] = lang_val
            # Update referer for Guided Tours specifically if we have a resolved ID
            headers["referer"] = f"https://tickets.museivaticani.va/home/fromtag/2/1769382000000/VG-Musei/1"

        try:
            resp = self.session.get(url, params=params, headers=headers, timeout=20)


            if resp.status_code == 200:
                data = resp.json()
                timetable = data.get('timetable', [])
                results = []
                for slot in timetable:
                    if slot.get('availability') != 'SOLD_OUT':
                        results.append({
                            "time": slot.get('time'),
                            "availability": slot.get('availability'),
                            "category": slot.get('category'),
                            "lang_code": visit_language_code
                        })
                return results
            else:
                logger.warning(f"Check failed with status {resp.status_code}")
                # To make it visible in manual test without DEBUG level
                if "Internal Server Error" in resp.text or "Generic Error" in resp.text:
                     logger.warning(f"❌ API SAYS: {resp.text}")
        except Exception as e:
            logger.error(f"Availability check failed: {e}")
            print(f"💥 Availability Check Exception: {e}")
            
        return []

    def check_availability_ninja(self, date_str, visit_type_id, visit_language_code=None, tag=None):
        """
        PURE UI BOT: Direct Playwright interaction following user's exact flow.
        1. Navigate to URL with date timestamp
        2. Click #ticket_dx_1 PRENOTA
        3. Select Language via UI
        4. Click calendar day
        5. Scrape available slots
        """
        proxy_config = self.get_rotation_proxy_config()
        logger.info(f"🥷 PURE UI BOT using Proxy: {proxy_config.get('server') if proxy_config else 'DIRECT'}")
        
        results = []
        try:
            with sync_playwright() as p:
                # 1. Stealth Browser Launch
                browser_args = [
                    "--no-sandbox", 
                    "--disable-setuid-sandbox", 
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars"
                ]
                
                browser = p.chromium.launch(headless=True, args=browser_args, proxy=proxy_config)
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080},
                    locale="it-IT",
                    timezone_id="Europe/Rome"
                )
                
                # Remove navigator.webdriver
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                page = context.new_page()
                stealth_sync(page)

                # 1b. Block Heavy Resources (Images, Fonts, CSS) - Save RAM & Bandwidth
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "stylesheet", "media"] else route.continue_())
                
                # 2. Convert date to timestamp for URL
                # User URL format: /fromtag/3/1769468400000/MV-Biglietti/1
                # 1769468400000 is milliseconds since epoch for Jan 27 2026
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                timestamp_ms = int(dt.timestamp() * 1000)
                
                tag_path = tag if tag else "MV-Biglietti"
                url = f"https://tickets.museivaticani.va/home/fromtag/3/{timestamp_ms}/{tag_path}/1"
                logger.info(f"   🥷 Navigating to {url}")
                
                # Navigate with network idle for full load
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(2)
                
                # 3. Click #ticket_dx_1 PRENOTA button
                logger.info("   🥷 Clicking #ticket_dx_1 PRENOTA...")
                try:
                    prenota_btn = page.locator('#ticket_dx_1').get_by_role('button', name='PRENOTA')
                    prenota_btn.wait_for(state="visible", timeout=10000)
                    prenota_btn.click()
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"   Could not click #ticket_dx_1: {e}")
                    # Fallback: try any PRENOTA button
                    page.locator("button:has-text('PRENOTA')").first.click()
                    time.sleep(2)
                
                # 4. Select Language via UI
                if visit_language_code:
                    lang_map = {"FRA": "Francese", "ENG": "Inglese", "SPA": "Spagnolo", "DEU": "Tedesco", "ITA": "Italiano", "POR": "Portoghese"}
                    target_lang = lang_map.get(visit_language_code, "Inglese")
                    logger.info(f"   🥷 Selecting language: {target_lang}")
                    
                    lang_box = page.locator('app-ticket-visit-language')
                    if lang_box.is_visible():
                        # Click textbox to open dropdown
                        lang_box.get_by_role('textbox').click()
                        time.sleep(1)
                        
                        # Select the language option
                        lang_option = lang_box.get_by_role('article').locator('div').filter(has_text=target_lang).first
                        if lang_option.is_visible():
                            lang_option.click()
                            time.sleep(2)
                        else:
                            logger.warning(f"   Language option {target_lang} not visible!")
                    else:
                        logger.warning("   Language selector not visible!")
                
                # 5. Click calendar day to reveal slots
                logger.info("   🥷 Clicking calendar day...")
                calendar_day = page.locator('.muvaCalendarDayBorder').first
                if calendar_day.is_visible():
                    calendar_day.click()
                    time.sleep(3)  # Wait for slots to load
                else:
                    logger.warning("   Calendar day not visible, trying alternative...")
                    # Try clicking any visible date button
                    page.locator("button[class*='calendar']").first.click()
                    time.sleep(3)
                
                # 6. Scrape available slots
                logger.info("   🥷 Scanning for available slots...")
                
                # Multiple selectors for slot elements
                slot_selectors = [
                    "app-time-slots .slot-item",
                    ".time-slot-item", 
                    "app-time-slot button",
                    ".mat-chip",
                    "[class*='slot']"
                ]
                
                for selector in slot_selectors:
                    items = page.locator(selector).all()
                    if items:
                        logger.info(f"   Found {len(items)} elements with selector: {selector}")
                        for item in items:
                            text = item.inner_text().strip().replace('\n', ' ')
                            if not text:
                                continue
                            
                            # Extract time pattern HH:MM
                            import re
                            time_match = re.search(r'(\d{2}:\d{2})', text)
                            if time_match:
                                slot_time = time_match.group(1)
                                
                                # Check if sold out
                                is_sold = any(x in text.upper() for x in ["SOLD_OUT", "ESAURITO", "NON DISPONIBILE"])
                                classes = item.get_attribute("class") or ""
                                if "disabled" in classes.lower():
                                    is_sold = True
                                
                                if not is_sold:
                                    results.append({
                                        "time": slot_time,
                                        "availability": "AVAILABLE",
                                        "lang_code": visit_language_code
                                    })
                        
                        if results:
                            break  # Found slots, stop searching
                
                if not results:
                    # Check for "no availability" message
                    page_text = page.content()
                    if "NESSUNA DISPONIBILITÀ" in page_text.upper() or "NO AVAILABILITY" in page_text.upper():
                        logger.info("   Confirmed: No availability message on page")
                    else:
                        logger.info("   No slots found (may be sold out or page structure changed)")
                
                logger.info(f"   🥷 Found {len(results)} available slots")
                browser.close()
                
        except Exception as e:
            logger.error(f"   Pure UI Bot failed: {e}")
            
        return results


    def run_task(self, task_data):
        """
        Main entry point.
        """
        all_results = {}
        dates = task_data.get('dates', [])
        tag = task_data.get('tag', 'MV-Biglietti')
        target_lang = task_data.get('language', None) # e.g., "FR"
        override_id = task_data.get('override_id', None) # NEW: Allow manual ID

        for date_str in dates:
            # 1. Get the Tour ID (e.g., Guided Tour of Museums)
            if override_id:
                type_id = override_id
            else:
                type_id = self.get_ticket_type_id(date_str, tag=tag)
            
            if type_id:
                # 2. Check Availability
                # [NEW] Use Ninja Bot for Guided Tours (High Accuracy + Speed)
                is_guided = "Visite-Guidate" in tag or "VG-Musei" in tag or target_lang is not None

                # CRITICAL FIX: Re-warm session for THIS specific Tour ID if needed
                # Only needed for Standard/Requests bot. Pure UI (Ninja) builds its own context.
                if not is_guided and not self.session.cookies.get('ticketmv'):
                     self.generate_trust_cookies(target_id=type_id)

                if is_guided:
                    slots = self.check_availability_ninja(date_str, type_id, visit_language_code=target_lang, tag=tag)

                else:
                    slots = self.check_availability(date_str, type_id, visit_language_code=target_lang, tag=tag)
                
                if slots:
                    logger.info(f"🎯 FOUND {len(slots)} SLOTS for {date_str} ({tag})")
                    all_results[date_str] = slots
                else:
                    logger.info(f"❌ No slots for {date_str}")
            else:
                logger.info(f"❌ Tour Type '{tag}' sold out or not found for {date_str}")
                
            time.sleep(random.uniform(1.0, 3.0)) # Jitter
            
        return all_results

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    monitor = VaticanPro(visitors=2)
    
    # Task 1: Check Standard Tickets (No language needed)
    # print(monitor.run_task({"dates": ["2026-05-20"], "tag": "MV-Biglietti"}))
    
    # Task 2: Check Guided Tours in FRENCH (Auto-resolves ID)
    # The tag for guided tours is usually 'MV-Visite-Guidate'
    print(monitor.run_task({
        "dates": ["2026-05-20"], 
        "tag": "MV-Visite-Guidate", 
        "language": "FR" 
    }))
