# GraphRAG Expansion: Context-Aware Compliance Mapping

## 1. Das Konzept
Das Ziel ist ein Paradigmenwechsel von einer "Pull"-Suche (Client sucht nach Begriffen) zu einem "Expand & Map"-Verfahren.
Der **Knowledge Graph (KG)** fungiert als aktiver Compliance-Partner. Er erhält den Kontext (die Förderrichtlinie) und "expandiert" diesen Kontext um alle relevanten, aber nicht explizit genannten Regeln aus seinem Wissensschatz.

## 2. Der Neue Workflow

1.  **Input**: Die FAPS-App sendet die **Förderrichtlinie** (als Text/Chunks) an den Förderwissensgraph.
2.  **Mapping & Expansion**: Der Förderwissensgraph analysiert den Text und identifiziert Konzepte.
3.  **Output**: Der Förderwissensgraph  liefert ein **strukturiertes Regel-Paket** zurück, das spezifisch für *diese* Richtlinie gilt.

## 3. Technische Spezifikation: API Endpoint

### `POST /api/graph/expand-context`

#### Request Body
```json
{
  "context_label": "Guidelines_Drone_2024",
  "text_chunks": [
    "....Text der Förderrichtlinie...",
    "...Zuwendungsempfänger sind KMU..."
  ],
  "metadata": {
    "agency": "BMWK",
    "year": 2024
  }
}
```

#### Graph-Interne Logik (Priorisierung ist entscheidend!)
1.  **Step A: Hard Citation Matching (High Priority)**
    *   Scanne Text nach konkreten Nennungen (z.B. "Es gelten die ANBest-P in der Fassung von 1998", "NKBF 98").
    *   *Aktion*: Suche exakt diesen Knoten (`doc_anbest_p_1998`).
    *   *Regel*: Wenn gefunden, **blockiere** generische Suchen für diesen Bereich (z.B. keine Suche nach ANBest-P 2024, da explizit 1998 gefordert ist).

2.  **Step B: Concept Expansion (Fallback)**
    *   Nur für Bereiche, wo keine explizite Nennung gefunden wurde (z.B. Text erwähnt "Reisekosten", nennt aber kein Gesetz).
    *   *Aktion*: Traversiere vom Konzept-Knoten "Reisekosten" zur *aktuell gültigen* Standard-Regelung (z.B. "BRKG 2025").

3.  **Step C: Implicit Logic (Expertise)**
    *   Folge Kanten wie `IMPLIES`. Beispiel: "Zuwendungsart: Anteilsfinanzierung" -> Impliziert Regel "VV Nr. 2.4 - Eigenmittel vorrangig einsetzen".

#### Beispiel: Versionierung
*   Input Text: *"Es findet die NKBF 98 Anwendung."*
*   Graph Logik: Erkennt "NKBF 98".
*   Resultat: Liefert Knoten `doc_nkbf_98`.
*   *Wichtig*: Der Graph liefert **NICHT** die neuere `NKBF 2017` oder `NABF`, obwohl diese thematisch ähnlich sind. Die explizite Nennung sticht.

#### Response Body (Das "Regel-Paket")
```json
{
  "compliance_context_id": "ctx_12345",
  "mapped_regulations": [
    {
      "category": "Personalkosten",
      "source_doc": "TVöD Entgelttabellen Bund 2024",
      "rules": [
        {
          "rule_id": "rule_tvod_e13",
          "content": "E13 Übertarifliche Bezahlung nur mit Begründung zulässig (Besserstellungsverbot).",
          "relevance_reason": "Richtlinie erwähnt 'TVöD-Anlehnung'."
        }
      ]
    },
    {
      "category": "Reisekosten",
      "source_doc": "Bundesreisekostengesetz (BRKG)",
      "rules": [
        {
          "rule_id": "rule_brkg_hotel",
          "content": "Maximale Hotelkosten: 80 EUR/Nacht ohne Begründung.",
          "relevance_reason": "Implizit relevant für alle Bundeszuwendungen."
        }
      ]
    }
  ]
}
```

## 4. Nutzung in den Prüfagenten

Die Prüfagenten (z.B. `KaufmaennischePruefung`) müssen nicht mehr raten. Sie erhalten das `mapped_regulations` Paket.

**Beispiel Prompt für den Agenten:**
> "Prüfe die Reisekosten im Finanzplan.
> Nutze dafür NICHT dein allgemeines Wissen, sondern EXPLIZIT folgende Regeln aus dem Graph-Paket:
> - Regel 'rule_brkg_hotel': Max 80 EUR/Nacht.
>
> Ist der Satz von 120 EUR im Antrag gerechtfertigt?"

## 5. Vorteile der Expansion
*   **Implizites Wissen**: Der Graph weiß, dass "Bundesmittel" immer das "Besserstellungsverbot" implizieren, auch wenn es in der Richtlinie nicht steht.
*   **Aktualität**: Der Graph liefert immer die *jetzt* gültigen Tabellen (TVöD 2024 vs 2025).
*   **Präzision**: Der Agent prüft genau gegen die Vorschriften, die für diesen spezifischen Fördertopf gelten.
