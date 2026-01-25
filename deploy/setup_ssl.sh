#!/bin/bash

# SSL Certificate Setup Script for foerderwissensgraph.digitalalchemisten.de
# This script helps set up the SSL certificate bundle

echo "🔐 SSL Certificate Setup - Bund-ZuwendungsGraph"
echo ""

# Check if certificate bundle exists
CERT_BUNDLE="./ssl/_.digitalalchemisten.de_bundle.crt"
PRIVATE_KEY="./ssl/private.key"

if [ ! -f "$CERT_BUNDLE" ]; then
    echo "❌ Zertifikats-Bundle nicht gefunden: $CERT_BUNDLE"
    echo ""
    echo "Bitte lade das Bundle aus dem IONOS Dashboard herunter:"
    echo "1. Gehe zu SSL-Verwaltung im IONOS Dashboard"
    echo "2. Lade das Bundle für *.digitalalchemisten.de herunter"
    echo "3. Speichere es als: $CERT_BUNDLE"
    echo ""
    echo "Das Bundle sollte die komplette Kette enthalten:"
    echo "  - Dein Domain-Zertifikat"
    echo "  - Intermediate-Zertifikate" 
    echo "  - Root-Zertifikat"
    echo ""
    exit 1
fi

if [ ! -f "$PRIVATE_KEY" ]; then
    echo "❌ Private Key nicht gefunden: $PRIVATE_KEY"
    echo "Bitte stelle sicher, dass der Private Key vorhanden ist."
    exit 1
fi

echo "✅ SSL-Dateien gefunden:"
echo "  Zertifikats-Bundle: $CERT_BUNDLE"
echo "  Private Key: $PRIVATE_KEY"
echo ""

# Set proper permissions
chmod 600 "$PRIVATE_KEY"
chmod 644 "$CERT_BUNDLE"
echo "✅ Dateiberechtigungen gesetzt"

echo ""
echo "🚀 SSL-Setup abgeschlossen! Du kannst nun die Services starten:"
echo "   ./deploy/deploy.sh"
echo ""
echo "The application will be available at:"
echo "   https://foerderwissensgraph.digitalalchemisten.de"