#!/bin/bash

# Setup Cronjob for Quarterly Updates (January, April, July, October)
# Run this on the VPS

PROJECT_DIR="/home/graph/bund-zuwendungsgraph"
LOG_DIR="$PROJECT_DIR/logs"
# 0 3 1 */3 * -> At 03:00 on day 1 of every 3rd month
CRON_CMD="0 3 1 */3 * cd $PROJECT_DIR && /usr/bin/docker compose exec -T backend python src/main_pipeline.py >> $LOG_DIR/cron.log 2>&1"

echo "⏰ Konfiguriere Quartals-Cronjob für User $(whoami)..."

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# 2. Setup user-level crontab
if crontab -l 2>/dev/null | grep -q "main_pipeline.py"; then
    echo "♻️ Aktualisiere existierenden Cronjob..."
    (crontab -l 2>/dev/null | grep -v "main_pipeline.py"; echo "$CRON_CMD") | crontab -
else
    echo "➕ Füge neuen Cronjob hinzu..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
fi

echo "✅ Cronjob konfiguriert:"
echo "   $CRON_CMD"

echo ""
echo "Um die Pipeline jetzt manuell zu testen:"
echo "cd $PROJECT_DIR && docker compose exec backend python src/main_pipeline.py"
