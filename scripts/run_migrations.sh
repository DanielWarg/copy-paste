#!/bin/bash
cd "$(dirname "$0")/.."
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/copypaste"
python3 -m alembic upgrade head

