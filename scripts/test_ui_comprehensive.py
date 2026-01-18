import os
import time
from playwright.sync_api import sync_playwright

# Configuration
CHROMIUM_PATH = "/home/enving/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome"
URL = "http://localhost:8000/docs/dashboard.html"
SCREENSHOT_DIR = "docs/test_artifacts"


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def run_comprehensive_test():
    ensure_dir(SCREENSHOT_DIR)

    with sync_playwright() as p:
        print(f"🚀 Launching Browser ({CHROMIUM_PATH})...")
        browser = p.chromium.launch(executable_path=CHROMIUM_PATH, headless=True)
        # Grant permissions if needed, though headless usually fine
        # Increased viewport size to avoid elements being out of view
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print(f"🌐 Navigating to {URL}...")
        page.goto(URL)

        # 1. Verify Load
        try:
            page.wait_for_selector("svg#graph", timeout=5000)
            print("✅ Graph SVG loaded")
        except Exception as e:
            print(f"❌ Graph load failed: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error_load.png")
            return

        # 2. Test Filters
        print("🧪 Testing Filters...")
        # Check if Ministry Filter exists
        ministry_select = page.locator("#filterMinistry")
        if ministry_select.is_visible():
            # Select first available option (excluding empty)
            # We need to wait for options to be populated (d3 data load)
            time.sleep(2)

            # Get options
            options = ministry_select.locator("option").all_inner_texts()
            valid_options = [o for o in options if o != "Alle Ressorts"]

            if valid_options:
                target = valid_options[0]
                print(f"   Selecting Ministry: {target}")
                ministry_select.select_option(label=target)
                time.sleep(1)  # Wait for d3 transition
                page.screenshot(path=f"{SCREENSHOT_DIR}/filter_ministry.png")

                # Check for dimmed nodes (visual check via screenshot, but we can check class)
                dimmed_count = page.locator(".node.dimmed").count()
                print(f"   Nodes dimmed: {dimmed_count}")
                if dimmed_count > 0:
                    print("✅ Filter logic applied (nodes dimmed)")
                else:
                    print("⚠️ Filter might not be working (no nodes dimmed)")
            else:
                print("⚠️ No ministry options found")
        else:
            print("❌ Ministry filter not found")

        # 3. Test Sidebar (Click Node)
        print("🧪 Testing Sidebar...")
        # Find a non-dimmed node to click
        visible_node = page.locator(".node:not(.dimmed)").first
        if visible_node.count() > 0:
            # Use dispatch_event to bypass viewport checks completely
            visible_node.dispatch_event("click")
            time.sleep(1)

            # Check sidebar visibility
            sidebar = page.locator("#sidebar")
            # Usually it slides in. Check if it's visible in viewport or just present.
            # Our CSS: w-1/3 bg-white ... flex flex-col z-20
            # It's always in DOM, but maybe hidden off-screen?
            # Looking at CSS: it seems it's always there but maybe 'hidden' class?
            # Actually dashboard.html: <aside id="sidebar" ...>
            # There is no 'hidden' class initially. Let's check 'docTitle'.

            title_text = page.locator("#docTitle").inner_text()
            print(f"   Sidebar Title: {title_text}")

            if title_text != "Wählen Sie ein Dokument aus":
                print("✅ Sidebar updated with node details")
                page.screenshot(path=f"{SCREENSHOT_DIR}/sidebar_open.png")
            else:
                print("❌ Sidebar did not update")
        else:
            print("❌ No visible nodes to click")

        # 4. Test Tooltips
        print("🧪 Testing Tooltips...")
        # Hover over a visible node (not dimmed)
        node = page.locator(".node:not(.dimmed)").nth(0)
        if node.count() > 0:
            # Dispatch events for D3 interaction
            node.dispatch_event("mouseover")
            time.sleep(0.5)

            tooltip = page.locator("#tooltip")
            if tooltip.is_visible():
                print(
                    f"✅ Tooltip visible: {tooltip.inner_text().replace('\n', ' - ')}"
                )
                page.screenshot(path=f"{SCREENSHOT_DIR}/tooltip.png")
            else:
                print("❌ Tooltip not visible")
        else:
            print("⚠️ No visible nodes for tooltip test")

        # 5. Test Zoom Controls
        print("🧪 Testing Zoom...")
        # Find Zoom In button (svg inside button)
        # Using title attribute if available, or onclick
        zoom_btn = page.locator("button[title='Zoom In']")
        if zoom_btn.count() > 0:
            zoom_btn.click()
            time.sleep(0.5)
            # Hard to verify zoom level programmatically without complex checking of transform
            # But we can check if it didn't crash
            print("✅ Zoom In clicked")
        else:
            print("❌ Zoom button not found")

        # 6. Test Search (again, thoroughly)
        print("🧪 Testing Search...")
        page.fill("#hybridSearchInput", "Vergabe")
        page.press("#hybridSearchInput", "Enter")

        try:
            page.wait_for_selector("#searchResults:not(.hidden)", timeout=3000)
            results = page.locator("#resultsList > div").count()
            print(f"✅ Search results visible: {results} items")
            page.screenshot(path=f"{SCREENSHOT_DIR}/search_results.png")
        except:
            print("❌ Search results container did not appear")

        browser.close()
        print(f"\n🏁 Testing Complete. Artifacts in {SCREENSHOT_DIR}")


if __name__ == "__main__":
    run_comprehensive_test()
