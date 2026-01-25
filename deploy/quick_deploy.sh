#!/bin/bash

# QUICK SERVER DEPLOY - User 'graph'
# Packages the application and uploads it to the VPS

SERVER="217.154.164.31"
USER="graph"
KEY="ssl/private.key"
PROJECT_DIR="/home/graph/bund-zuwendungsgraph"
DOMAIN="förderwissensgraph.digitalalchemisten.de"

echo "🚀 SMART DEPLOY (User: $USER)"
echo "======================================="

# 0. Check Key Permissions
if [ -f "$KEY" ]; then
    chmod 600 "$KEY"
else
    echo "❌ Error: Key file $KEY not found!"
    exit 1
fi

# 1. Clean up old artifacts
rm -f app.tar.gz

# 2. Package Application
echo "📦 Packaging application..."
tar -czf app.tar.gz \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='data/raw' \
    --exclude='data/chroma_db' \
    --exclude='data/chroma_db_container' \
    --exclude='tmp' \
    --exclude='.env' \
    .

FILE_SIZE=$(du -h app.tar.gz | cut -f1)
echo "✅ Package created: app.tar.gz ($FILE_SIZE)"

# 3. Prepare Remote Directory
echo "📂 Creating remote directory..."
ssh -i "$KEY" -o StrictHostKeyChecking=no $USER@$SERVER "mkdir -p $PROJECT_DIR"

# 4. Upload
echo "📤 Uploading to $SERVER..."
scp -i "$KEY" -o StrictHostKeyChecking=no app.tar.gz $USER@$SERVER:$PROJECT_DIR/

# 5. Deploy on Server
echo "🐳 Deploying on Server..."
ssh -i "$KEY" -o StrictHostKeyChecking=no $USER@$SERVER "cd $PROJECT_DIR && \
    tar -xzf app.tar.gz && \
    chmod +x deploy/*.sh && \
    
    # Ensure Docker is running (try with sudo if needed, assuming user in docker group)
    docker compose down && \
    docker compose up -d --build && \
    
    # Setup Cron (might fail if no sudo, but try)
    ./deploy/setup_cron.sh && \

    echo '✅ Deployment successful!' && \
    echo 'Server: https://$DOMAIN' && \
    docker compose ps"

echo ""
echo "🎉 DONE! Server is updated."