#!/usr/bin/env python3
"""
Test Scout med SCOUT_RUN_ONCE för att polla feeds direkt.
"""
import os
import sys
import asyncio

# Sätt environment variables
os.environ["BACKEND_URL"] = "http://localhost:8000"
os.environ["FEEDS_CONFIG"] = "scout/feeds.yaml"
os.environ["SCOUT_RUN_ONCE"] = "true"

# Lägg till scout i path
sys.path.insert(0, "scout")

# Importera och kör scheduler
from scheduler import main

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTAR SCOUT RUN_ONCE")
    print("=" * 60)
    print()
    
    asyncio.run(main())

