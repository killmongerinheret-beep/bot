import json
import time
import random
import logging
import socket
import re
from datetime import datetime
from curl_cffi import requests
from collections import OrderedDict

# Safe Cache Import
try:
    from django.core.cache import cache
except ImportError:
    cache = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Module-level DNS Cache
DNS_CACHE = {}

class ColosseumPro:
    def __init__(self, lang='en', proxy=None):
        self.lang = lang
        self.proxy = proxy
        
        # --- ULTIMATE STEALTH: UA & TLS MATCHING ---
        stealth_configs = [
            {
                "impersonate": "chrome124",
                "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "platform": '"Windows"',
                "brands": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"'
            }
        ]
        
        cfg = random.choice(stealth_configs)
        self.impersonate = cfg["impersonate"]
        self.session = requests.Session(impersonate=self.impersonate)
        
        if self.proxy:
            self.session.proxies = {"http": self.proxy, "https": self.proxy}
            
        self.base_headers = self.get_stealth_headers(cfg)
        self.event_guid = None
        
        # GOD TIER UPDATE: Load Cached Session
        self.load_cached_session()

    def load_cached_session(self):
        """God Tier: Load pre-warmed cookies from Redis (Solver)"""
        if not cache:
            return False
            
        try:
            # 1. Try Solver Cookies (Raw JSON from Nodriver)
            # We access the raw client to get the string, or use cache.get if the backend matches
            # Django-Redis stores keys with a prefix usually. 
            # Let's try ignoring prefix or using the raw connection if possible.
            # Simpler: use the cache.get with default which might fail if key format differs.
            # Best: Direct Redis check for robustness.
            # But we can just use cache.get('colosseum_cookies_raw') if we assume same DB.
            
            raw_data = cache.get('colosseum_cookies_raw')
            if raw_data:
                cookies = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                self.session.cookies.update(cookies)
                logger.info("🚀 GOD TIER: Loaded Nodriver Cookies (Queue Solver)!")
                return True
                
            # 2. Fallback to old Django Cache
            cached_cookies = cache.get('colosseum_cookies')
            if cached_cookies:
                self.session.cookies.update(cached_cookies)
                return True
                
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
        return False

    def get_stealth_headers(self, cfg):
        headers = OrderedDict()
        headers["Host"] = "ticketing.colosseo.it"
        headers["Connection"] = "keep-alive"
        
        if cfg["brands"]:
            headers["sec-ch-ua"] = cfg["brands"]
            headers["sec-ch-ua-mobile"] = "?0"
            headers["sec-ch-ua-platform"] = cfg["platform"]
            
        headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers["User-Agent"] = cfg["ua"]
        headers["Origin"] = "https://ticketing.colosseo.it"
        headers["Sec-Fetch-Site"] = "same-origin"
        headers["Sec-Fetch-Mode"] = "cors"
        headers["Sec-Fetch-Dest"] = "empty"
        headers["Referer"] = f"https://ticketing.colosseo.it/{self.lang}/event/parco-colosseo-24h/"
        headers["Accept-Encoding"] = "gzip, deflate, br"
        
        langs = [f"{self.lang},en-US;q=0.9,en;q=0.8", f"it-IT,it;q=0.9,en-US;q=0.8", "en-GB,en;q=0.8"]
        random.shuffle(langs)
        headers["Accept-Language"] = langs[0]
        
        return headers

    def resolve_dns(self, host):
        global DNS_CACHE
        if host not in DNS_CACHE:
            try:
                DNS_CACHE[host] = socket.gethostbyname(host)
            except Exception:
                return host
        return DNS_CACHE[host]

    def request_with_backoff(self, method, url, **kwargs):
        max_retries = 3
        for i in range(max_retries):
            try:
                resp = self.session.request(method, url, **kwargs)
                
                if "queue-it" in resp.text.lower() or "queue-it.net" in resp.url:
                    logger.error("🛑 Hit Queue-it waiting room. Aborting.")
                    return None
                    
                if resp.status_code == 200:
                    return resp
                elif resp.status_code in [403, 429, 500, 503]:
                    wait = (2 ** (i + 1)) + random.random()
                    time.sleep(wait)
                else:
                    return resp
            except Exception as e:
                wait = (2 ** (i + 1)) + random.random()
                time.sleep(wait)
        return None
    
    def fetch_dynamic_guid(self):
        logger.info("Fetching dynamic Event GUID...")
        try:
            url = f"https://ticketing.colosseo.it/{self.lang}/event/parco-colosseo-24h/"
            resp = self.request_with_backoff("GET", url, headers=self.base_headers, timeout=30)
            
            if resp and resp.status_code == 200:
                match = re.search(r'["\']guid["\']\s*:\s*["\']([a-f0-9\-]{36})["\']', resp.text)
                if match:
                    self.event_guid = match.group(1)
                    logger.info(f"✅ Found Dynamic GUID: {self.event_guid}")
                    return True
        except Exception as e:
            logger.error(f"Failed to fetch dynamic GUID: {e}")
            
        self.event_guid = "ce1af0d8-41e9-4e97-88cf-938e52ec8dbb"
        logger.warning(f"⚠️ Using Fallback GUID: {self.event_guid}")
        return False

    def generate_trust_cookies(self):
        logger.info(f"Pre-Warming Colosseum Session (Target: {self.impersonate})...")
        try:
            # 1. Hit the Landing Page
            url = f"https://ticketing.colosseo.it/{self.lang}/event/parco-colosseo-24h/"
            resp = self.session.get(url, headers=self.base_headers, timeout=30)
            
            # 2. CHECK FOR OCTOFENCE / QUEUE
            if "waiting_styles.css" in resp.text or "queue-it" in resp.text:
                logger.warning("🛑 HIT WAITING ROOM! Starting Queue Logic...")
                
                # Simple Wait Strategy
                # We retry checking the status every 5 seconds
                for i in range(6): # Try for 30 seconds
                    time.sleep(5)
                    logger.info(f"⏳ Waiting in queue... ({i+1}/6)")
                    resp = self.session.get(url, headers=self.base_headers, timeout=30)
                    
                    if "waiting_styles.css" not in resp.text and "queue-it" not in resp.text:
                        logger.info("🎉 PASSED THE QUEUE!")
                        break
                else:
                    logger.error("❌ Failed to pass queue after retries.")
                    return # Abort if still in queue

            # 3. Extract GUID only if we are on the real page
            match = re.search(r'uuid["\']\s*:\s*["\']([a-f0-9\-]+)["\']', resp.text)
            if match:
                self.event_guid = match.group(1)
                logger.info(f"✅ Dynamic GUID Found: {self.event_guid}")
            
            logger.info(f"Trust Established. Cookies: {len(self.session.cookies)}")
            for k, v in self.session.cookies.items():
                logger.info(f"Cookie: {k}={v[:10]}...")

        except Exception as e:
            logger.error(f"Trust generation failed: {e}")

    def get_availability(self, year, month, day=None):
        url = "https://ticketing.colosseo.it/mtajax/calendars_month"
        data = {
            "action": "midaabc_calendars_month",
            "guids[entranceEvent_guid][]": self.event_guid,
            "year": year,
            "month": month,
            "day": day if day else ""
        }
        
        resp = self.request_with_backoff("POST", url, data=data, headers=self.base_headers, timeout=30)
        if resp and resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return None
        return None

    def parse_time_slots(self, response_data, date_str):
        slots = []
        if not response_data or 'result' not in response_data:
            return slots
        
        events = response_data.get('result', {}).get(self.event_guid, [])
        
        if not events:
            for key in response_data.get('result', {}):
                if len(key) == 36:
                    events = response_data['result'][key]
                    break
        
        for event in events:
            capacity = event.get('capacity')
            needed = event.get('neededCapacity', 1)
            if capacity is not None and capacity >= needed:
                slots.append({
                    "time": event.get('start_time', ''),
                    "availability": f"{capacity} left",
                    "id": event.get('guid')
                })
        return slots

    def check_dates(self, target_dates):
        # 1. Try to load "Fast Pass" cookies if we don't have them
        if not self.session.cookies:
            if not self.load_cached_session():
                logger.info("ℹ️ No cached session. Using Direct API / Proxy.")
        
        # 2. Ensure GUID (Try dynamic, fallback to hardcoded)
        if not self.event_guid:
            self.fetch_dynamic_guid()

        results = {}
        for date_str in target_dates:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            
            # 3. Hit API
            resp_json = self.get_availability(dt.year, dt.month, dt.day)
            
            # 4. Handle Failure (Queue detected in get_availability?)
            if not resp_json:
                # If API failed, it might be the Queue or 403. 
                # Last resort: Try generating cookies manually ONCE per run
                if not self.session.cookies and not hasattr(self, '_trust_tried'):
                    self.generate_trust_cookies()
                    self._trust_tried = True
                    # Retry API
                    resp_json = self.get_availability(dt.year, dt.month, dt.day)

            if resp_json:
                slots = self.parse_time_slots(resp_json, date_str)
                if slots:
                    logger.info(f"🎉 SUCCESS: Found {len(slots)} slots for {date_str}!")
                    results[date_str] = slots
            
            time.sleep(random.uniform(3.0, 7.0))
            
        return results

if __name__ == "__main__":
    monitor = ColosseumPro()
    res = monitor.check_dates(["2026-02-23"]) 
    print(json.dumps(res, indent=2))
