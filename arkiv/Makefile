.PHONY: help up up-backend up-frontend up-scout up-all down down-backend down-frontend down-scout down-all restart restart-backend restart-frontend restart-scout restart-all test logs health check-backend

help:
	@echo "Copy/Paste - Editorial AI Pipeline"
	@echo ""
	@echo "Commands:"
	@echo "  make up          - Start backend and frontend servers"
	@echo "  make up-all      - Start backend, frontend and scout servers"
	@echo "  make up-backend  - Start backend server only"
	@echo "  make up-frontend - Start frontend server only"
	@echo "  make up-scout    - Start scout server only"
	@echo "  make down        - Stop backend and frontend servers"
	@echo "  make down-all    - Stop backend, frontend and scout servers"
	@echo "  make down-backend - Stop backend server only"
	@echo "  make down-frontend - Stop frontend server only"
	@echo "  make down-scout  - Stop scout server only"
	@echo "  make restart     - Restart backend and frontend servers"
	@echo "  make restart-all - Restart backend, frontend and scout servers"
	@echo "  make restart-backend - Restart backend server only"
	@echo "  make restart-frontend - Restart frontend server only"
	@echo "  make restart-scout - Restart scout server only"
	@echo "  make test        - Run test suite"
	@echo "  make logs        - Show backend logs"
	@echo "  make health      - Check if backend is running"
	@echo "  make check-backend - Verify backend can import"

# Backend server management
BACKEND_DIR = backend
BACKEND_PORT = 8000
PID_FILE = .backend.pid
LOG_FILE = backend.log

# Frontend server management
FRONTEND_DIR = frontend
FRONTEND_PORT = 3000
FRONTEND_PID_FILE = .frontend.pid
FRONTEND_LOG_FILE = frontend.log

# Scout server management
SCOUT_DIR = scout
SCOUT_PORT = 8001
SCOUT_PID_FILE = .scout.pid
SCOUT_LOG_FILE = .scout.log

up:
	@echo "Starting backend server..."
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Backend already running (PID: $$PID)"; \
			make health; \
			exit 0; \
		fi; \
	fi
	@cd $(BACKEND_DIR) && \
	(python3 -m uvicorn app.main:app --host 0.0.0.0 --port $(BACKEND_PORT) > ../$(LOG_FILE) 2>&1 & echo $$! > ../$(PID_FILE))
	@sleep 3
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Backend started (PID: $$PID)"; \
		else \
			echo "⚠️  Backend process died. Check logs:"; \
			tail -20 $(LOG_FILE) 2>/dev/null || echo "No log file"; \
			rm -f $(PID_FILE); \
			exit 1; \
		fi; \
	else \
		echo "⚠️  PID file not created. Check logs:"; \
		tail -20 $(LOG_FILE) 2>/dev/null || echo "No log file"; \
		exit 1; \
	fi
	@echo "Waiting for server to be ready..."
	@for i in 1 2 3 4 5; do \
		sleep 1; \
		if curl -s http://localhost:$(BACKEND_PORT)/health > /dev/null 2>&1; then \
			echo "✅ Server is ready"; \
			make health; \
			exit 0; \
		fi; \
	done; \
	echo "⚠️  Server may still be starting. Check logs with 'make logs'"

down:
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Stopping backend server (PID: $$PID)..."; \
			kill $$PID; \
			rm $(PID_FILE); \
			echo "Backend stopped"; \
		else \
			echo "Backend process not running"; \
			rm $(PID_FILE); \
		fi; \
	else \
		echo "No PID file found. Trying to find and kill uvicorn processes..."; \
		pkill -f "uvicorn.*app.main:app" || echo "No uvicorn processes found"; \
	fi

