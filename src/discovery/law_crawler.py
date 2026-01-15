import requests
import zipfile
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any


class LawCrawler:
    """
    Crawls and parses German federal laws from gesetze-im-internet.de
    """

    BASE_URL = "https://www.gesetze-im-internet.de/{abbr}/xml.zip"

    def fetch_law(self, abbr: str) -> str:
        url = self.BASE_URL.format(abbr=abbr.lower())
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch law {abbr} from {url}")

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            xml_filename = [name for name in z.namelist() if name.endswith(".xml")][0]
            with z.open(xml_filename) as f:
                return f.read().decode("utf-8")

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
