import re
from typing import List, Dict


class CitationExtractor:
    """
    Extracts citations from text for the Graph Density Phase.
    Targets:
    - Laws (BHO, VwVfG, etc.)
    - Funding Regulations (BNBest, ANBest, AZA, AZK)
    """

    PATTERNS = [
        # 1. Standard Laws (with Paragraph)
        # Matches: § 44 BHO, § 23 BHO, Art. 3 GG
        # We explicitly list common federal laws to avoid false positives
        {
            "type": "law",
            "regex": r"(?:§|Artikel|Art\.)\s*(?P<section>\d+[a-z]*)\s*(?:Abs\.\s*\d+\s*)?(?:Satz\s*\d+\s*)?(?:[a-zA-Z\s\.]*\s+)?(?P<law>BHO|VwVfG|HGB|BGB|GG|AO|UStG|VgV|GWB)",
        },
        # 2. Funding Regulations (specific codes)
        # Matches: BNBest-P, ANBest-GK, NKBF 98, BNBest-BMBF
        {
            "type": "regulation",
            "regex": r"(?P<regulation>BNBest-[A-Z0-9a-z\-]+|ANBest-[A-Z0-9a-z\-]+|AZA|AZK|NKBF|NABF|BEBF|NKFT)(?:\s+(?P<year>98|20\d{2}))?",
        },
    ]

    def extract(self, text: str) -> List[Dict[str, str]]:
        citations = []

        # 1. Laws
        for match in re.finditer(self.PATTERNS[0]["regex"], text):
            citations.append(
                {
                    "type": "law",
                    "target": match.group("law"),
                    "section": match.group("section"),
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # 2. Regulations
        for match in re.finditer(self.PATTERNS[1]["regex"], text):
            target = match.group("regulation")
            if match.group("year"):
                target += " " + match.group("year")

            citations.append(
                {
                    "type": "regulation",
                    "target": target,
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        return citations


if __name__ == "__main__":
    extractor = CitationExtractor()
    examples = [
        "Das Verfahren richtet sich nach § 44 BHO und den dazu ergangenen Verwaltungsvorschriften.",
        "Es gelten die Nebenbestimmungen der BNBest-P sowie die ANBest-GK.",
        "Gemäß Artikel 104b GG ist der Bund zuständig.",
        "Siehe Nummer 5.1 der NKBF 98.",
    ]

    print("--- Citation Extractor Prototype ---")
    for text in examples:
        print(f"\nText: {text}")
        results = extractor.extract(text)
        for r in results:
            print(f"  Found: {r['type'].upper()} -> {r['target']} (in '{r['text']}')")
