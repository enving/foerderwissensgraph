# Checkpoint: Bund-ZuwendungsGraph Deployment
**Datum:** 2026-01-27 17:21 Uhr
**Version:** v2.3.0

---

## ✅ Abgeschlossene Aufgaben

### 1. GraphRAG Expansion Endpoint implementiert
- **Neuer Endpoint:** `POST /api/graph/expand-context`
- **Funktion:** Nimmt Text-Chunks entgegen, extrahiert Zitationen, mappt auf Knowledge Graph
- **Schema:** `ExpandContextRequest` / `ExpandContextResponse` in `src/models/schemas.py`
- **Logik:** `src/graph/compliance_mapper.py`
  - Hard Citation Matching (explizite Referenzen wie "NKBF 98")
  - Implicit Expansion (Keywords wie "Reisekosten" → Bundesreisekostengesetz)
  - Version Family Handling (neueste Version bei impliziten Matches)

### 2. Deployment auf VPS repariert
- **Problem:** GitHub Actions Pipeline baute Image, aber VPS zog es nicht
- **Lösung:** 
  - Manueller SSH-Zugriff via `~/.ssh/id_ed25519` (nicht `ssl/private.key`)
  - Docker Compose auf VPS aktualisiert mit `ghcr.io/enving/foerderwissensgraph:latest`
  - Nginx SSL-Konfiguration korrigiert

### 3. Nginx-Konfiguration optimiert
- **Datei:** `nginx_ssl-vps-v2.3.2.conf` (deployed als `nginx_ssl.conf` auf VPS)
- **Routing:**
  - `/api/` (exact) → API-Info JSON
  - `/api/*` → Backend (strips prefix)
  - `/data/*` → Static data files
  - `/` → Dashboard

### 4. Static File Serving repariert
- `/data/d3_graph_documents.json` und `/data/knowledge_graph.json` sind jetzt erreichbar
- FastAPI StaticFiles Mount mit absoluten Pfaden

---

## 🌐 Live-Endpunkte

| URL | Funktion | Status |
|-----|----------|--------|
| `https://foerderwissensgraph.digitalalchemisten.de/` | Dashboard | ✅ |
| `https://foerderwissensgraph.digitalalchemisten.de/api/` | API Info | ✅ |
| `https://foerderwissensgraph.digitalalchemisten.de/api/docs` | Swagger UI | ✅ |
| `https://foerderwissensgraph.digitalalchemisten.de/api/health` | Health Check | ✅ |
| `https://foerderwissensgraph.digitalalchemisten.de/api/search?q=...` | Hybrid Search | ✅ |
| `https://foerderwissensgraph.digitalalchemisten.de/api/graph/expand-context` | GraphRAG Expansion | ✅ |
| `https://foerderwissensgraph.digitalalchemisten.de/data/knowledge_graph.json` | Graph Data | ✅ |

---

## 📁 Wichtige Dateien (geändert/erstellt)

```
src/
├── api/search_api.py          # v2.3.0, expand-context endpoint
├── graph/compliance_mapper.py # GraphRAG Expansion Logik
├── models/schemas.py          # Pydantic Models für Expansion
├── parser/citation_extractor.py # Zitationen aus Text extrahieren

docs/
├── dashboard.html             # fetch-Pfade korrigiert

config/
├── nginx/nginx_ssl.conf       # Lokale Referenz

# VPS-spezifische Configs (nicht im Git)
nginx_ssl-vps-v2.3.2.conf      # Deployed auf VPS
docker-compose-vps.yml         # Deployed auf VPS
```

---

## 🔧 VPS-Zugriff

```bash
# SSH-Verbindung (funktioniert mit Default-Key)
ssh graph@217.154.164.31

# Docker-Status prüfen
cd /home/graph/bund-zuwendungsgraph && docker compose ps

# Logs anzeigen
docker compose logs backend --tail 50

# Neustart
docker compose restart backend nginx-ssl
```

---

## 📋 Offene Punkte / Next Steps

1. **Version Bump:** Code zeigt v2.3.0, aber v2.3.1/v2.3.2 wurde deployed
2. **CI/CD Pipeline:** GitHub Actions läuft, aber Auto-Deploy nach VPS sollte getestet werden
3. **Reisekosten-Mapping:** Keyword "Reisekosten" findet noch nichts (BRKG nicht im Graph als eigenständiges Dokument)
4. **Graph Expansion Deduplizierung:** Manchmal doppelte Rules in Response

---

## 📊 Stats

- **Knowledge Graph:** 11.490 Nodes geladen
- **BM25 Index:** 11.370 Chunks
- **Deployment-Zeit:** ~4 Stunden (inkl. Debugging)