up-frontend:
	@echo "Starting frontend server..."
	@if [ -f $(FRONTEND_PID_FILE) ]; then \
		PID=$$(cat $(FRONTEND_PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Frontend already running (PID: $$PID)"; \
			exit 0; \
		fi; \
	fi
	@cd $(FRONTEND_DIR) && \
	if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/vite" ]; then \
		echo "Installing frontend dependencies..."; \
		npm install; \
	fi
	@cd $(FRONTEND_DIR) && \
	if [ -f "node_modules/.bin/vite" ]; then \
		(./node_modules/.bin/vite --host 0.0.0.0 --port $(FRONTEND_PORT) > ../$(FRONTEND_LOG_FILE) 2>&1 & echo $$! > ../$(FRONTEND_PID_FILE)); \
	else \
		(npm run dev -- --host 0.0.0.0 --port $(FRONTEND_PORT) > ../$(FRONTEND_LOG_FILE) 2>&1 & echo $$! > ../$(FRONTEND_PID_FILE)); \
	fi
	@sleep 3
	@if [ -f $(FRONTEND_PID_FILE) ]; then \
		PID=$$(cat $(FRONTEND_PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Frontend started (PID: $$PID)"; \
			echo "Frontend available at http://localhost:$(FRONTEND_PORT)"; \
		else \
			echo "⚠️  Frontend process died. Check logs:"; \
			tail -20 $(FRONTEND_LOG_FILE) 2>/dev/null || echo "No log file"; \
			rm -f $(FRONTEND_PID_FILE); \
			exit 1; \
		fi; \
	else \
		echo "⚠️  PID file not created. Check logs:"; \
		tail -20 $(FRONTEND_LOG_FILE) 2>/dev/null || echo "No log file"; \
		exit 1; \
	fi

down-frontend:
	@if [ -f $(FRONTEND_PID_FILE) ]; then \
		PID=$$(cat $(FRONTEND_PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Stopping frontend server (PID: $$PID)..."; \
			kill $$PID; \
			rm $(FRONTEND_PID_FILE); \
			echo "Frontend stopped"; \
		else \
			echo "Frontend process not running"; \
			rm $(FRONTEND_PID_FILE); \
		fi; \
	else \
		echo "No frontend PID file found. Trying to find and kill vite processes..."; \
		pkill -f "vite" || echo "No vite processes found"; \
	fi

restart-frontend: down-frontend up-frontend

# Scout server management
up-scout:
	@echo "Starting scout server..."
	@if [ -f $(SCOUT_PID_FILE) ]; then \
		PID=$$(cat $(SCOUT_PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Scout already running (PID: $$PID)"; \
			curl -s http://localhost:$(SCOUT_PORT)/health > /dev/null && echo "✅ Scout is healthy" || echo "⚠️  Scout not responding"; \
			exit 0; \
		fi; \
	fi
	@cd $(SCOUT_DIR) && \
	(BACKEND_URL="http://localhost:8000" python3 scheduler.py > ../$(SCOUT_LOG_FILE) 2>&1 & echo $$! > ../$(SCOUT_PID_FILE))
	@sleep 5
	@if [ -f $(SCOUT_PID_FILE) ]; then \
		PID=$$(cat $(SCOUT_PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Scout started (PID: $$PID)"; \
		else \
			echo "⚠️  Scout process died. Check logs:"; \
			tail -20 $(SCOUT_LOG_FILE) 2>/dev/null || echo "No log file"; \
			rm -f $(SCOUT_PID_FILE); \
			exit 1; \
		fi; \
	else \
		echo "⚠️  PID file not created. Check logs:"; \
		tail -20 $(SCOUT_LOG_FILE) 2>/dev/null || echo "No log file"; \
		exit 1; \
	fi
	@echo "Waiting for scout to be ready..."
	@for i in 1 2 3 4 5; do \
		sleep 1; \
		if curl -s http://localhost:$(SCOUT_PORT)/health > /dev/null 2>&1; then \
			echo "✅ Scout is ready"; \
			exit 0; \
		fi; \
	done; \
	echo "⚠️  Scout may still be starting. Check logs: tail -f $(SCOUT_LOG_FILE)"

down-scout:
	@if [ -f $(SCOUT_PID_FILE) ]; then \
		PID=$$(cat $(SCOUT_PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Stopping scout server (PID: $$PID)..."; \
			kill $$PID; \
			rm $(SCOUT_PID_FILE); \
			echo "Scout stopped"; \
		else \
			echo "Scout process not running"; \
			rm $(SCOUT_PID_FILE); \
		fi; \
	else \
		echo "No scout PID file found. Trying to find and kill scheduler processes..."; \
		pkill -f "scheduler.py" || echo "No scheduler processes found"; \
	fi

restart-scout: down-scout up-scout

# Backend-specific targets (renamed from up/down to avoid circular dependency)
up-backend:
	@echo "Starting backend server..."
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Backend already running (PID: $$PID)"; \
			make health; \
			exit 0; \
		fi; \
	fi
	@cd $(BACKEND_DIR) && \
	(python3 -m uvicorn app.main:app --host 0.0.0.0 --port $(BACKEND_PORT) > ../$(LOG_FILE) 2>&1 & echo $$! > ../$(PID_FILE))
	@sleep 3
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Backend started (PID: $$PID)"; \
		else \
			echo "⚠️  Backend process died. Check logs:"; \
			tail -20 $(LOG_FILE) 2>/dev/null || echo "No log file"; \
			rm -f $(PID_FILE); \
			exit 1; \
		fi; \
	else \
		echo "⚠️  PID file not created. Check logs:"; \
		tail -20 $(LOG_FILE) 2>/dev/null || echo "No log file"; \
		exit 1; \
	fi
	@echo "Waiting for server to be ready..."
	@for i in 1 2 3 4 5; do \
		sleep 1; \
		if curl -s http://localhost:$(BACKEND_PORT)/health > /dev/null 2>&1; then \
			echo "✅ Server is ready"; \
			make health; \
			exit 0; \
		fi; \
	done; \
	echo "⚠️  Server may still be starting. Check logs with 'make logs'"

down-backend:
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Stopping backend server (PID: $$PID)..."; \
			kill $$PID; \
			rm $(PID_FILE); \
			echo "Backend stopped"; \
		else \
			echo "Backend process not running"; \
			rm $(PID_FILE); \
		fi; \
	else \
		echo "No PID file found. Trying to find and kill uvicorn processes..."; \
		pkill -f "uvicorn.*app.main:app" || echo "No uvicorn processes found"; \
	fi

restart-backend: down-backend up-backend

# Start both backend and frontend
up: up-backend up-frontend

# Start all services (backend, frontend, scout)
up-all: up-backend up-frontend up-scout

# Stop both backend and frontend
down: down-backend down-frontend

# Stop all services (backend, frontend, scout)
down-all: down-backend down-frontend down-scout

# Restart both backend and frontend
restart: restart-backend restart-frontend

# Restart all services (backend, frontend, scout)
restart-all: restart-backend restart-frontend restart-scout

# Testing
test:
	@echo "Running test suite..."
	@python3 scripts/test_suite_v2.py

# Utilities
logs:
	@if [ -f $(LOG_FILE) ]; then \
		tail -f $(LOG_FILE); \
	else \
		echo "No log file found. Start server with 'make up' first."; \
	fi

health:
	@echo "Checking backend health..."
	@curl -s http://localhost:$(BACKEND_PORT)/health > /dev/null && echo "✅ Backend is healthy" || echo "❌ Backend is not responding"

check-backend:
	@echo "Checking if backend can import..."
	@cd $(BACKEND_DIR) && python3 -c "from app.main import app; print('✅ Backend imports OK')" || echo "❌ Backend import failed"

