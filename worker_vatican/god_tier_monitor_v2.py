"""
God-Tier Vatican Monitor V2
===========================
Fixed version with:
- Proper API session validation
- Correct cookie handling for HTTP API
- Better error handling and logging
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from curl_cffi.requests import AsyncSession

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GodTierVaticanV2")

# Constants
# Use script directory for session file (works on Windows + Docker)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.environ.get("VATICAN_SESSION_FILE", os.path.join(_SCRIPT_DIR, "vatican_session.json"))
CACHE_MAX_AGE_HOURS = 4  # 4 hours as per working configuration
CONCURRENT_REQUESTS = 8
RATE_LIMIT_RPS = 10
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0


class GodTierVaticanMonitorV2:
    """
    Ultra-fast Vatican ticket monitor with fixed session handling.
    """
    
    def __init__(self, proxies: List[str] = None, sticky_proxy: bool = True):
        self.proxies = proxies or self._load_proxies()
        self.session_cache = self._load_session()
        self.semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
        self.rate_limit_delay = 1.0 / RATE_LIMIT_RPS
        self.last_request_time = 0
        
        # Sticky proxy
        self.sticky_proxy = sticky_proxy
        self.current_proxy = None
        if sticky_proxy and self.proxies:
            self.current_proxy = random.choice(self.proxies)
            logger.info(f"🔒 Sticky Proxy: {self.current_proxy.split(':')[0]}:***")
        
    def _load_proxies(self) -> List[str]:
        """Load proxies from environment or files."""
        proxies = []
        try:
            proxy_env = os.getenv('PROXY_LIST')
            if proxy_env:
                return proxy_env.split(',')
            
            search_paths = ["/app", ".", "..", "../.."]
            for base_dir in search_paths:
                json_path = os.path.join(base_dir, "Proxy lists.json")
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                        for p in data:
                            entry = f"{p['entryPoint']}:{p['port']}"
                            proxies.append(entry)
                    logger.info(f"✅ Loaded {len(proxies)} Oxylabs proxies")
                    return proxies
        except Exception as e:
            logger.warning(f"⚠️ Could not load proxies: {e}")
        
        return proxies
    
    def _load_session(self) -> Dict:
        """Load cached session from file."""
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r') as f:
                    data = json.load(f)
                    last_updated = data.get('last_updated', '')
                    if last_updated:
                        last_dt = datetime.fromisoformat(last_updated)
                        age_hours = (datetime.now() - last_dt).total_seconds() / 3600
                        if age_hours < CACHE_MAX_AGE_HOURS:
                            logger.info(f"📂 Loaded cached session (age: {age_hours:.1f}h)")
                            return data
                        else:
                            logger.info(f"⏰ Session expired (age: {age_hours:.1f}h)")
                    return data
            except Exception as e:
                logger.error(f"❌ Failed to load session: {e}")
        return {"cookies": [], "ids_cache": {}, "last_updated": ""}
    
    def _save_session(self, cookies: List[Dict], ids_cache: Dict):
        """Save session to file."""
        try:
            data = {
                "cookies": cookies,
                "ids_cache": ids_cache,
                "last_updated": datetime.now().isoformat()
            }
            os.makedirs(os.path.dirname(SESSION_FILE) or ".", exist_ok=True)
            with open(SESSION_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("💾 Session cached successfully")
            self.session_cache = data
        except Exception as e:
            logger.error(f"❌ Failed to save session: {e}")
    
    def _get_proxy_url(self, proxy_str: str) -> Optional[str]:
        """Convert proxy string to URL format for curl_cffi."""
        if not proxy_str:
            return None
        try:
            if "@" in proxy_str:
                return f"http://{proxy_str}" if "http" not in proxy_str else proxy_str
            elif ":" in proxy_str:
                parts = proxy_str.split(':')
                if len(parts) == 4:
                    return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                elif len(parts) == 2:
                    if 'oxylabs' in proxy_str.lower():
                        user = os.getenv('OXYLABS_USERNAME')
                        pwd = os.getenv('OXYLABS_PASSWORD')
                        if user and pwd:
                            return f"http://{user}:{pwd}@{parts[0]}:{parts[1]}"
                    return f"http://{parts[0]}:{parts[1]}"
        except Exception as e:
            logger.warning(f"⚠️ Proxy parse error: {e}")
        return None
    
    async def _rate_limited_request(self, session: AsyncSession, url: str, max_retries: int = RETRY_MAX_ATTEMPTS) -> Optional[Dict]:
        """Make rate-limited request with retry logic."""
        async with self.semaphore:
            for attempt in range(max_retries):
                try:
                    now = time.time()
                    time_since_last = now - self.last_request_time
                    if time_since_last < self.rate_limit_delay:
                        await asyncio.sleep(self.rate_limit_delay - time_since_last)
                    
                    self.last_request_time = time.time()
                    
                    resp = await session.get(url, timeout=15)
                    
                    if resp.status_code == 200:
                        try:
                            return resp.json()
                        except:
                            logger.warning(f"⚠️ Invalid JSON from {url}")
                            return None
                    elif resp.status_code in (401, 403):
                        logger.warning(f"🔒 Session expired (status {resp.status_code})")
                        return None
                    elif resp.status_code == 429:
                        wait_time = (attempt + 1) * RETRY_BASE_DELAY * 2
                        logger.warning(f"⏳ Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.debug(f"⚠️ HTTP {resp.status_code} for {url}")
                        
                except Exception as e:
                    wait_time = (attempt + 1) * RETRY_BASE_DELAY
                    logger.debug(f"⚠️ Request failed (attempt {attempt+1}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
            
            return None
    
    async def validate_api_session(self) -> bool:
        """
        Validate session by making a real API call.
        This is the key fix - we test the actual API endpoint.
        """
        if not self.session_cache.get("cookies"):
            return False
        
        cookie_dict = {c['name']: c['value'] for c in self.session_cache['cookies']}
        
        try:
            proxy_url = None
            if self.proxies:
                proxy_str = self.current_proxy if self.sticky_proxy and self.current_proxy else random.choice(self.proxies)
                proxy_url = self._get_proxy_url(proxy_str)
            
            async with AsyncSession(
                verify=False, 
                impersonate="chrome120",
                proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None
            ) as session:
                session.cookies.update(cookie_dict)
                session.headers.update({
                    "Referer": "https://tickets.museivaticani.va/",
                    "Accept": "application/json, text/plain, */*",
                    "X-Requested-With": "XMLHttpRequest"
                })
                
                # Test with a real API call - use a known ticket ID or the home endpoint
                # The home/info endpoint is lightweight and good for validation
                resp = await session.get(
                    "https://tickets.museivaticani.va/api/home/info",
                    timeout=10
                )
                
                if resp.status_code == 200:
                    logger.info("✅ API session validation passed")
                    return True
                else:
                    logger.warning(f"❌ API session validation failed: HTTP {resp.status_code}")
                    return False
                
        except Exception as e:
            logger.debug(f"Session validation error: {e}")
            return False
    
    async def refresh_session_with_browser(self, ticket_type: int = 0, target_date: str = "27/02/2026") -> bool:
        """Use Playwright browser to get fresh session cookies and IDs."""
        if not HAS_PLAYWRIGHT:
            logger.error("❌ Playwright not installed")
            return False
        
        logger.info("🔄 Refreshing session with browser...")
        
        try:
            async with async_playwright() as p:
                proxy_str = self.current_proxy if self.sticky_proxy and self.current_proxy else (random.choice(self.proxies) if self.proxies else None)
                proxy_config = None
                
                if proxy_str and ":" in proxy_str:
                    parts = proxy_str.split(':')
                    if len(parts) == 4:
                        proxy_config = {
                            "server": f"http://{parts[0]}:{parts[1]}",
                            "username": parts[2],
                            "password": parts[3]
                        }
                    elif len(parts) == 2 and 'oxylabs' in proxy_str.lower():
                        user = os.getenv('OXYLABS_USERNAME')
                        pwd = os.getenv('OXYLABS_PASSWORD')
                        if user and pwd:
                            proxy_config = {
                                "server": f"http://{proxy_str}",
                                "username": user,
                                "password": pwd
                            }
                
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy_config,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage"
                    ]
                )
                
                context = await browser.new_context(
                    locale="it-IT",
                    timezone_id="Europe/Rome",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                
                page = await context.new_page()
                
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = { runtime: {} };
                """)
                
                # Build deep link
                from zoneinfo import ZoneInfo
                from datetime import datetime as dt
                
                if "/" in target_date:
                    day, month, year = target_date.split('/')
                    dt_obj = dt(int(year), int(month), int(day))
                else:
                    dt_obj = dt.strptime(target_date, "%Y-%m-%d")
                
                rome = ZoneInfo("Europe/Rome")
                midnight = dt_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
                ts = int(midnight.timestamp() * 1000)
                
                # Use correct slug based on ticket type
                slug = "MV-Biglietti" if ticket_type == 0 else "MV-Visite-Guidate"
                visitors = 3 if ticket_type == 0 else 2
                deep_url = f"https://tickets.museivaticani.va/home/fromtag/{visitors}/{ts}/{slug}/1"
                
                logger.info(f"🔗 Navigating to: {deep_url}")
                await page.goto(deep_url, timeout=45000, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                
                # Extract cookies
                cookies = await context.cookies()
                
                # Extract ticket IDs
                ids_js = """
                () => {
                    const results = [];
                    const buttons = document.querySelectorAll("[data-cy^='bookTicket_']");
                    buttons.forEach(btn => {
                        const id = btn.getAttribute("data-cy").split("_")[1];
                        let name = "Unknown";
                        let currentEl = btn;
                        for (let i = 0; i < 5; i++) {
                            currentEl = currentEl.parentElement;
                            if (!currentEl) break;
                            const exactTitle = currentEl.querySelector('.muvaTicketTitle');
                            if (exactTitle) {
                                name = exactTitle.innerText.trim();
                                break;
                            }
                            const genericTitle = currentEl.querySelector('h1, h2, h3, h4');
                            if (genericTitle) {
                                name = genericTitle.innerText.trim();
                                break;
                            }
                        }
                        results.push({id: id, name: name});
                    });
                    return results;
                }
                """
                ids = await page.evaluate(ids_js)
                
                await browser.close()
                
                if ids:
                    ids_cache = {target_date: ids}
                    self._save_session(cookies, ids_cache)
                    logger.info(f"✅ Session refreshed! Got {len(ids)} ticket IDs")
                    return True
                else:
                    logger.error("❌ No ticket IDs found during refresh")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Browser refresh failed: {e}")
            return False
    
    async def check_availability(
        self, 
        date_str: str, 
        ticket_type: int = 0,
        languages: List[str] = None
    ) -> List[Dict]:
        """
        Check ticket availability using HTTP API.
        Key fix: Proper session validation against actual API.
        """
        results = []
        
        # Step 1: Validate session against actual API
        if not await self.validate_api_session():
            logger.info("🔄 API session invalid, refreshing with browser...")
            if not await self.refresh_session_with_browser(ticket_type, date_str):
                logger.error("❌ Failed to refresh session")
                return results
        
        # Step 2: Get cached IDs
        cached_ids = self.session_cache.get("ids_cache", {}).get(date_str, [])
        if not cached_ids:
            logger.info(f"🔍 No cached IDs for {date_str}, harvesting...")
            if not await self.refresh_session_with_browser(ticket_type, date_str):
                return results
            cached_ids = self.session_cache.get("ids_cache", {}).get(date_str, [])
        
        if not cached_ids:
            logger.error("❌ No ticket IDs available")
            return results
        
        # Format date for API
        if "-" in date_str:
            parts = date_str.split("-")
            api_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
        else:
            api_date = date_str
        
        # Language setup
        lang_map = {"ITA": "it", "ENG": "en", "FRA": "fr", "DEU": "de", "SPA": "es", "TED": "de"}
        if not languages:
            languages = ["ITA", "ENG"] if ticket_type == 1 else ["ITA"]
        
        # Get proxy
        proxy_url = None
        if self.proxies:
            proxy_str = self.current_proxy if self.sticky_proxy and self.current_proxy else random.choice(self.proxies)
            proxy_url = self._get_proxy_url(proxy_str)
        
        # Build requests
        cookie_dict = {c['name']: c['value'] for c in self.session_cache['cookies']}
        
        async with AsyncSession(
            verify=False, 
            impersonate="chrome120",
            proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None
        ) as session:
            session.cookies.update(cookie_dict)
            session.headers.update({
                "Referer": "https://tickets.museivaticani.va/",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest"
            })
            
            check_tasks = []
            check_meta = []
            
            for item in cached_ids:
                t_id = item['id']
                t_name = item['name']
                
                # Filter by ticket type
                is_guided = "Guidat" in t_name or "Guided" in t_name
                if ticket_type == 0 and is_guided:
                    continue
                if ticket_type == 1 and not is_guided:
                    continue
                
                visitors = 3 if ticket_type == 0 else 2
                
                for lang_code in languages:
                    api_lang = lang_map.get(lang_code, "en")
                    visit_lang_param = f"&visitLang={lang_code}" if is_guided else ""
                    
                    url = (
                        f"https://tickets.museivaticani.va/api/visit/timeavail"
                        f"?lang={api_lang}{visit_lang_param}"
                        f"&visitTypeId={t_id}&visitorNum={visitors}&visitDate={api_date}"
                    )
                    
                    check_tasks.append(self._rate_limited_request(session, url))
                    check_meta.append({
                        "id": t_id,
                        "name": t_name,
                        "lang": lang_code,
                        "date": date_str
                    })
            
            logger.info(f"🔍 Checking {len(check_tasks)} ticket/language combinations...")
            responses = await asyncio.gather(*check_tasks, return_exceptions=True)
            
            # Process results
            for i, resp_data in enumerate(responses):
                if isinstance(resp_data, Exception):
                    continue
                
                if resp_data is None:
                    continue
                
                meta = check_meta[i]
                timetable = resp_data.get("timetable", [])
                
                available_slots = [
                    {"time": t['time'], "availability": t['availability']}
                    for t in timetable
                    if t.get('availability') != 'SOLD_OUT'
                ]
                
                if available_slots:
                    results.append({
                        "ticket_id": meta['id'],
                        "ticket_name": meta['name'],
                        "language": meta['lang'],
                        "date": meta['date'],
                        "slots": available_slots,
                        "total_slots": len(timetable),
                        "available_count": len(available_slots)
                    })
                    logger.info(
                        f"🎉 FOUND: {meta['name']} ({meta['lang']}) - "
                        f"{len(available_slots)} slots"
                    )
        
        return results


# Convenience function for direct use
async def check_vatican_availability(
    date: str,
    ticket_type: int = 0,
    languages: List[str] = None,
    proxies: List[str] = None
) -> List[Dict]:
    """
    Quick check function.
    
    Args:
        date: DD/MM/YYYY or YYYY-MM-DD format
        ticket_type: 0 = Standard, 1 = Guided
        languages: List of language codes (e.g., ["ENG", "ITA"])
        proxies: Optional list of proxy strings
    
    Returns:
        List of available ticket results
    """
    monitor = GodTierVaticanMonitorV2(proxies=proxies)
    return await monitor.check_availability(date, ticket_type, languages)


if __name__ == "__main__":
    # Test the monitor
    async def test():
        monitor = GodTierVaticanMonitorV2()
        results = await monitor.check_availability(
            date_str="27/02/2026",
            ticket_type=0,  # Standard
            languages=["ITA"]
        )
        print(f"Found {len(results)} available tickets")
        for r in results:
            print(f"  {r['ticket_name']}: {len(r['slots'])} slots")
    
    asyncio.run(test())
