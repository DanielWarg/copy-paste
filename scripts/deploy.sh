#!/bin/bash
set -euo pipefail

# Deploy script for Copy/Paste
# Usage: ./scripts/deploy.sh

echo "🚀 Starting deployment..."

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Build and restart services
echo "🔨 Building and restarting services..."
docker compose -f docker-compose.yml -f deploy/compose.prod.yml up -d --build

# Run migrations
echo "📊 Running migrations..."
docker compose exec backend alembic upgrade head

# Verify deployment
echo "✅ Verifying deployment..."
sleep 5
curl -f https://nyhetsdesk.postboxen.se/health || {
    echo "❌ Health check failed!"
    exit 1
}

echo "✅ Deployment complete!"

