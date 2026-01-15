import asyncio
from playwright.async_api import async_playwright


async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://foerderportal.bund.de/easy/easy_index.php?auswahl=formularschrank_foerderportal&formularschrank=bmbf"

        print(f"Visiting {url}")
        await page.goto(url, wait_until="load")

        # Check t1 content
        try:
            t1_html = await page.inner_html("#t1")
            print("T1 HTML preview:", t1_html[:1000])

            # Check rows
            rows = await page.evaluate("document.querySelectorAll('#t1 tr').length")
            print(f"Rows in t1: {rows}")
        except Exception as e:
            print(f"Error accessing #t1: {e}")
            # Dump all IDs
            ids = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('[id]')).map(el => el.id);
            }""")
            print("Found IDs:", ids)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
