#!/bin/bash

# Bund-ZuwendungsGraph Deployment Script
# Usage: ./deploy.sh [start|stop|restart|update|logs]

set -e

ACTION=${1:-start}
PROJECT_NAME="bund-zuwendungsgraph"

echo "🔧 Bund-ZuwendungsGraph Deployment - Action: $ACTION"

case $ACTION in
    start)
        echo "🚀 Starte Services..."
        docker compose up -d --build
        echo "✅ Services gestartet. Dashboard: https://foerderwissensgraph.digitalalchemisten.de"
        ;;
    
    stop)
        echo "🛑 Stoppe Services..."
        docker compose down
        echo "✅ Services gestoppt."
        ;;
    
    restart)
        echo "🔄 Starte Services neu..."
        docker compose down
        docker compose up -d --build
        echo "✅ Services neu gestartet. Dashboard: https://foerderwissensgraph.digitalalchemisten.de"
        ;;
    
    update)
        echo "📦 Aktualisiere Anwendung..."
        
        # Pull latest code (if in git repo)
        if [ -d ".git" ]; then
            echo "📥 Ziehe neueste Änderungen..."
            git pull
        fi
        
        # Rebuild and restart
        docker compose down
        docker compose up -d --build
        
        # Wait for services to be ready
        echo "⏳ Warte auf Bereitschaft der Services..."
        sleep 10
        
        # Run data update if requested
        if [ "$2" = "data" ]; then
            echo "📊 Führe Daten-Update aus..."
            docker compose exec backend python src/discovery/easy_crawler.py
            docker compose exec backend python src/parser/vector_store.py
        fi
        
        echo "✅ Update abgeschlossen. Dashboard: https://foerderwissensgraph.digitalalchemisten.de"
        ;;
    
    logs)
        echo "📋 Zeige Logs..."
        docker compose logs -f --tail=100
        ;;
    
    status)
        echo "📊 Service status:"
        docker compose ps
        ;;
    
    *)
        echo "❌ Unknown action: $ACTION"
        echo "Usage: $0 [start|stop|restart|update|logs|status]"
        echo "Examples:"
        echo "  $0 start                    # Start all services"
        echo "  $0 restart                  # Restart all services"  
        echo "  $0 update                   # Update and restart"
        echo "  $0 update data             # Update with data refresh"
        echo "  $0 logs                     # Show logs"
        echo "  $0 status                   # Show service status"
        exit 1
        ;;
esac

echo "🎉 Deployment action completed!"