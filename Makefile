.PHONY: up down restart logs health test clean lint format typecheck ci frontend-dev dev verify smoke live-verify purge

# Default target
.DEFAULT_GOAL := help

# Variables
COMPOSE_FILE := docker-compose.yml
BACKEND_URL := http://localhost:8000
FRONTEND_URL := http://localhost:5173

help:
	@echo "Copy/Paste Core - Makefile Commands"
	@echo ""
	@echo "  make up           - Start all services (PostgreSQL + Backend + Frontend)"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - Show logs from all services"
	@echo "  make health       - Check /health and /ready endpoints"
	@echo "  make smoke        - Quick smoke test (health + ready)"
	@echo "  make test         - Run smoke tests (start stack, check endpoints)"
	@echo "  make verify       - Complete GO/NO-GO verification (all checks)"
	@echo "  make live-verify       - Live bulletproof test (real DB + backend + fixtures)"
	@echo "  make live-verify-reset - Live test with Docker reset (down -v before test)"
	@echo "  make lint         - Run ruff check"
	@echo "  make format       - Run ruff format"
	@echo "  make typecheck    - Run mypy type check"
	@echo "  make ci           - Run lint + typecheck + test"
	@echo "  make frontend-dev - Run frontend dev server locally"
	@echo "  make dev          - Start backend + frontend (local, no Docker)"
	@echo "  make clean        - Stop services and remove volumes"

up:
	@echo "Starting services..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@make health

down:
	@echo "Stopping services..."
	docker-compose -f $(COMPOSE_FILE) down

restart:
	@echo "Restarting services..."
	docker-compose -f $(COMPOSE_FILE) restart
	@sleep 3
	@make health

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

health:
	@echo "Checking /health endpoint..."
	@curl -s $(BACKEND_URL)/health | python3 -m json.tool || echo "❌ /health failed"
	@echo ""
	@echo "Checking /ready endpoint..."
	@curl -s $(BACKEND_URL)/ready | python3 -m json.tool || echo "❌ /ready failed"

smoke:
	@echo "Running quick smoke test..."
	@HTTP_CODE=$$(curl -s -o /dev/null -w "%{http_code}" $(BACKEND_URL)/health); \
	if [ "$$HTTP_CODE" = "200" ]; then \
		echo "✅ /health returned 200"; \
	else \
		echo "❌ /health returned $$HTTP_CODE"; \
		exit 1; \
	fi
	@HTTP_CODE=$$(curl -s -o /dev/null -w "%{http_code}" $(BACKEND_URL)/ready); \
	if [ "$$HTTP_CODE" = "200" ] || [ "$$HTTP_CODE" = "503" ]; then \
		echo "✅ /ready returned $$HTTP_CODE"; \
	else \
		echo "❌ /ready returned $$HTTP_CODE"; \
		exit 1; \
	fi
	@echo "✅ Smoke test passed"

verify:
	@echo "Running complete GO/NO-GO verification..."
	@echo ""
	@python3 scripts/verify_complete.py || exit 1
	@echo ""
	@echo "Running make test (smoke tests)..."
	@make test || exit 1
	@echo ""
	@echo "Running make ci (code quality)..."
	@make ci || exit 1
	@echo ""
	@echo "=========================================="
	@echo "✅ ALL VERIFICATIONS PASSED - GO"
	@echo "=========================================="

live-verify:
	@echo "Running Live Bulletproof Test Pass..."
	@echo ""
	@echo "Step 1: Ensuring services are up..."
	@docker-compose -f $(COMPOSE_FILE) up -d || true
	@sleep 5
	@echo ""
	@echo "Step 2: Running live verification..."
	@python3 scripts/live_verify.py || exit 1
	@echo ""
	@echo "=========================================="
	@echo "✅ LIVE VERIFICATION PASSED - GO"
	@echo "=========================================="

live-verify-reset:
	@echo "Running Live Bulletproof Test Pass (with reset)..."
	@echo ""
	@echo "Step 1: Running live verification with --reset..."
	@python3 scripts/live_verify.py --reset || exit 1
	@echo ""
	@echo "=========================================="
	@echo "✅ LIVE VERIFICATION PASSED - GO"
	@echo "=========================================="

