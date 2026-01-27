import sys
from pathlib import Path
import json

# Setup path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.search_api import app

client = TestClient(app)

def run_compliance_check_example():
    """
    Simulates a 'Compliance Prüfagent' (Checking Agent) using the Context Expansion API.
    """
    print("=== Compliance Prüfagent Simulation ===")
    
    # 1. Provide the context (New Guideline)
    print("\n[Step 1] Loading new guideline context...")
    guideline_text = [
        "Förderrichtlinie für KI-Forschung 2026.",
        "Es finden die NKBF 98 Anwendung.",
        "Das Verfahren richtet sich nach dem Haushaltsrecht (BHO).",
        "Förderfähig sind KMU mit Sitz in Deutschland."
    ]
    
    # 2. Expand Context via API
    print("[Step 2] Requesting GraphRAG Expansion...")
    payload = {
        "context_label": "KI_Forschung_2026",
        "text_chunks": guideline_text
    }
    
    response = client.post("/graph/expand-context", json=payload)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    expansion_data = response.json()
    mapped_regs = expansion_data["mapped_regulations"]
    
    print(f"Success! Found {len(mapped_regs)} relevant regulation sets from the Knowledge Graph.")
    for reg in mapped_regs:
        print(f"  - {reg['category']}: {reg['source_doc']} ({len(reg['rules'])} rules)")

    # 3. Simulate the Check (The Agent's Job)
    print("\n[Step 3] Performing Compliance Check on a specific claim...")
    
    # Claim to check
    claim = "Wir vergeben den Auftrag direkt ohne Ausschreibung."
    
    # Find relevant rules from the expanded context
    relevant_rules = []
    for reg in mapped_regs:
        for rule in reg["rules"]:
            # Simple keyword matching for this demo
            if any(kw in rule["content"].lower() for kw in ["vergabe", "haushalt", "bho", "ausschreibung"]):
                relevant_rules.append(rule)
    
    print(f"Processing claim: '{claim}'")
    
    # Simple logic for the 'Prüfagent'
    # In a real scenario, this would evaluate the BHO rules against the claim.
    if any("bho" in reg["source_doc"].lower() for reg in mapped_regs):
        print("RESULT: ⚠️ WARNING / NON-COMPLIANT")
        print("REASON: The Knowledge Graph expanded the context to include BHO. BHO § 55 generally requires public tender (Ausschreibung).")
    else:
        print("RESULT: ✅ POTENTIALLY COMPLIANT (BHO not found in context)")

    print("\n=== Simulation Complete ===")

if __name__ == "__main__":
    run_compliance_check_example()
