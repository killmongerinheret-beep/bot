"""
Manual check - just open the browser and let me see what's on the page
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Opening March 19 page...")
        print("URL: https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1")
        
        await page.goto("https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1")
        
        print("\nWaiting 30 seconds for you to inspect the page...")
        print("Check if tickets are visible!")
        
        await page.wait_for_timeout(30000)
        
        # Try to extract what's on the page
        html_snippet = await page.evaluate("""
            () => {
                return document.body.innerText.substring(0, 500);
            }
        """)
        
        print("\nPage text:")
        print(html_snippet)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
