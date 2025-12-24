#!/bin/bash
# Kör alla Privacy Shield v2 tester med riktig data

set -e

echo "=========================================="
echo "PRIVACY SHIELD v2 - FULL TEST SUITE"
echo "=========================================="
echo ""

# Kontrollera att backend körs
echo "⏳ Kontrollerar backend..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend körs inte på localhost:8000"
    echo "   Starta backend först:"
    echo "   cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ Backend är igång"
echo ""

# Kontrollera att scrub_v2 endpoint finns
echo "⏳ Kontrollerar scrub_v2 endpoint..."
if ! curl -s -X POST http://localhost:8000/api/v1/privacy/scrub_v2 \
    -H "Content-Type: application/json" \
    -d '{"event_id":"00000000-0000-0000-0000-000000000000","production_mode":false}' \
    | grep -q "404\|Not Found"; then
    echo "✅ scrub_v2 endpoint finns"
else
    echo "❌ scrub_v2 endpoint finns inte - backend behöver startas om"
    echo "   cd backend && pkill -f uvicorn && uvicorn app.main:app --reload"
    exit 1
fi

echo ""

# Kör tester
echo "🚀 Kör omfattande A-Z tester..."
python3 scripts/test_full_privacy_v2.py

echo ""
echo "✅ Alla tester körda!"

