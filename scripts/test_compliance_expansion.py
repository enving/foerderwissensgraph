import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.search_api import app
from src.models.schemas import ExpandContextRequest

client = TestClient(app)

def test_expand_context_endpoint_structure():
    """
    Verifies that the endpoint exists and accepts the correct schema.
    """
    print("Testing /graph/expand-context endpoint...")
    payload = {
        "context_label": "Drone Guidelines 2024",
        "text_chunks": [
            "Es findet die NKBF 98 Anwendung.",
            "Zuwendungen werden nur an KMU gewährt.",
            "Für die Reisekosten gilt das Gesetz.",
            "Das Verfahren richtet sich nach BHO."
        ],
        "metadata": {"agency": "BMWK"}
    }
    
    response = client.post("/graph/expand-context", json=payload)
    
    if response.status_code != 200:
        print(f"FAILED: Status code {response.status_code}")
        print(response.json())
        return

    data = response.json()
    print(f"Response received. Mapped Regulations: {len(data['mapped_regulations'])}")
    for reg in data['mapped_regulations']:
        print(f"  - Source: {reg['source_doc']} ({len(reg['rules'])} rules)")
    
    if "compliance_context_id" not in data:
        print("FAILED: Missing compliance_context_id")
        return
        
    if "mapped_regulations" not in data:
        print("FAILED: Missing mapped_regulations")
        return
        
    print("SUCCESS: Endpoint structure verification passed.")

if __name__ == "__main__":
    test_expand_context_endpoint_structure()
