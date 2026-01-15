import asyncio
import os
import hashlib
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


class EasyCrawler:
    """
    Systematischer Crawler für den Bundes-Formularschrank (Easy-Online).
    Unterstützt Kategorien-Scanning, Download und Hashing.
    """

    BASE_URL = "https://foerderportal.bund.de/easy/"
    START_PAGE = "easy_index.php?auswahl=formularschrank_foerderportal&formularschrank="

    CATEGORIES = {
        "t1": "AZA (Ausgabenbasis)",
        "t2": "AZK (Kostenbasis)",
        "t3": "AAA (Aufträge Ausgaben)",
        "t4": "AAK (Aufträge Kosten)",
        "t5": "AZV (Zuweisungen/AZV)",
        "t6": "Allgemein",
        "t7": "Altvorhaben",
    }

    def __init__(
        self, output_dir: Path, ministerium: str = "bmwe", limit_per_cat: int = None
    ):
        self.output_dir = output_dir
        self.raw_dir = output_dir / "raw" / ministerium
        self.ministerium = ministerium
        self.manifest_path = self.raw_dir / "manifest.json"
        self.limit_per_cat = limit_per_cat

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        if self.manifest_path.exists():
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except:
                    pass
        return {"ministerium": self.ministerium, "last_crawl": None, "files": {}}

    def _save_manifest(self):
        self.manifest["last_crawl"] = datetime.now().isoformat()
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)

    def _calculate_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def run(self):
        async with async_playwright() as p:
            print(f"🚀 Starte Crawler für Ministerium: {self.ministerium}")
            browser = await p.chromium.launch(headless=True)
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            context = await browser.new_context(user_agent=user_agent)
            page = await context.new_page()

            url = f"{self.BASE_URL}{self.START_PAGE}{self.ministerium}"

            for cat_id, cat_name in self.CATEGORIES.items():
                print(f"\n📂 Scanne Kategorie: {cat_name}...")

                try:
                    await page.goto(url, wait_until="load")

                    # BMBF Specific Check
                    if "bmbf" not in self.ministerium.lower():
                        await page.evaluate(f"easy_tabelle('{cat_id}', 7)")
                        await page.wait_for_timeout(5000)
                    else:
                        print(
                            "   ℹ️ BMBF-Modus: Überspringe JS-Toggle (Tabelle bereits offen)"
                        )

                    rows = await page.query_selector_all(f"#{cat_id} tr")
                    print(f"   📊 {len(rows)} Zeilen gefunden.")

                    cookies = await context.cookies()
                    session_cookies = {c["name"]: c["value"] for c in cookies}

                    target_rows = (
                        rows
                        if self.limit_per_cat is None
                        else rows[: self.limit_per_cat + 1]
                    )

                    for i, row in enumerate(target_rows):
                        cells = await row.query_selector_all("td")
                        if len(cells) >= 3:
                            nr = (await cells[0].inner_text()).strip()
                            if not nr:
                                continue

                            title = (await cells[1].inner_text()).strip()
                            file_link = await cells[2].query_selector("a")

                            if file_link:
                                filename = (await file_link.inner_text()).strip()
                                href = await file_link.get_attribute("href")
                                full_url = (
                                    href
                                    if href.startswith("http")
                                    else f"{self.BASE_URL}{href}"
                                )

                                await self._download_file_requests(
                                    full_url,
                                    nr,
                                    title,
                                    filename,
                                    cat_name,
                                    session_cookies,
                                )
                except Exception as e:
                    print(f"   ❌ Fehler in Kategorie {cat_name}: {e}")

            self._save_manifest()
            await browser.close()
            print(
                f"\n✅ Crawl abgeschlossen. Manifest gespeichert in {self.manifest_path}"
            )

    async def _download_file_requests(
        self, url, nr, title, filename, category, cookies
    ):
        import requests

        cat_dir = self.raw_dir / category.split(" ")[0]
        cat_dir.mkdir(exist_ok=True)
        file_path = cat_dir / filename

        if nr in self.manifest["files"] and file_path.exists():
            print(f"   ⏭️  Überspringe: [{nr}] {title[:50]} (existiert bereits)")
            return

        print(f"   📥 Downloade: [{nr}] {title[:50]}...")

        try:

            def do_download():
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://foerderportal.bund.de/easy/easy_index.php",
                }
                response = requests.get(
                    url, cookies=cookies, headers=headers, timeout=30
                )
                response.raise_for_status()
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return True

            success = await asyncio.to_thread(do_download)
            if success:
                file_hash = self._calculate_hash(file_path)
                self.manifest["files"][nr] = {
                    "nr": nr,
                    "title": title,
                    "filename": filename,
                    "category": category,
                    "url": url,
                    "hash": file_hash,
                    "last_seen": datetime.now().isoformat(),
                }
                print(f"      ✅ Erfolgreich: {filename} ({file_hash[:8]})")
        except Exception as e:
            print(f"      ❌ Download fehlgeschlagen: {e}")


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Easy-Online Crawler")
    parser.add_argument(
        "limit", nargs="?", type=int, default=None, help="Limit files per category"
    )
    parser.add_argument(
        "--ministry",
        type=str,
        default="bmwe",
        help="Target Ministry (e.g., bmwe, bmbf)",
    )

    args = parser.parse_args()

    output = Path("/home/enving/Dev/Bund-ZuwendungsGraph/data")
    crawler = EasyCrawler(output, ministerium=args.ministry, limit_per_cat=args.limit)
    asyncio.run(crawler.run())
