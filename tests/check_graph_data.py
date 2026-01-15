import asyncio
from playwright.async_api import async_playwright
import json


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://localhost:8000/docs/dashboard.html")
        await asyncio.sleep(2)

        graph_data = await page.evaluate("graphData")
        print(f"Total Nodes: {len(graph_data['nodes'])}")

        node_types = {}
        for node in graph_data["nodes"]:
            t = node.get("type", "unknown")
            node_types[t] = node_types.get(t, 0) + 1
        print(f"Node Types: {node_types}")

        link_relations = {}
        for link in graph_data["links"]:
            r = link.get("relation", "unknown")
            link_relations[r] = link_relations.get(r, 0) + 1
        print(f"Link Relations: {link_relations}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
