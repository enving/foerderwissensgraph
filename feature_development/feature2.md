# Feature: Server-Side Deduplication & Score Aggregation (v2.3.1)

**Implementiert am:** 27.01.2026
**Datei:** `src/graph/compliance_mapper.py`

## Hintergrund
Der Endpoint `/api/graph/expand-context` lieferte bisher redundante Ergebnisse, wenn mehrere Text-Chunks ähnliche Konzepte oder Zitationen enthielten. Dies erzwang eine client-seitige Deduplizierung.

## Implementierung

Die Logik wurde um eine zentrale **Aggregation Registry** erweitert, bevor die Ergebnisse finalisiert werden.

### Mechanismen

1.  **Global Aggregation**
    *   Alle Chunks werden nacheinander verarbeitet.
    *   Treffer werden nicht sofort in die Ergebnisliste geschrieben, sondern in einem Dictionary (`aggregated_regs`) gesammelt, geschlüsselt nach Dokumententitel.

2.  **Hit Counting & Score Boosting**
    *   Jedes Mal, wenn ein Dokument in einem Chunk gefunden wird (sei es explizit oder implizit), wird ein Zähler (`hit_count`) erhöht.
    *   Die Indizes der Chunks werden gespeichert (`found_in_chunks`).
    *   **Output:** Wenn ein Dokument in mehr als einem Chunk gefunden wurde, wird der `relevance_reason` der Regeln um den Suffix `(Gefunden in X Textsegmenten)` erweitert. Dies dient als Indikator für hohe Relevanz.

3.  **Priorisierung**
    *   **Explizit > Implizit:** Wenn ein Dokument in Chunk A implizit (über Keyword) und in Chunk B explizit (über Zitation) gefunden wird, gewinnt die Kategorie "Explizite Bestimmungen".

## Code-Beispiel (Logik)

```python
# Pseudo-Code der Aggregation
if doc_title not in aggregated_regs:
    aggregated_regs[doc_title] = {
        "hit_count": 0,
        "priority": 1, # 1=Implicit, 10=Explicit
        ...
    }

entry["hit_count"] += 1

# Update Priority if better match found later
if category == "Explizit":
    entry["priority"] = 10
```

## Vorteil
- **Payload-Reduktion:** Keine doppelten Regelwerke mehr im JSON-Response.
- **Bessere Signale:** Der Client erkennt sofort, welche Regelwerke den gesamten Kontext (mehrere Chunks) betreffen.
- **Einfachere Integration:** Client muss keine Hashes mehr bilden oder filtern.
