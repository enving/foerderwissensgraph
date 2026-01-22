#!/bin/bash
# Bund-ZuwendungsGraph - Monthly Update Script
# Führt den gesamten Pipeline-Zyklus im Docker-Container aus.

set -e

echo "--- Starting Monthly Update Cycle: $(date) ---"

# 1. Discovery: Neue Dokumente von Easy-Online crawlen
echo "Step 1/3: Crawling Easy-Online..."
docker exec app-backend-1 python src/discovery/easy_crawler.py

# 2. Parsing & Graph: Neue Dokumente verarbeiten (Graph Update)
# Hinweis: Docling_engine wird hier vorausgesetzt für die Extraktion
echo "Step 2/3: Parsing new documents..."
docker exec app-backend-1 python src/parser/docling_engine.py

# 3. Indexing: Vector Store & BM25 aktualisieren
echo "Step 3/3: Updating Vector Index & BM25..."
docker exec app-backend-1 python src/parser/vector_store.py
docker exec app-backend-1 python src/parser/bm25_index.py

# Backend neustarten, um neue Indizes (BM25) zu laden
echo "Restarting backend to apply changes..."
docker compose restart backend

echo "--- Update Cycle Completed Successfully: $(date) ---"