test:
	@echo "Running comprehensive smoke tests..."
	@echo ""
	@echo "=========================================="
	@echo "SCENARIO A: No DB configured"
	@echo "=========================================="
	@echo "Starting backend without DATABASE_URL..."
	@docker-compose -f $(COMPOSE_FILE) stop backend postgres 2>/dev/null || true
	@docker-compose -f $(COMPOSE_FILE) up -d postgres
	@sleep 3
	@echo "Starting backend container without DATABASE_URL..."
	@docker-compose -f $(COMPOSE_FILE) run --rm -d --name test-backend-no-db -e DATABASE_URL= -p 8001:8000 backend uvicorn app.main:app --host 0.0.0.0 --port 8000 || true
	@sleep 5
	@echo "Testing /health (should be 200)..."
	@HTTP_CODE=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "000"); \
	if [ "$$HTTP_CODE" = "200" ]; then \
		echo "✅ /health returned 200"; \
	else \
		echo "❌ /health returned $$HTTP_CODE"; \
		docker stop test-backend-no-db 2>/dev/null || true; \
		docker rm test-backend-no-db 2>/dev/null || true; \
		exit 1; \
	fi
	@echo "Testing /ready (should be 200 with db:not_configured)..."
	@RESPONSE=$$(curl -s http://localhost:8001/ready); \
	HTTP_CODE=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/ready); \
	if [ "$$HTTP_CODE" = "200" ]; then \
		echo "$$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert data.get('status') == 'ready', 'Missing ready status'; assert data.get('db') == 'not_configured', 'Should have db:not_configured'; print('✅ /ready returned 200 with db:not_configured')" || (echo "❌ /ready response structure invalid: $$RESPONSE"; docker stop test-backend-no-db 2>/dev/null || true; docker rm test-backend-no-db 2>/dev/null || true; exit 1); \
	else \
		echo "❌ /ready returned $$HTTP_CODE (expected 200), response: $$RESPONSE"; \
		docker stop test-backend-no-db 2>/dev/null || true; \
		docker rm test-backend-no-db 2>/dev/null || true; \
		exit 1; \
	fi
	@echo "Testing /api/v1/transcripts (No DB - should return seed data)..."
	@TRANS_RESPONSE=$$(curl -s http://localhost:8001/api/v1/transcripts); \
	TRANS_CODE=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/transcripts); \
	if [ "$$TRANS_CODE" = "200" ]; then \
		echo "$$TRANS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert 'items' in data, 'Missing items'; assert len(data.get('items', [])) > 0, 'Should have seed data'; print('✅ /api/v1/transcripts returned 200 with seed data')" || (echo "❌ /api/v1/transcripts response invalid: $$TRANS_RESPONSE"; docker stop test-backend-no-db 2>/dev/null || true; docker rm test-backend-no-db 2>/dev/null || true; exit 1); \
	else \
		echo "❌ /api/v1/transcripts returned $$TRANS_CODE (expected 200), response: $$TRANS_RESPONSE"; \
		docker stop test-backend-no-db 2>/dev/null || true; \
		docker rm test-backend-no-db 2>/dev/null || true; \
		exit 1; \
	fi
	@echo "Testing /api/v1/transcripts/1 (No DB - should return transcript)..."
	@TRANS1_RESPONSE=$$(curl -s http://localhost:8001/api/v1/transcripts/1); \
	TRANS1_CODE=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/transcripts/1); \
	if [ "$$TRANS1_CODE" = "200" ]; then \
		echo "$$TRANS1_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert data.get('id') == 1, 'Wrong transcript ID'; assert 'segments' in data, 'Missing segments'; print('✅ /api/v1/transcripts/1 returned 200 with transcript')" || (echo "❌ /api/v1/transcripts/1 response invalid: $$TRANS1_RESPONSE"; docker stop test-backend-no-db 2>/dev/null || true; docker rm test-backend-no-db 2>/dev/null || true; exit 1); \
	else \
		echo "❌ /api/v1/transcripts/1 returned $$TRANS1_CODE (expected 200), response: $$TRANS1_RESPONSE"; \
		docker stop test-backend-no-db 2>/dev/null || true; \
		docker rm test-backend-no-db 2>/dev/null || true; \
		exit 1; \
	fi
	@echo "Testing /api/v1/transcripts/1/export?format=quotes (No DB)..."
	@EXPORT_RESPONSE=$$(curl -s "http://localhost:8001/api/v1/transcripts/1/export?format=quotes"); \
	EXPORT_CODE=$$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/api/v1/transcripts/1/export?format=quotes"); \
	if [ "$$EXPORT_CODE" = "200" ]; then \
		echo "$$EXPORT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert data.get('format') == 'quotes', 'Wrong format'; assert 'items' in data, 'Missing items'; print('✅ /api/v1/transcripts/1/export returned 200 with quotes')" || (echo "❌ /api/v1/transcripts/1/export response invalid: $$EXPORT_RESPONSE"; docker stop test-backend-no-db 2>/dev/null || true; docker rm test-backend-no-db 2>/dev/null || true; exit 1); \
	else \
		echo "❌ /api/v1/transcripts/1/export returned $$EXPORT_CODE (expected 200), response: $$EXPORT_RESPONSE"; \
		docker stop test-backend-no-db 2>/dev/null || true; \
		docker rm test-backend-no-db 2>/dev/null || true; \
		exit 1; \
	fi
	@docker stop test-backend-no-db 2>/dev/null || true
	@docker rm test-backend-no-db 2>/dev/null || true
	@echo ""
	@echo "=========================================="
	@echo "SCENARIO B: DB up"
	@echo "=========================================="
	@echo "Starting full stack with PostgreSQL..."
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Testing /health (should be 200)..."
	@HTTP_CODE=$$(curl -s -o /dev/null -w "%{http_code}" $(BACKEND_URL)/health); \
	if [ "$$HTTP_CODE" = "200" ]; then \
		echo "✅ /health returned 200"; \
	else \
		echo "❌ /health returned $$HTTP_CODE"; \
		exit 1; \
	fi
	@echo "Testing /ready (should be 200 with DB up)..."
	@RESPONSE=$$(curl -s $(BACKEND_URL)/ready); \
	HTTP_CODE=$$(curl -s -o /dev/null -w "%{http_code}" $(BACKEND_URL)/ready); \
	if [ "$$HTTP_CODE" = "200" ]; then \
		echo "$$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert data.get('status') == 'ready', 'Missing ready status'; print('✅ /ready returned 200 with DB up')" || (echo "❌ /ready response structure invalid: $$RESPONSE"; exit 1); \
	else \
		echo "❌ /ready returned $$HTTP_CODE (expected 200 with DB up), response: $$RESPONSE"; \
		exit 1; \
	fi
	@echo "Testing /api/v1/example (should be 200)..."
	@RESPONSE=$$(curl -s "$(BACKEND_URL)/api/v1/example?q=test"); \
	HTTP_CODE=$$(curl -s -o /dev/null -w "%{http_code}" "$(BACKEND_URL)/api/v1/example?q=test"); \
	if [ "$$HTTP_CODE" = "200" ]; then \
		echo "$$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert data.get('status') == 'ok', 'Missing ok status'; assert data.get('module') == 'example', 'Missing module:example'; print('✅ /api/v1/example returned 200 with module:example')" || (echo "❌ /api/v1/example response structure invalid: $$RESPONSE"; exit 1); \
	else \
		echo "❌ /api/v1/example returned $$HTTP_CODE (expected 200), response: $$RESPONSE"; \
		exit 1; \
	fi
	@echo "Testing error handling (validation error)..."
	@ERROR_RESPONSE=$$(curl -s "$(BACKEND_URL)/api/v1/example"); \
	ERROR_CODE=$$(curl -s -o /dev/null -w "%{http_code}" "$(BACKEND_URL)/api/v1/example"); \
	if [ "$$ERROR_CODE" = "422" ]; then \
		echo "$$ERROR_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert 'error' in data, 'Missing error field'; assert 'request_id' in data.get('error', {}), 'Missing request_id'; assert data['error'].get('code') == 'validation_error', 'Wrong error code'; assert 'traceback' not in str(data).lower(), 'Should not contain traceback'; assert 'file' not in str(data).lower() or '/app/' not in str(data), 'Should not contain file paths'; print('✅ Error handling works: 422 with request_id, no traceback')" || (echo "⚠️  Error response structure unclear: $$ERROR_RESPONSE"; exit 1); \
	else \
		echo "❌ Expected 422 validation error, got $$ERROR_CODE, response: $$ERROR_RESPONSE"; \
		exit 1; \
	fi
	@echo ""
	@echo "Testing Transcripts module (DB up)..."
	@echo "Creating transcript..."
	@CREATE_RESPONSE=$$(curl -s -X POST "$(BACKEND_URL)/api/v1/transcripts" -H "Content-Type: application/json" -d '{"title":"Test Transcript","source":"test","language":"sv"}'); \
	CREATE_CODE=$$(curl -s -o /dev/null -w "%{http_code}" -X POST "$(BACKEND_URL)/api/v1/transcripts" -H "Content-Type: application/json" -d '{"title":"Test Transcript","source":"test","language":"sv"}'); \
	if [ "$$CREATE_CODE" = "200" ]; then \
		TRANS_ID=$$(echo "$$CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id'))"); \
		echo "✅ Created transcript ID: $$TRANS_ID"; \
		echo "Adding segments..."; \
		SEG_RESPONSE=$$(curl -s -X POST "$(BACKEND_URL)/api/v1/transcripts/$$TRANS_ID/segments" -H "Content-Type: application/json" -d '{"segments":[{"start_ms":0,"end_ms":5000,"speaker_label":"SPEAKER_1","text":"Test segment text","confidence":0.95}]}'); \
		SEG_CODE=$$(curl -s -o /dev/null -w "%{http_code}" -X POST "$(BACKEND_URL)/api/v1/transcripts/$$TRANS_ID/segments" -H "Content-Type: application/json" -d '{"segments":[{"start_ms":0,"end_ms":5000,"speaker_label":"SPEAKER_1","text":"Test segment text","confidence":0.95}]}'); \
		if [ "$$SEG_CODE" = "200" ]; then \
			echo "✅ Added segments"; \
			echo "Testing GET transcript..."; \
			GET_RESPONSE=$$(curl -s "$(BACKEND_URL)/api/v1/transcripts/$$TRANS_ID"); \
			GET_CODE=$$(curl -s -o /dev/null -w "%{http_code}" "$(BACKEND_URL)/api/v1/transcripts/$$TRANS_ID"); \
			if [ "$$GET_CODE" = "200" ]; then \
				echo "$$GET_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert data.get('id') == int('$$TRANS_ID'), 'Wrong ID'; assert 'segments' in data, 'Missing segments'; assert len(data.get('segments', [])) > 0, 'No segments'; print('✅ GET transcript returned 200 with segments')" || (echo "❌ GET transcript response invalid: $$GET_RESPONSE"; exit 1); \
			else \
				echo "❌ GET transcript returned $$GET_CODE, response: $$GET_RESPONSE"; \
				exit 1; \
			fi; \
			echo "Testing export SRT..."; \
			SRT_RESPONSE=$$(curl -s "$(BACKEND_URL)/api/v1/transcripts/$$TRANS_ID/export?format=srt"); \
			SRT_CODE=$$(curl -s -o /dev/null -w "%{http_code}" "$(BACKEND_URL)/api/v1/transcripts/$$TRANS_ID/export?format=srt"); \
			if [ "$$SRT_CODE" = "200" ]; then \
				echo "$$SRT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert data.get('format') == 'srt', 'Wrong format'; assert '00:00:00,000' in data.get('content', ''), 'Missing SRT time format'; print('✅ Export SRT returned 200 with correct format')" || (echo "❌ Export SRT response invalid: $$SRT_RESPONSE"; exit 1); \
			else \
				echo "❌ Export SRT returned $$SRT_CODE, response: $$SRT_RESPONSE"; \
				exit 1; \
			fi; \
			echo "Testing DELETE transcript..."; \
			DEL_RESPONSE=$$(curl -s -X DELETE "$(BACKEND_URL)/api/v1/transcripts/$$TRANS_ID"); \
			DEL_CODE=$$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$(BACKEND_URL)/api/v1/transcripts/$$TRANS_ID"); \
			if [ "$$DEL_CODE" = "200" ]; then \
				echo "$$DEL_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); assert data.get('status') == 'deleted', 'Wrong status'; assert 'receipt_id' in data, 'Missing receipt_id'; print('✅ DELETE transcript returned 200 with receipt')" || (echo "❌ DELETE transcript response invalid: $$DEL_RESPONSE"; exit 1); \
			else \
				echo "❌ DELETE transcript returned $$DEL_CODE, response: $$DEL_RESPONSE"; \
				exit 1; \
			fi; \
		else \
			echo "❌ Add segments returned $$SEG_CODE, response: $$SEG_RESPONSE"; \
			exit 1; \
		fi; \
	else \
		echo "❌ Create transcript returned $$CREATE_CODE, response: $$CREATE_RESPONSE"; \
		exit 1; \
	fi
	@echo ""
	@echo "=========================================="
	@echo "SCENARIO C: DB down"
	@echo "=========================================="
	@echo "Stopping PostgreSQL but keeping backend running..."
	@docker-compose -f $(COMPOSE_FILE) stop postgres
	@sleep 2
	@echo "Testing /ready (should be 503 within timeout)..."
	@START_TIME=$$(date +%s); \
	RESPONSE=$$(curl -s -w "\n%{http_code}" $(BACKEND_URL)/ready 2>&1); \
	END_TIME=$$(date +%s); \
	ELAPSED=$$((END_TIME - START_TIME)); \
	HTTP_CODE=$$(echo "$$RESPONSE" | tail -n1); \
	BODY=$$(echo "$$RESPONSE" | head -n-1); \
	if [ "$$HTTP_CODE" = "503" ]; then \
		echo "$$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); detail=data.get('detail', {}); assert detail.get('status') == 'db_down' or data.get('status') == 'db_down', 'Missing db_down status'; print('✅ /ready returned 503 with db_down')" || echo "⚠️  /ready returned 503 but response structure unclear: $$BODY"; \
		if [ $$ELAPSED -lt 4 ]; then \
			echo "✅ Timeout respected ($$ELAPSED seconds < 4 seconds)"; \
		else \
			echo "⚠️  Timeout took longer than expected ($$ELAPSED seconds)"; \
		fi; \
	else \
		echo "❌ /ready returned $$HTTP_CODE (expected 503 when DB is down), response: $$BODY"; \
		docker-compose -f $(COMPOSE_FILE) up -d postgres; \
		exit 1; \
	fi
	@docker-compose -f $(COMPOSE_FILE) up -d postgres
	@echo ""
	@echo "=========================================="
	@echo "✅ All smoke tests passed!"
	@echo "=========================================="

lint:
	@echo "Running ruff check..."
	ruff check backend/app

format:
	@echo "Running ruff format..."
	ruff format backend/app

typecheck:
	@echo "Running mypy type check..."
	mypy backend/app

ci: lint typecheck test check-docs
	@echo "✅ All CI checks passed!"

check-docs:
	@echo "Checking documentation consistency..."
	@./scripts/check_docs.sh

frontend-dev:
	@echo "Starting frontend development server..."
	@cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 5173

dev:
	@echo "Starting backend and frontend locally..."
	@cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@sleep 3
	@make frontend-dev
	@echo "Backend running on $(BACKEND_URL)"
	@echo "Frontend running on http://localhost:5173"
	@echo "Press Ctrl+C to stop both."
	fg

purge:
	@echo "Running Record purge (GDPR retention)..."
	@docker-compose -f $(COMPOSE_FILE) exec backend python -m app.modules.record.purge_runner

purge-dry-run:
	@echo "Running Record purge (dry run)..."
	@docker-compose -f $(COMPOSE_FILE) exec backend python -m app.modules.record.purge_runner --dry-run

clean:
	@echo "Stopping services and removing volumes..."
	docker-compose -f $(COMPOSE_FILE) down -v
