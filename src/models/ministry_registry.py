import json
from pathlib import Path
from typing import List, Optional

# Die "Single Source of Truth" für Ministeriums-Identitäten
# Dies erlaubt es, historische Namen (BMWi, BMWE) auf die aktuellen (BMWK) zu mappen.
MINISTRY_REGISTRY = {
    "BMWK": {
        "id": "MIN_ECONOMY",
        "current_name": "Bundesministerium für Wirtschaft und Klimaschutz",
        "aliases": [
            "BMWK",
            "BMWi",
            "BMWE",
            "Wirtschaft und Energie",
            "Wirtschaft und Klimaschutz",
        ],
    },
    "BMBF": {
        "id": "MIN_RESEARCH",
        "current_name": "Bundesministerium für Bildung und Forschung",
        "aliases": ["BMBF", "Bildung und Forschung"],
    },
    "BMFSFJ": {
        "id": "MIN_FAMILY",
        "current_name": "Bundesministerium für Familie, Senioren, Frauen und Jugend",
        "aliases": ["BMFSFJ", "BMBFSFJ", "Familie"],
    },
    "BMF": {
        "id": "MIN_FINANCE",
        "current_name": "Bundesministerium der Finanzen",
        "aliases": ["BMF", "Finanzen"],
    },
    "BMEL": {
        "id": "MIN_AGRICULTURE",
        "current_name": "Bundesministerium für Ernährung und Landwirtschaft",
        "aliases": ["BMEL", "BML", "Ernährung und Landwirtschaft", "BMLEH"],
    },
    "BMUV": {
        "id": "MIN_ENVIRONMENT",
        "current_name": "Bundesministerium für Umwelt, Naturschutz, nukleare Sicherheit und Verbraucherschutz",
        "aliases": ["BMUV", "BMU", "BMUKN", "Umwelt"],
    },
    "BMDV": {
        "id": "MIN_TRANSPORT",
        "current_name": "Bundesministerium für Digitales und Verkehr",
        "aliases": ["BMDV", "BMVI", "BMVBS", "BMFTR", "Verkehr"],
    },
    "BISP": {
        "id": "AGENCY_SPORTS",
        "current_name": "Bundesinstitut für Sportwissenschaft",
        "aliases": ["BISP", "Sportwissenschaft"],
    },
    "BLE": {
        "id": "AGENCY_AGRICULTURE",
        "current_name": "Bundesanstalt für Landwirtschaft und Ernährung",
        "aliases": ["BLE"],
    },
    "BAFA": {
        "id": "AGENCY_ECONOMY",
        "current_name": "Bundesamt für Wirtschaft und Ausfuhrkontrolle",
        "aliases": ["BAFA"],
    },
}


class MinistryRegistry:
    @staticmethod
    def get_canonical_name(name_query: str) -> str:
        """Findet das aktuelle Kürzel für einen beliebigen historischen Namen."""
        query = name_query.upper().strip()
        for key, data in MINISTRY_REGISTRY.items():
            if query in [a.upper() for a in data["aliases"]]:
                return key
        return name_query

    @staticmethod
    def get_full_name(kuerzel: str) -> str:
        return MINISTRY_REGISTRY.get(kuerzel, {}).get("current_name", kuerzel)


if __name__ == "__main__":
    # Test
    print(f"BMWE maps to: {MinistryRegistry.get_canonical_name('BMWE')}")
    print(f"BMWi maps to: {MinistryRegistry.get_canonical_name('BMWi')}")
