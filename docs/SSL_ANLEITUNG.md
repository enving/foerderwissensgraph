# SSL ZERTIFIKAT SETUP

## Was du brauchst vom IONOS Dashboard:

1. **Private Key** ✓ (hast du schon - `.digitalalchemisten.de_private_key.key`)
2. **Certificate Bundle** (muss heruntergeladen werden)

## Schritte:

### 1. IONOS Dashboard:
- Gehe zu SSL Management
- Finde dein Wildcard-Zertifikat für `*.digitalalchemisten.de`
- Lade "Certificate Bundle" herunter 
- Speichere als: `_.digitalalchemisten.de_bundle.crt`

### 2. Auf dem Server ausführen:
```bash
# SSH zum Server
ssh root@217.154.164.31

# Projektverzeichnis
mkdir -p /opt/bund-zuwendungsgraph/ssl
cd /opt/bund-zuwendungsgraph

# Dateien kopieren (von deinem lokalen Rechner):
scp ssl/private.key root@217.154.164.31:/opt/bund-zuwendungsgraph/ssl/
scp Downloads/_.digitalalchemisten.de_bundle.crt root@217.154.164.31:/opt/bund-zuwendungsgraph/ssl/

# Repository clonen
git clone https://github.com/dein-user/Bund-ZuwendungsGraph.git .

# Anwendung starten
docker compose up -d --build
```

### 3. Überprüfen:
```bash
# Services prüfen
docker compose ps

# Logs ansehen
docker compose logs -f

# Port prüfen
netstat -tlnp | grep :443
```

## Ergebnis:
Die Anwendung läuft unter:
- **Dashboard:** https://förderwissensgraph.digitalalchemisten.de
- **API:** https://förderwissensgraph.digitalalchemisten.de/api/docs

**WICHTIG:** Ohne Certificate Bundle Datei funktioniert SSL nicht!