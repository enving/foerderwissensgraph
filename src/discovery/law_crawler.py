import requests
import zipfile
import io
import xml.etree.ElementTree as ET
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from src.config_loader import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LawCrawler:
    """
    Crawls and parses German federal laws from gesetze-im-internet.de
    Supports both XML (bulk) and HTML (targeted) parsing.
    """

    def fetch_law_xml(self, abbr: str, retries: int = 3) -> Optional[str]:
        """Fetch full XML zip for a law."""
        base_url = settings.get(
            "crawlers.laws.base_url",
            "https://www.gesetze-im-internet.de/{abbr}/xml.zip",
        )
        url = base_url.format(abbr=abbr.lower())

        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        xml_filename = [
                            name for name in z.namelist() if name.endswith(".xml")
                        ][0]
                        with z.open(xml_filename) as f:
                            return f.read().decode("utf-8")
                elif response.status_code == 404:
                    logger.warning(f"XML not found for {abbr} (404).")
                    return None
                else:
                    logger.warning(
                        f"Attempt {attempt + 1}: Received status {response.status_code}"
                    )
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error fetching {abbr}: {e}")

            if attempt < retries - 1:
                time.sleep(2**attempt)

        return None

    def fetch_law_html_toc(self, abbr: str) -> List[str]:
        """
        Fetches the Table of Contents (TOC) HTML page to find sub-links.
        Returns a list of URLs to individual sections (paragraphs).
        Example: https://www.gesetze-im-internet.de/vob_a/index.html
        """
        url = f"https://www.gesetze-im-internet.de/{abbr.lower()}/index.html"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"HTML TOC not found for {abbr}: {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, "html.parser")
            links = []
            # The structure usually has links in a table or list
            # We look for links that look like relative paths to sections
            # e.g. "__1.html" or "BJNR...html"

            # Base path for relative links
            base_path = url.rsplit("/", 1)[0]

            for a in soup.find_all("a", href=True):
                href = str(a["href"])
                # Filter logic: only content links, avoid 'index.html' self-ref
                # Also ignore "aktuell.html", "gliederung.html", "aktuDienst.html", "impressum.html"
                ignore_list = [
                    "index.html",
                    "gliederung",
                    "aktuell",
                    "aktuDienst",
                    "impressum",
                    "datenschutz",
                    "suche",
                    "Teilliste",
                    "service",
                ]
                if href.endswith(".html") and not any(
                    ign in href for ign in ignore_list
                ):
                    # Resolve relative path properly
                    if href.startswith(".."):
                        # Ignore links going up (usually to other laws or meta pages)
                        continue

                    full_link = f"{base_path}/{href}"
                    links.append(full_link)

            # Remove duplicates while preserving order
            return list(dict.fromkeys(links))

        except Exception as e:
            logger.error(f"Error fetching TOC for {abbr}: {e}")
            return []

    def parse_law_html_section(self, url: str) -> Optional[Dict[str, Any]]:
        """Parses a single section HTML page."""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, "html.parser")

            # Heuristic extraction for gesetze-im-internet.de structure
            # Title is usually in h1 or specialized divs

            # Try to find paragraph number (Enbez) and Title (Titel)
            norm_id = ""
            title = ""

            # Common structure:
            # <div class="jnheader"> ... <h1> ... </h1> </div>
            header = soup.find("div", {"class": "jnheader"})
            if header:
                h1 = header.find("h1")
                if h1:
                    full_title = h1.get_text(strip=True)
                    # Split into ID and Text if possible
                    # E.g. "§ 1 Grundsätze" -> ID="§ 1", Title="Grundsätze"
                    parts = full_title.split(" ", 2)
                    if len(parts) > 1 and (
                        parts[0].startswith("§") or parts[0] == "Art"
                    ):
                        norm_id = f"{parts[0]} {parts[1]}"
                        title = parts[2] if len(parts) > 2 else ""
                    else:
                        norm_id = full_title

            # Content
            # <div class="jurAbsatz">...</div>
            content_divs = soup.find_all("div", {"class": "jurAbsatz"})
            content_text = "\n".join([d.get_text(strip=True) for d in content_divs])

            if not content_text:
                return None

            return {
                "paragraph": norm_id,
                "title": title,
                "content": content_text,
                "source_url": url,
            }

        except Exception as e:
            logger.error(f"Error parsing section {url}: {e}")
            return None

    def crawl_law_hybrid(self, abbr: str) -> List[Dict[str, Any]]:
        """
        Main entry point. Tries XML first, falls back to HTML crawling.
        """
        # 1. Try XML
        logger.info(f"Trying XML download for {abbr}...")
        xml_content = self.fetch_law_xml(abbr)
        if xml_content:
            logger.info(f"XML found for {abbr}. Parsing...")
            return self.parse_law_xml(xml_content)

        # 2. Fallback HTML
        logger.info(f"XML failed. Trying HTML crawl for {abbr}...")
        toc_links = self.fetch_law_html_toc(abbr)

        if not toc_links:
            raise Exception(f"Could not find law {abbr} via XML or HTML.")

        logger.info(f"Found {len(toc_links)} sections in HTML TOC. Crawling...")
        norms = []
        for i, link in enumerate(toc_links):
            # Gentle crawling
            if i > 0 and i % 10 == 0:
                time.sleep(1)

            norm = self.parse_law_html_section(link)
            if norm:
                norms.append(norm)

        return norms

    def parse_law_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        root = ET.fromstring(xml_content.encode("utf-8"))
        norms = []

        for norm in root.findall(".//norm"):
            metadaten = norm.find("metadaten")
            textdaten = norm.find("textdaten")

            title = ""
            norm_id = ""
            if metadaten is not None:
                titel_node = metadaten.find("titel")
                title = titel_node.text if titel_node is not None else ""

                enbez_node = metadaten.find("enbez")
                norm_id = enbez_node.text if enbez_node is not None else ""

            text_content = ""
            if textdaten is not None:
                text_node = textdaten.find("text")
                if text_node is not None:
                    text_content = "".join(text_node.itertext()).strip()

            if text_content:
                norms.append(
                    {"paragraph": norm_id, "title": title, "content": text_content}
                )

        return norms


if __name__ == "__main__":
    crawler = LawCrawler()
    try:
        # Test HTML Fallback with BHO (by asking for non-existent XML, or just testing the HTML method directly)
        print("Testing HTML Parser with BHO...")
        links = crawler.fetch_law_html_toc("bho")
        print(f"Found {len(links)} links in TOC.")
        if links:
            print(f"First link: {links[0]}")
            section = crawler.parse_law_html_section(links[0])
            print(f"Parsed Section: {section}")

    except Exception as e:
        print(f"Error: {e}")
