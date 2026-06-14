import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_page()
        print("Navigating to maps...")
        await context.goto("https://www.google.com/maps/search/Car+Tinted+Sunway", timeout=60000)
        await asyncio.sleep(8)
        
        # Click the first result to open sidebar
        print("Clicking first result...")
        try:
            # Try to click the first a.hfpxzc
            cards = context.locator('a.hfpxzc')
            if await cards.count() > 0:
                await cards.first.click()
                await asyncio.sleep(5)
                
                print("Capturing sidebar content...")
                sidebar = await context.content()
                with open("sidebar_debug.html", "w") as f:
                    f.write(sidebar)
                await context.screenshot(path="sidebar_debug.png")
                print("Sidebar captured.")
            else:
                print("No cards found with a.hfpxzc")
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())
