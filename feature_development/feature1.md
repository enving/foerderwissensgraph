# Feature 1: Erweiterung der UI zum Graph-RAG Chat mit Upload-Funktion

## 🎯 Zusammenfassung
Das bestehende Dashboard (D3.js Graph-Visualisierung + einfache Suche) soll zu einem **interaktiven KI-Assistenten** ausgebaut werden. Anstatt einer reinen Suchleiste wird ein **Chat-Interface** implementiert, das zusätzlich einen **Dokumenten-Upload** unterstützt.

## 🌟 Neue Funktionen

### 1. Chat-Interface (Conversational Search)
*   **Status Quo**: Einfaches Suchfeld -> Liste von Ergebnissen.
*   **Neu**: Ein persistenter Chat-Verlauf (ähnlich ChatGPT/Claude/Gemini).
*   **Funktionalität**:
    *   Nutzer können Fragen in natürlicher Sprache stellen (z.B. "Welche Fristen gelten für die Zuwendung X?").
    *   Der Bot antwortet basierend auf dem Knowledge Graph und zeigt Quellen an.
    *   Follow-up Fragen sind möglich (Kontext-Erhaltung im Chat).

### 2. "Chat with your Policy" (Dokumenten-Upload)
*   **Feature**: Drag & Drop Zone oder "Büroklammer"-Icon im Chat-Fenster.
*   **Use Case**: Ein Nutzer hat eine *neue* oder *spezifische* Förderrichtlinie als PDF, die noch nicht im Graphen ist (oder er will sie explizit prüfen).
*   **Ablauf**:
    1.  Nutzer lädt PDF hoch (z.B. "Richtlinie_2026_Entwurf.pdf").
    2.  **On-the-fly Parsing**: Das System parst die PDF im Hintergrund (via Docling).
    3.  **Ad-hoc RAG**: Das Dokument wird temporär in den Kontext geladen.
    4.  **Graph-Verknüpfung**: Das System prüft, ob das Dokument Referenzen auf den bestehenden Knowledge Graph enthält (z.B. Verweis auf BNBest oder BHO).
    5.  **Antwort**: Der Nutzer kann nun Fragen *spezifisch zu diesem Dokument* stellen, wobei der Bot Hintergrundwissen aus dem Graphen hinzuzieht (z.B. "Wie verhält sich § 4 dieser Richtlinie zur allgemeinen Verwaltungsvorschrift?").

### 3. Visuelle Integration
*   Der Knowledge Graph (D3.js) bleibt sichtbar, agiert aber nun dynamisch:
    *   Wenn der Chat über bestimmte Knoten spricht, werden diese im Graphen **hervorgehoben** (Highlighting).
    *   Ein Klick auf einen Knoten im Graphen kann diesen als Kontext in den Chat senden.

## 🛠️ Technische Umsetzung (Backend & Frontend)

### Frontend (Vue.js / Vanilla JS Update)
*   **Chat Komponente**:
    *   Message Bubble Design (User vs. System).
    *   Markdown-Rendering für Antworten.
    *   Citation-Links: Klick auf [1] öffnet die Quelle in der Sidebar.
*   **Upload Komponente**:
    *   Progress Bar beim Parsen.
    *   Anzeige des aktiven Dokuments im Chat-Header.

### Backend (FastAPI)
*   **Neuer Endpoint**: `POST /api/chat/upload`
    *   Nimmt PDF entgegen.
    *   Parst Inhalt -> Chunks.
    *   Gibt Session-ID zurück.
*   **Update Endpoint**: `POST /api/chat/query`
    *   Parameter: `message`, `history`, `uploaded_document_id`.
    *   Logik:
        *   Suche im Graphen (bestehende Logik).
        *   Zusätzlich: Suche im hochgeladenen Dokument.
        *   Kombination der Kontexte (Graph-Wissen + PDF-Inhalt).
        *   LLM-Prompting mit kombiniertem Kontext.

## 📝 User Flow Beispiel
1.  **Nutzer** öffnet `foerderwissensgraph.digitalalchemisten.de`.
2.  **UI** zeigt den Graphen im Hintergrund und ein Chat-Fenster rechts (oder als Overlay).
3.  **Nutzer** sieht Hinweis: *"Lade eine Förderrichtlinie hoch oder stelle eine Frage zum Bestand."*
4.  **Nutzer** zieht eine PDF in den Chat.
5.  **System**: *"Analysiere Richtlinie... Erledigt. Ich habe 3 Verweise auf die BNBest gefunden."*
6.  **Nutzer**: *"Welche Reisekosten sind hiernach erstattungsfähig?"*
7.  **System**: *"Laut Ihrer hochgeladenen Richtlinie (Abschnitt 4.2) gilt das Bundesreisekostengesetz. Im Kontext des Graphen bedeutet das: Pauschalen nach § x BRKG..."*

---
*Status: Geplant für v2.3*
