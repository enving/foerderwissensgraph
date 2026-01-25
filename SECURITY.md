# Sicherheit (Security) - Bund-ZuwendungsGraph

## Datensouveränität & Privatsphäre
Der Schutz von Daten und die Souveränität über die verarbeiteten Informationen sind Kernbestandteile dieses Projekts.

### 1. Keine personenbezogenen Daten
Das System ist darauf ausgelegt, ausschließlich **öffentliche Bekanntmachungen, Richtlinien und Gesetze** zu verarbeiten. 
- Es werden keine Nutzerdaten, Profile oder persönlichen Informationen gespeichert.
- Die Suchanfragen werden nicht geloggt oder für das Training von Modellen verwendet.

### 2. Hosting in Deutschland
- **Embedding-Modelle**: Wir nutzen das Modell `BAAI/bge-m3` über die **IONOS Cloud**. Die Verarbeitung erfolgt in zertifizierten deutschen Rechenzentren unter Einhaltung der DSGVO.
- **Infrastruktur**: Die Anwendung selbst wird auf einem VPS in Deutschland gehostet.

### 3. Lokale Verarbeitung (Privacy-First)
- Das Parsing der PDF-Dokumente erfolgt mittels **Docling** lokal innerhalb der Docker-Container. 
- Es werden keine Dokumenteninhalte an externe Cloud-Parsing-Dienste gesendet.

### 4. Technische Sicherheitsmaßnahmen
- **Verschlüsselung**: Der Zugriff auf das Dashboard und die API erfolgt ausschließlich über HTTPS (SSL/TLS).
- **Container-Isolierung**: Die Anwendung läuft in isolierten Docker-Containern als non-root User (`graph`).
- **Minimaler Footprint**: Wir verwenden schlanke Base-Images und begrenzen die installierten Pakete auf das absolute Minimum.

## Meldung von Sicherheitslücken
Da dies ein Hobby-Projekt ist, bitten wir bei Entdeckung von potenziellen Sicherheitslücken um eine diskrete Mitteilung:
- Per GitHub Issue (wenn unkritisch)
- Per E-Mail an das Team der [DigitalAlchemisten](https://digitalalchemisten.de).

---
*Stand: Januar 2026*
