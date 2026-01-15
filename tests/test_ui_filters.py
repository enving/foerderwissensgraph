from playwright.sync_api import sync_playwright
import time
import os


def test_filters():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto("http://localhost:8000/docs/dashboard.html", timeout=5000)
        except:
            dashboard_path = os.path.abspath("docs/dashboard.html")
            page.goto(f"file://{dashboard_path}")

        page.wait_for_load_state("networkidle")
        print(f"Page title: {page.title()}")

        options = page.eval_on_selector_all(
            "#filterMinistry option", "opts => opts.map(o => o.value)"
        )
        target_min = next((o for o in options if o and o != "Alle Ressorts"), "BMWK")
        print(f"Selecting Ministry: {target_min}")
        page.select_option("#filterMinistry", target_min)
        page.wait_for_timeout(500)

        type_options = page.eval_on_selector_all(
            "#filterType option", "opts => opts.map(o => o.value)"
        )
        target_type = next(
            (o for o in type_options if o and o != "Alle Typen"), "Merkblatt"
        )
        print(f"Selecting Type: {target_type}")
        page.select_option("#filterType", target_type)
        page.wait_for_timeout(500)

        dimmed_count = page.locator(".node.dimmed").count()
        total_nodes = page.locator(".node").count()
        print(f"Nodes: {total_nodes}, Dimmed: {dimmed_count}")

        print("Testing Hybrid Search with filters...")
        page.fill("#hybridSearchInput", "ANBest")
        page.keyboard.press("Enter")
        page.wait_for_selector("#resultsList", timeout=10000)

        results_count = page.locator("#resultsList > div").count()
        print(f"Search Results: {results_count}")

        page.screenshot(path="docs/screenshots/intensive_ui_test.png")
        browser.close()
        assert total_nodes > 0


if __name__ == "__main__":
    if not os.path.exists("docs/screenshots"):
        os.makedirs("docs/screenshots")
    test_filters()
