#!/bin/bash
# Bash status script for Copy/Paste project
# Shows backend health, frontend URL, and Docker container status

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🎯 SYSTEM STATUS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Backend health check
echo "✅ Backend: http://localhost:8000"
HEALTH_STATUS=$(curl -s http://localhost:8000/health 2>/dev/null | grep -o '"status":"[^"]*"' || echo "")
if [ -n "$HEALTH_STATUS" ]; then
    echo "   Health: $HEALTH_STATUS"
else
    echo "   Health: ❌ Unreachable"
fi

# Backend ready check
READY_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/ready 2>/dev/null)
READY_HTTP_CODE=$(echo "$READY_RESPONSE" | tail -1)
READY_BODY=$(echo "$READY_RESPONSE" | head -1)

if [ "$READY_HTTP_CODE" = "200" ]; then
    READY_STATUS=$(echo "$READY_BODY" | grep -o '"status":"[^"]*"' || echo "")
    echo "   Ready: $READY_STATUS"
elif [ "$READY_HTTP_CODE" = "503" ]; then
    echo "   Ready: ⚠️  DB not ready (503)"
else
    echo "   Ready: ❌ Error ($READY_HTTP_CODE)"
fi

echo ""
echo "✅ Frontend: http://localhost:5174"
echo "   (Öppna i webbläsare för att se UI:n)"
echo ""

# Docker container status
echo "📋 Docker Containers:"
docker ps --filter "name=copy-paste" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "   No containers running"

echo ""
echo "🔗 Öppna frontend: http://localhost:5174"
echo "════════════════════════════════════════════════════════════"
echo ""

