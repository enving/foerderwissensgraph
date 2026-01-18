import os
import time
from playwright.sync_api import sync_playwright

# Path found via 'find'
CHROMIUM_PATH = "/home/enving/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome"


def run():
    with sync_playwright() as p:
        print(f"Launching Chromium from {CHROMIUM_PATH}")
        browser = p.chromium.launch(executable_path=CHROMIUM_PATH, headless=True)
        page = browser.new_page()

        # 1. Load Dashboard
        url = "http://localhost:8000/docs/dashboard.html"
        print(f"Navigating to {url}")
        page.goto(url)

        # Check title
        print(f"Title: {page.title()}")

        # 2. Check for Graph
        # Wait for SVG (D3 graph)
        try:
            page.wait_for_selector("svg", timeout=5000)
            print("Graph SVG found ✅")
        except Exception as e:
            print(f"Graph SVG NOT found ❌: {e}")

        # Screenshot Initial State
        page.screenshot(path="docs/screenshot_initial.png")
        print("Screenshot saved: docs/screenshot_initial.png")

        # 3. Test Search
        search_term = "Förderung"
        print(f"Testing search for '{search_term}'...")

        # Input
        page.fill("#hybridSearchInput", search_term)
        page.press("#hybridSearchInput", "Enter")

        # Wait for results
        # Results container id="searchResults" becomes visible (class 'hidden' removed)
        try:
            page.wait_for_selector("#searchResults:not(.hidden)", timeout=5000)
            print("Search results appeared ✅")
        except Exception as e:
            print(f"Search results NOT found ❌: {e}")

        time.sleep(2)  # Wait for animation/render

        page.screenshot(path="docs/screenshot_search.png")
        print("Screenshot saved: docs/screenshot_search.png")

        browser.close()


if __name__ == "__main__":
    run()
