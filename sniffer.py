import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        async def handle_response(response):
            if "api" in response.url:
                try:
                    # We might need to handle empty responses or text
                    if response.status == 200:
                        body = await response.json()
                        results.append({
                            "url": response.url,
                            "status": response.status,
                            "body": body
                        })
                except:
                    pass
        
        page.on("response", handle_response)
        
        print("Navigating to an available date (27/02/2026)...")
        # ts = 1772146800000 (roughly 27/02/2026)
        # Actually, let's just go to 20/03/2026 if it's state 1
        await page.goto("https://tickets.museivaticani.va/home/fromtag/2/1772146800000/MV-Biglietti/1", wait_until="networkidle")
        
        print("Waiting for 'PRENOTA' buttons...")
        try:
            await page.wait_for_selector("[data-cy^='bookTicket_']", timeout=10000)
            print("Clicking first ticket...")
            await page.click("[data-cy^='bookTicket_']:first-of-type")
            
            print("Waiting for response...")
            await page.wait_for_timeout(5000)

        except Exception as e:
            print(f"Workflow error: {e}")
        
        with open("api_available_date.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"Saved {len(results)} API responses to api_available_date.json")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
