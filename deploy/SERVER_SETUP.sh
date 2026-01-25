#!/bin/bash

# SERVER SETUP GUIDE - Kopiere diese Befehle und führe auf deinem VPS aus

echo "🚀 Bund-ZuwendungsGraph Server Setup"
echo "====================================="
echo ""

# 1. Verzeichnis erstellen
echo "📁 Erstelle Projektverzeichnis..."
mkdir -p /opt/bund-zuwendungsgraph/{ssl,data,logs}
cd /opt/bund-zuwendungsgraph

# 2. Git Repository clonen
echo "📥 Klone Repository..."
git clone https://github.com/your-repo/Bund-ZuwendungsGraph.git .

# 3. SSL Dateien einfügen (manuell)
echo "🔐 SSL Setup - Folgende Dateien werden benötigt:"
echo "   - /opt/bund-zuwendungsgraph/ssl/_.digitalalchemisten.de_bundle.crt"
echo "   - /opt/bund-zuwendungsgraph/ssl/private.key"
echo ""
echo "WICHTIG: Kopiere die Certificate Bundle Datei von IONOS!"
echo ""

# 4. Umgebungsvariablen einrichten
echo "⚙️ Erstelle .env Datei..."
cat > .env << EOF
# IONOS API für Embeddings
IONOS_API_KEY=deine_ionos_api_key_hier

# ChromaDB Konfiguration
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Server Konfiguration
ENVIRONMENT=production
DEBUG=false
EOF

# 5. Docker starten (falls nicht installiert)
echo "🐳 Prüfe Docker Installation..."
if ! command -v docker &> /dev/null; then
    echo "Installiere Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installiere Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 6. Anwendung starten
echo "🚀 Starte Anwendung..."
docker compose up -d --build

# 7. Cronjob einrichten
echo "⏰ Richte automatische Updates ein..."
chmod +x setup_cron.sh
./setup_cron.sh

echo ""
echo "✅ Server Setup abgeschlossen!"
echo "🌐 Anwendung sollte laufen unter: https://foerderwissensgraph.digitalalchemisten.de"
echo ""
echo "Prüfe mit:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo ""