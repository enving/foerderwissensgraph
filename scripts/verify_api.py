import sys
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://foerderwissensgraph.digitalalchemisten.de/api/docs"
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            title = await page.title()
            print(f"Page Title: {title}")
            
            # Check if we are redirected
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            # Take screenshot
            await page.screenshot(path="api_docs_verify.png", full_page=True)
            print("Screenshot saved to api_docs_verify.png")
            
            # Get some content
            content = await page.content()
            print(f"Content length: {len(content)}")
            print(f"First 500 chars of content: {content[:500]}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
