import re
from typing import List, Dict, Any


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
            "regex": r"(?:§|Artikel|Art\.)\s*(?P<section>\d+[a-z]*)\s*(?:Abs\.\s*\d+\s*)?(?:Satz\s*\d+\s*)?(?:[a-zA-Z\s\.]*\s+)?(?P<law>BHO|VwVfG|HGB|BGB|GG|AO|UStG|VgV|GWB|InsO|SGB\s*[IVX]+|BRKG|VOB/[AB]|LuftVG|AtG)",
        },
        # 2. Funding Regulations (specific codes)
        # Matches: BNBest-P, ANBest-GK, NKBF 98, BNBest-BMBF
        {
            "type": "regulation",
            # Updated to support "BNBest-mittelbarer Abruf-BMBF" specifically (Longer match first!)
            "regex": r"(?P<regulation>(?:BNBest|ANBest)(?:[\s-]mittelbarer[\s-]Abruf(?:-BMBF)?|-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)|AZA|AZK|NKBF|NABF|BEBF|NKFT)(?:\s+(?P<year>98|20\d{2}))?",
        },
    ]

    NEGATION_PHRASES = [
        "keine anwendung",
        "nicht anwendbar",
        "gilt nicht",
        "findet keine anwendung",
        "abweichend von",
        "ausgeschlossen",
        "nicht maßgebend",
    ]

    def extract(self, text: str) -> List[Dict[str, Any]]:
        citations = []
        text_lower = text.lower()

        # Helper to check for negation
        def is_negated(start, end):
            # Check window of 40 characters after citation
            window_after = text_lower[end : end + 40]
            if any(phrase in window_after for phrase in self.NEGATION_PHRASES):
                return True
            # Check window of 40 characters before citation
            window_before = text_lower[max(0, start - 40) : start]
            if any(phrase in window_before for phrase in self.NEGATION_PHRASES):
                return True
            return False

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
                    "is_excluded": is_negated(match.start(), match.end()),
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
                    "is_excluded": is_negated(match.start(), match.end()),
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
