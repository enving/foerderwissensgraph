from playwright.sync_api import sync_playwright
import time
import os


def test_filters():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load the local dashboard file
        dashboard_path = os.path.abspath(
            "/home/enving/Dev/Bund-ZuwendungsGraph/docs/dashboard.html"
        )
        page.goto(f"file://{dashboard_path}")
        page.wait_for_load_state("networkidle")

        print(f"Page title: {page.title()}")

        # Check if filter elements exist
        print("Checking filter visibility...")
        print(f"Ministry filter visible: {page.is_visible('#filterMinistry')}")
        print(f"Type filter visible: {page.is_visible('#filterType')}")

        # Try to select BMWK (or BMWE which we know exists in the data)
        # Check available options first
        print("Checking filter options...")
        options = page.eval_on_selector_all(
            "#filterMinistry option", "opts => opts.map(o => o.value)"
        )
        print(f"Available Ministry Options: {options}")

        target_ministry = "BMWE" if "BMWE" in options else "BMWK"
        print(f"Selecting {target_ministry}...")

        # Select option
        page.select_option("#filterMinistry", target_ministry)

        # Wait for transition
        page.wait_for_timeout(1000)

        # Take a screenshot to see the state
        page.screenshot(path="docs/screenshots/filter_test.png")
        print("Screenshot saved to docs/screenshots/filter_test.png")

        # Verify Visual Change: Check if 'dimmed' class is applied to some nodes
        # Since we have filtered, nodes NOT matching should have class 'dimmed'
        dimmed_count = page.locator(".node.dimmed").count()
        total_nodes = page.locator(".node").count()

        print(f"Total Nodes: {total_nodes}")
        print(f"Dimmed Nodes: {dimmed_count}")

        if dimmed_count > 0:
            print("SUCCESS: Filter applied visually (nodes dimmed).")
        else:
            print(
                "WARNING: No nodes dimmed. Filter might not be working or all nodes match."
            )

        # Test Search
        print("Testing Search...")
        page.fill("#hybridSearchInput", "Förderung")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)  # Wait for results

        results_visible = page.is_visible("#searchResults")
        print(f"Search Results Visible: {results_visible}")
        page.screenshot(path="docs/screenshots/search_test.png")

        browser.close()


if __name__ == "__main__":
    if not os.path.exists("docs/screenshots"):
        os.makedirs("docs/screenshots")
    test_filters()
