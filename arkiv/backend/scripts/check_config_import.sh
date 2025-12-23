#!/bin/bash
# CI check: Verify that config can be imported quickly without blocking

set -e

echo "Testing config import speed..."

# Test that config imports in < 2 seconds
if timeout 2 python3 -c "from app.core.config import settings; print('Config imported successfully')" 2>&1; then
    echo "✅ Config import OK (< 2s)"
    exit 0
else
    echo "❌ Config import FAILED or TIMED OUT (> 2s)"
    echo "This means config.py is doing something blocking (file I/O, network, etc)"
    exit 1
fi

