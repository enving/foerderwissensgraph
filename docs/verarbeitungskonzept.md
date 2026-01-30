# Verarbeitungskonzept & Datenarchitektur

**Stand:** 30.01.2026
**Status:** Living Document

Dieses Dokument beschreibt den Datenfluss im "Bund-ZuwendungsGraph", von der Erhebung (Crawling) über die Speicherung (Knowledge Graph) bis zur Verarbeitung im LLM (IONOS OSS 120B). Besonderes Augenmerk liegt auf der Einhaltung von Kontext-Grenzen (Context Window) und der Transparenz der Datenherkunft.

---

## 1. Datenquellen & Erhebung (Ingestion)

Das System aggregiert Daten aus zwei Hauptquellen-Typen:

### A. Förderrichtlinien (Unstrukturierte Dokumente)
*   **Quelle:** Förderportal des Bundes, Webseiten der Ministerien (BMDV, BMWK, BMBF).
*   **Format:** PDF, DOCX.
*   **Verarbeitung:**
    *   Tool: `Docling` (Microsoft) oder `PyPDF`.
    *   Schritt: Konvertierung in Markdown -> Hierarchisches Chunking (Kapitelweise Zerlegung).
    *   Extraktion: Identifikation von Metadaten (Titel, Fristen) und Zitaten ("Gilt gemäß § 44 BHO").

### B. Rechtsgrundlagen (Strukturierte Daten)
*   **Quelle:** `gesetze-im-internet.de` (Offizielles Kompetenzzentrum des Bundes).
*   **Format:** XML (bevorzugt) oder HTML (Fallback).
*   **Verarbeitung:**
    *   Tool: `LawCrawler` (Eigenentwicklung, Hybrid-Modus).
    *   Schritt: Parsing der XML-Struktur (Normen) oder HTML-TOC (Table of Contents).
    *   Granularität: **Paragraphenscharf**. Jedes Gesetz wird nicht als ein Block, sondern pro Paragraph (`§ 1`, `§ 2`...) als eigener Knoten gespeichert.

---

## 2. Speicherung & Struktur (Persistence)

Die Daten werden **nicht** flüchtig zur Laufzeit geladen, sondern persistent in zwei spezialisierten Datenbanken abgelegt, um Performance und Reproduzierbarkeit zu sichern.

### A. Der Knowledge Graph (`knowledge_graph.json`)
*   **Technologie:** `NetworkX` (JSON-Serialisiert).
*   **Inhalt:** Die logische Struktur.
    *   *Nodes:* Dokumente, Paragraphen (Chunks), Konzepte ("Reisekosten").
    *   *Edges:* `REFERENCES` (Richtlinie -> Gesetz), `SUPERSEDES` (Versionierung), `IMPLIES` (Thematische Verknüpfung).
*   **Zweck:** Ermöglicht "Multi-Hop Reasoning". Wenn eine Richtlinie "BRKG" erwähnt, weiß der Graph sofort, dass das "Bundesreisekostengesetz" gemeint ist.

### B. Der Vektor-Index (`lite_store.json` / `chroma_db`)
*   **Technologie:** `LiteVectorStore` (JSON) oder `ChromaDB`.
*   **Inhalt:** Semantische Repräsentationen (Embeddings) der Text-Chunks.
*   **Modell:** IONOS Embedding API (z.B. `bge-m3` oder `mistral-embed`).
*   **Zweck:** Ermöglicht die inhaltliche Suche ("Was darf ich abrechnen?"), auch wenn keine expliziten Stichworte passen.

---

## 3. Laufzeit & Verarbeitung (Inference)

Hier wird das Risiko des **Context Window Overflow** (zu viele Token für das LLM) mitigiert. Das System nutzt einen strikten **RAG-Ansatz (Retrieval Augmented Generation)**.

### Der Prozess im Detail:

1.  **User Query:** "Darf ich Business Class fliegen?"
2.  **Context Guard (Neu):**
    *   Prüfung: In welcher Richtlinie befinden wir uns? (z.B. mFUND).
    *   Aktion: Erstelle Whitelist der erlaubten Gesetze (z.B. nur `BRKG`, `BHO`). Fremde Regeln (BMBF) werden ausgefiltert.
3.  **Retrieval (Suche):**
    *   Das System sucht **nicht** ganze Gesetze.
    *   Es sucht die **Top-K (z.B. 10) relevantesten Paragraphen** aus dem Vektor-Index.
    *   *Ergebnis:* Nur `§ 4 BRKG` und `VV Nr. 2.3` werden geladen, nicht das ganze Gesetzbuch.
4.  **Graph Expansion (Präzision):**
    *   Falls ein gefundener Paragraph auf einen anderen verweist (z.B. "siehe § 5"), wird dieser *einzelne* Nachbar nachgeladen.
5.  **Prompt Construction:**
    *   Dem LLM (IONOS OSS 120B) wird ein striktes Prompt übergeben:
    *   `"Beantworte die Frage NUR basierend auf folgenden Textauszügen: [Auszug 1], [Auszug 2]..."`
6.  **Antwort:** Das LLM generiert die Antwort aus den ~2.000 Token Kontext, weit unterhalb des Limits.

### Risikobewertung: Context Window

| Risiko | Beschreibung | Mitigation |
| :--- | :--- | :--- |
| **Overflow** | Das Laden ganzer Gesetze (z.B. BGB) sprengt das 4k/8k/32k Limit des Modells. | **Chunking:** Wir speichern und laden nur Paragraphen. **Ranking:** Nur die Top-Resultate werden verwendet. |
| **Halluzination** | Das Modell erfindet Paragraphen oder wendet falsches Recht an. | **Context Guard:** Harte Filterung auf zitierte Gesetze. **Prompting:** Anweisung "Zitiere nur aus dem Kontext". |
| **Veraltete Daten** | Crawler speichert Gesetze lokal, im Web ändern sie sich. | **Versionierung:** Der Crawler muss periodisch laufen (Update-Zyklus). Der Graph unterstützt `SUPERSEDES` Kanten für Versionen. |

---

## 4. Datenschutz & Souveränität

*   **Verarbeitung:** Findet lokal auf dem Server (VPS) statt (Python Logic).
*   **KI-Dienste:**
    *   *Embeddings & Chat:* Laufen über **IONOS Cloud (Deutschland)** oder **Mistral (Europa)**.
    *   *Kein* Datenabfluss an OpenAI/US-Hyperscaler (sofern per Env-Var konfiguriert).
*   **Rechtliche Texte:** Sind Open Data (`gesetze-im-internet.de`). Keine Urheberrechtsprobleme bei Gesetzestexten (§ 5 UrhG).

---

## 5. Ausblick: Modularisierung

Die Komponente `LawCrawler` + `LiteVectorStore` ist so entworfen, dass sie als **eigenständiger Microservice** ("German Law API") ausgekoppelt werden kann. Externe Apps könnten via REST-API gezielt Paragraphen abfragen, ohne den Förder-Kontext zu kennen.
