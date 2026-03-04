import asyncio
import os
import json
import logging
from playwright.async_api import async_playwright
from curl_cffi.requests import AsyncSession
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Diagnostic")

load_dotenv()

async def diagnostic():
    logger.info("Diagnostic Start (Browser + HTTP Hybrid)")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        logger.info("Browser: Navigating to home...")
        await page.goto("https://tickets.museivaticani.va/home", wait_until="networkidle")
        
        logger.info("Browser: Extracting cookies...")
        cookies = await context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}
        logger.info(f"Cookies found: {list(cookie_dict.keys())}")
        
        xsrf_token = cookie_dict.get('XSRF-TOKEN') or cookie_dict.get('__Host-XSRF-TOKEN')
        if xsrf_token:
            logger.info(f"✅ Found XSRF Token: {xsrf_token[:10]}...")
        else:
            logger.warning("❌ No XSRF Token found in cookies")
            
        await browser.close()
        
        # Now try HTTP with these cookies and XSRF header
        logger.info("Testing HTTP API with browser cookies...")
        async with AsyncSession(impersonate="chrome120", verify=False) as session:
            session.cookies.update(cookie_dict)
            headers = {
                "Referer": "https://tickets.museivaticani.va/",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest",
            }
            if xsrf_token:
                # url-decode if needed? Usually .NET expects it as received
                import urllib.parse
                headers["X-XSRF-TOKEN"] = urllib.parse.unquote(xsrf_token)
            
            logger.info("Checking /api/home/info...")
            resp = await session.get("https://tickets.museivaticani.va/api/home/info?lang=it", headers=headers, timeout=10)
            logger.info(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    logger.info(f"✅ Success! Site Name: {data.get('siteName')}")
                except:
                    logger.error("❌ Still got HTML instead of JSON")
                    logger.info(f"Snippet: {resp.text[:200]}")
            else:
                logger.error(f"Failed with status {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(diagnostic())
