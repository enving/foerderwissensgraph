import requests
import zipfile
import io
import xml.etree.ElementTree as ET
import time
from pathlib import Path
from typing import List, Dict, Any
from src.config_loader import settings


class LawCrawler:
    """
    Crawls and parses German federal laws from gesetze-im-internet.de
    """

    def fetch_law(self, abbr: str, retries: int = 3) -> str:
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
                else:
                    print(
                        f"Attempt {attempt + 1}: Received status {response.status_code}"
                    )
            except Exception as e:
                print(f"Attempt {attempt + 1}: Error fetching {abbr}: {e}")

            if attempt < retries - 1:
                time.sleep(2**attempt)

        raise Exception(f"Failed to fetch law {abbr} after {retries} attempts.")

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
        print("Fetching BHO (Bundeshaushaltsordnung)...")
        xml = crawler.fetch_law("bho")
        norms = crawler.parse_law_xml(xml)

        print(f"Successfully parsed {len(norms)} sections from BHO.")
        for n in norms:
            if "44" in n["paragraph"]:
                print(f"\nFound: {n['paragraph']} {n['title']}")
                print(f"Content: {n['content'][:200]}...")
                break

    except Exception as e:
        print(f"Error: {e}")
