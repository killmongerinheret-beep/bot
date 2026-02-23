"""
VATICAN BOT - GOD TIER IMPLEMENTATION
Response Interception + Caching + High-Speed Monitor

This module implements the optimal 3-phase workflow:
1. Recon: Intercept JSON catalog responses (Method A) + DOM fallback (Method B)
2. Validation: Test harvested IDs with API calls
3. Handover: Cache confirmed IDs for high-speed monitoring
"""

import asyncio
import json
import time
import logging
from pathlib import Path
from playwright.async_api import async_playwright

logger = logging.getLogger("GodTierBot")

class VaticanGodTierBot:
    
    def __init__(self, proxies=None):
        self.cache_dir = Path("vatican_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = 86400  # 24 hours
        self.proxies = proxies if proxies else []  # Proxy list for rotation
    
    # ===== PHASE 1: RECON (Response Interception) =====
    
    async def harvest_ids_with_interception(self, page, ticket_type, target_date, visitors=2):
        """
        GOD TIER Method: Intercepts background JSON responses
        Fallback: DOM scraping if interception fails
        """
        catalog_data = None
        intercepted = False
        
        # Response handler
        async def handle_response(response):
            nonlocal catalog_data, intercepted
            url = response.url
            
            # Look for catalog/visitTypes/tickets endpoints
            if any(keyword in url.lower() for keyword in ['catalog', 'visittype', 'tickets', 'products']):
                try:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0:
                            catalog_data = data
                            intercepted = True
                            logger.info(f"📦 [Method A] Intercepted catalog from {url}: {len(data)} items")
                except Exception as e:
                    logger.debug(f"Failed to parse response from {url}: {e}")
        
        # Attach listener BEFORE navigation
        page.on("response", handle_response)
        
        # ✅ FIX: Decouple Tag ID from Visitor Count
        if ticket_type == 0:
            tag_id = 1       # Standard Tickets are ALWAYS Tag 1 (Public Pool)
            slug = "MV-Biglietti"
        else:
            tag_id = 2       # Guided Tours are ALWAYS Tag 2
            slug = "MV-Visite-Guidate"
        
        # Navigate to deep link
        ts = self._get_timestamp(target_date)
        
        # ✅ CORRECT URL: /fromtag/{tag_id}/{timestamp}/{slug}/1
        # The tag_id is FIXED per ticket type (NOT visitor count!)
        deep_url = f"https://tickets.museivaticani.va/home/fromtag/{tag_id}/{ts}/{slug}/1"
        
        logger.info(f"🕸️ Navigating to deep link: {deep_url}")
        await page.goto(deep_url, wait_until="load", timeout=60000)
        
        # Wait for interception (shorter timeout since we're looking for network response)
        await page.wait_for_timeout(2000)
        
        # Remove listener
        page.remove_listener("response", handle_response)
        
        if intercepted and catalog_data:
            # Method A: Parse intercepted JSON
            logger.info(f"✅ [Method A] Using intercepted catalog")
            return self._parse_catalog_json(catalog_data)
        else:
            # Method B: Fallback to DOM scraping
            logger.warning(f"⚠️ [Method A] Failed, using DOM fallback")
            await page.wait_for_timeout(2000)  # Extra wait for DOM
            return await self._extract_ids_from_dom(page)
    
    def _parse_catalog_json(self, catalog_data):
        """Parse intercepted JSON catalog"""
        items = []
        for item in catalog_data:
            if isinstance(item, dict) and 'id' in item:
                items.append({
                    "id": str(item.get('id', '')),
                    "name": item.get('name', item.get('title', 'Unknown')),
                    "price": item.get('price', 0)
                })
        return items
    
    async def _extract_ids_from_dom(self, page):
        """Fallback: Extract IDs from DOM - using exact .muvaTicketTitle class"""
        ids_js = """
        () => {
            const results = [];
            const buttons = document.querySelectorAll("[data-cy^='bookTicket_']");
            
            buttons.forEach(btn => {
                const id = btn.getAttribute("data-cy").split("_")[1];
                let name = "Unknown Ticket";
                
                // STRATEGY: Climb up to find the main container, then find the specific title class
                let currentEl = btn;
                
                // Climb up 5 levels max to find the container that holds the title
                for (let i = 0; i < 5; i++) {
                    currentEl = currentEl.parentElement;
                    if (!currentEl) break;
                    
                    // 🎯 TARGET: The exact class found in DOM inspection
                    const exactTitle = currentEl.querySelector('.muvaTicketTitle');
                    if (exactTitle) {
                        name = exactTitle.innerText.trim();
                        break;
                    }
                    
                    // Fallback: If exact class isn't there, look for headers
                    const genericTitle = currentEl.querySelector('h1, h2, h3, h4');
                    if (genericTitle) {
                         name = genericTitle.innerText.trim();
                         break;
                    }
                }
                
                results.push({id, name});
            });
            return results;
        }
        """
        
        found_items = await page.evaluate(ids_js)
        
        # Deduplicate
        seen = set()
        unique = []
        for item in found_items:
            if item['id'] not in seen:
                seen.add(item['id'])
                unique.append(item)
        
        logger.info(f"✅ [Method B] Extracted {len(unique)} IDs from DOM")
        return unique
    
    # ===== PHASE 2: VALIDATION =====
    
    async def validate_ids(self, page, ticket_ids, test_date, visitors=2):
        """
        Test each harvested ID with real API call
        Returns only confirmed working IDs
        """
        confirmed = []
        
        logger.info(f"🔍 Validating {len(ticket_ids)} IDs...")
        
        for item in ticket_ids:
            ticket_id = item['id']
            
            # Test API call
            is_valid = await self._test_single_id(page, ticket_id, test_date, visitors)
            
            if is_valid:
                confirmed.append(item)
                logger.info(f"✅ ID {ticket_id} ({item['name']}) - CONFIRMED")
            else:
                logger.warning(f"❌ ID {ticket_id} - REJECTED")
            
            await asyncio.sleep(0.1)  # Small delay between validations
        
        return confirmed
    
    async def _test_single_id(self, page, ticket_id, date, visitors):
        """Test if ID returns valid response from API"""
        try:
            api_date = self._format_date(date)
            url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={api_date}"
            
            js = f"""
            async () => {{
                try {{
                    const resp = await fetch("{url}");
                    if (!resp.ok) return false;
                    const data = await resp.json();
                    return !data.error;  // Valid if no error field
                }} catch (e) {{
                    return false;
                }}
            }}
            """
            
            result = await page.evaluate(js)
            return result
        except:
            return False
    
    # ===== PHASE 3: HANDOVER (Caching) =====
    
    def save_confirmed_ids(self, ticket_ids, tag):
        """Cache validated IDs to disk"""
        cache_file = self.cache_dir / f"ids_{tag}.json"
        data = {
            "timestamp": time.time(),
            "tag": tag,
            "ids": ticket_ids
        }
        cache_file.write_text(json.dumps(data, indent=2))
        logger.info(f"💾 Cached {len(ticket_ids)} confirmed IDs for {tag}")
    
    def load_cached_ids(self, tag):
        """Load IDs from cache if fresh"""
        cache_file = self.cache_dir / f"ids_{tag}.json"
        
        if not cache_file.exists():
            return None
        
        data = json.loads(cache_file.read_text())
        age = time.time() - data["timestamp"]
        
        if age > self.cache_ttl:
            logger.info(f"⏰ Cache expired (age: {age/3600:.1f}h)")
            return None
        
        logger.info(f"✅ Using cached IDs (age: {age/60:.1f}m)")
        return data
    
    # ===== HIGH-SPEED MONITOR MODE =====
    
    async def high_speed_monitor(self, ticket_ids, dates, visitors=2):
        """
        SECURED High-Speed Mode:
        - Rotates Proxies
        - Fakes Browser User-Agent
        - Limits Concurrency (Semaphore to prevent DDoS detection)
        """
        try:
            import aiohttp
            import random
        except ImportError:
            logger.error("aiohttp not installed. Run: pip install aiohttp")
            return []
        
        results = []
        
        # 1. Fake Headers (Look like a Browser)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://tickets.museivaticani.va/",
            "Origin": "https://tickets.museivaticani.va"
        }
        
        # 2. Semaphore (Limit to 10 concurrent requests to avoid volumetric ban)
        sem = asyncio.Semaphore(10)
        
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = []
            
            for i, date in enumerate(dates):
                api_date = self._format_date(date)
                
                for item in ticket_ids:
                    ticket_id = item['id']
                    url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={api_date}"
                    
                    # 3. Rotate Proxy (Simple Round Robin)
                    proxy = self.proxies[i % len(self.proxies)] if self.proxies else None
                    
                    tasks.append(self._fetch_api_secured(sem, session, url, proxy, ticket_id, date))
            
            logger.info(f"⚡ HIGH-SPEED: Queued {len(tasks)} requests (Max 10 concurrent)...")
            
            # 4. Fire with concurrency control
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for resp in responses:
                if isinstance(resp, dict) and resp.get('slots'):
                    results.append(resp)
        
        return results
    
    async def _fetch_api_secured(self, sem, session, url, proxy, ticket_id, date):
        """Secured fetch with concurrency limit and error handling"""
        async with sem:  # Wait for a free slot
            try:
                # Optional: Add random jitter to prevent pattern detection
                # await asyncio.sleep(random.uniform(0.05, 0.15))
                
                async with session.get(url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        slots = data.get('timetable', [])
                        available = [s for s in slots if s.get('availability') != 'SOLD_OUT']
                        
                        if available:
                            return {
                                'ticket_id': ticket_id,
                                'date': date,
                                'slots': [s['time'] for s in available]
                            }
                    elif resp.status in [403, 429]:
                        logger.warning(f"⚠️ Blocked ({resp.status}) on {date}. Rotate Proxy.")
            except Exception as e:
                # logger.debug(f"Fetch failed: {e}")
                pass
            return None
    
    # ===== ORCHESTRATOR =====
    
    async def god_tier_orchestrator(self, dates, ticket_type=0, visitors=2):
        """
        Main workflow:
        1. Check cache
        2. If fresh: Use high-speed mode
        3. If stale: Run reconnaissance → cache → high-speed mode
        """
        tag = "MV-Biglietti" if ticket_type == 0 else "MV-Visite-Guidate"
        
        # Check cache
        cached = self.load_cached_ids(tag)
        
        if cached:
            # Cache hit - use high-speed mode
            logger.info("🚀 CACHE HIT - Activating HIGH-SPEED MODE")
            return await self.high_speed_monitor(cached['ids'], dates, visitors)
        else:
            # Cache miss - run full reconnaissance
            logger.info("🔍 CACHE MISS - Running RECONNAISSANCE MODE")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Phase 1: Harvest
                test_date = dates[0] if dates else "2026-02-15"
                ticket_ids = await self.harvest_ids_with_interception(
                    page, ticket_type, test_date, visitors
                )
                
                if not ticket_ids:
                    logger.error("❌ No IDs harvested")
                    await browser.close()
                    return []
                
                # Phase 2: Validate
                confirmed = await self.validate_ids(page, ticket_ids, test_date, visitors)
                
                # Phase 3: Cache
                self.save_confirmed_ids(confirmed, tag)
                
                await browser.close()
            
            # Now run high-speed mode with confirmed IDs
            logger.info("⚡ Switching to HIGH-SPEED MODE")
            return await self.high_speed_monitor(confirmed, dates, visitors)
    
    # ===== HELPERS =====
    
    def _get_timestamp(self, date_str):
        """Convert date to Rome midnight timestamp (ms)"""
        from zoneinfo import ZoneInfo
        from datetime import datetime
        
        rome = ZoneInfo("Europe/Rome")
        if "/" in date_str:
            dt = datetime.strptime(date_str, "%d/%m/%Y")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        
        midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
        return int(midnight.timestamp() * 1000)
    
    def _format_date(self, date_str):
        """Convert to DD/MM/YYYY for API"""
        if "/" in date_str:
            return date_str
        
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")


# ===== USAGE EXAMPLE =====

async def main():
    bot = VaticanGodTierBot()
    
    dates = [
        "2026-02-10",
        "2026-02-11", 
        "2026-02-12",
        "2026-02-13",
        "2026-02-14"
    ]
    
    results = await bot.god_tier_orchestrator(
        dates=dates,
        ticket_type=0,  # Standard
        visitors=2
    )
    
    if results:
        print(f"\n🎯 FOUND {len(results)} AVAILABLE SLOTS:")
        for r in results:
            print(f"  Date: {r['date']}, Slots: {r['slots']}")
    else:
        print("\n❌ No availability found")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
