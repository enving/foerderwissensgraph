#!/bin/bash

# Setup Cronjob for Monthly Updates (User Level)
# Run this on the VPS

PROJECT_DIR="/home/graph/bund-zuwendungsgraph"
LOG_DIR="$PROJECT_DIR/logs"
CRON_CMD="0 3 1 * * cd $PROJECT_DIR && /usr/bin/docker compose exec -T backend python src/main_pipeline.py >> $LOG_DIR/cron.log 2>&1"

echo "⏰ Configuring Cronjob for user $(whoami)..."

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Check if job already exists (simple grep)
if crontab -l 2>/dev/null | grep -q "main_pipeline.py"; then
    echo "✅ Cronjob already exists in crontab."
else
    # Appending to crontab
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Cronjob added to crontab:"
    echo "   $CRON_CMD"
fi

echo ""
echo "To test the pipeline manually now, run:"
echo "cd $PROJECT_DIR && docker compose exec backend python src/main_pipeline.py"
