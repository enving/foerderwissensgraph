import asyncio
from playwright.async_api import async_playwright
import sys


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://localhost:8000/docs/dashboard.html")
        await asyncio.sleep(5)

        await page.fill("#hybridSearchInput", "BHO")
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)
        await page.screenshot(path="docs/screenshots/audit_search_bho.png")

        await page.evaluate("""() => {
            const nodes = document.querySelectorAll('.node');
            if (nodes.length > 0) {
                const event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                nodes[0].dispatchEvent(event);
            }
        }""")
        await asyncio.sleep(1)
        await page.screenshot(path="docs/screenshots/audit_node_click.png")

        sidebar_text = await page.inner_text("#sidebar")
        print("Sidebar Content after click:")
        print(sidebar_text[:500])

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
