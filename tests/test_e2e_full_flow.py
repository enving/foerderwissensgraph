from playwright.sync_api import sync_playwright, expect


def test_full_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Listen to console
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))

        # 1. Navigate to dashboard
        print("Navigating to dashboard...")
        page.goto("http://localhost:8000/docs/dashboard.html")

        # Check title
        expect(page).to_have_title("Bund-ZuwendungsGraph | Interactive Dashboard")

        # 2. Perform a search
        print("Performing search...")
        search_input = page.locator("#hybridSearchInput")
        search_input.fill("Wie ist die Verwendungsprüfung nach § 44 BHO geregelt?")
        search_input.press("Enter")

        # 3. Wait for results
        print("Waiting for results...")
        results_list = page.locator("#resultsList")
        page.wait_for_selector("#resultsList .group", timeout=45000)

        # 4. Verify AI Answer if present
        print("Verifying results...")
        answer_engine = page.locator("#resultsList .bg-federal-900")
        # Answer might take some time or not appear for all queries, but for this complex one it should
        if answer_engine.is_visible(timeout=5000):
            print("✅ AI Answer found")
            expect(answer_engine).to_contain_text("Answer Engine")

        # 5. Verify Graph Context (Multi-Hop)
        result_with_context = (
            page.locator("details").filter(has_text="Graph-Kontext").first
        )
        expect(result_with_context).to_be_visible()
        print("✅ Graph Context (Multi-Hop) found")

        # Expand and check content
        result_with_context.click()
        expect(result_with_context.locator(".line-clamp-2").first).to_be_visible()
        print("✅ Neighbor context content verified")

        # 6. Verify Node Selection
        first_result = page.locator("#resultsList .group").first
        first_result.click()

        # Sidebar should update
        doc_title = page.locator("#docTitle")
        expect(doc_title).not_to_have_text("Wählen Sie ein Dokument aus")
        print(f"✅ Selected node: {doc_title.inner_text()}")

        browser.close()


if __name__ == "__main__":
    test_full_flow()
