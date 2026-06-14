"""Ultra-minimal debug: what does Google Maps actually show?"""

import asyncio
from playwright.async_api import async_playwright


async def debug():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()

        print("Navigating to Google Maps...")
        await page.goto("https://www.google.com/maps", timeout=30000)
        print(f"URL after navigation: {page.url}")
        print(f"Page title: {await page.title()}")

        # Wait a bit
        await asyncio.sleep(5)
        print(f"URL after 5s wait: {page.url}")

        # Check for consent screen
        content = await page.content()
        has_consent = "consent" in content.lower() or "agree" in content.lower() or "cookie" in content.lower()
        print(f"Page mentions consent/agree/cookie: {has_consent}")

        # Check for any buttons
        buttons = await page.locator("button").all()
        print(f"\nTotal <button> elements: {len(buttons)}")
        for i, btn in enumerate(buttons[:15]):
            try:
                text = (await btn.inner_text(timeout=2000)).strip()[:80]
                visible = await btn.is_visible()
                print(f"  [{i}] visible={visible} text='{text}'")
            except:
                print(f"  [{i}] (could not read)")

        # Check for search box with various selectors
        search_selectors = [
            'input[name="q"]',
            '#searchboxinput',
            'input[aria-label="Search Google Maps"]',
            'input[type="text"]',
            'input',
        ]
        print(f"\nSearch box detection:")
        for sel in search_selectors:
            count = await page.locator(sel).count()
            print(f"  '{sel}': {count} found")

        # Dump page text (to see what's visible)
        try:
            body_text = await page.locator("body").inner_text(timeout=3000)
            print(f"\nPage body text (first 1500 chars):")
            print(body_text[:1500])
        except Exception as e:
            print(f"\nCould not get body text: {e}")

        # Try clicking consent buttons
        consent_texts = ["Accept all", "Reject all", "I agree", "Accept"]
        for text in consent_texts:
            try:
                btn = page.get_by_role("button", name=text)
                count = await btn.count()
                if count > 0:
                    print(f"\n>>> Found consent button: '{text}', clicking it...")
                    await btn.click(timeout=3000)
                    await asyncio.sleep(3)
                    print(f"URL after consent: {page.url}")
                    
                    # Re-check search box
                    search_count = await page.locator('input[name="q"]').count()
                    print(f"Search box after consent: {search_count} found")
                    break
            except:
                pass

        await context.close()
        await browser.close()
        print("\n=== DEBUG COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(debug())
