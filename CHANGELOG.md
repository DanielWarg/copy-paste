# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-12-23

### Added - CORE v1.0.0

**Foundation:**
- FastAPI backend with DB-optional architecture
- Privacy-safe structured JSON logging
- Global exception handling with consistent error shape
- Request ID middleware with timing
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- CORS sanity guard (prevents "*" in production)

**Endpoints:**
- `GET /health` - Always returns 200
- `GET /ready` - Returns 200/503 based on DB status
- `GET /meta` - Optional version info (behind ENABLE_META flag)

**Infrastructure:**
- Docker & docker-compose setup
- Alembic migrations (minimal service_state table)
- Makefile with up/down/test/ci targets
- GitHub Actions CI pipeline
- Pre-commit hooks (ruff, mypy)
- Quality gates (ruff lint, ruff format, mypy)

**Example Module:**
- Reference implementation demonstrating Module Contract v1
- `GET /api/v1/example` endpoint

**Testing:**
- Comprehensive smoke tests (no DB, DB up, DB down scenarios)
- Error handling verification
- Privacy-safe logging assertions

**Documentation:**
- Complete README with architecture, API docs, troubleshooting
- Module Contract v1 specification
- CORE v1 freeze policy

### Security

- Privacy-by-default logging (no payloads, no headers, no PII)
- CORS guard prevents wide-open CORS in production
- Security headers always set
- Request ID for traceability

### Performance

- DB health check with hard timeout (non-blocking)
- Log sampling support (LOG_SAMPLE_RATE)
- Efficient async/await patterns

---

## Release Tags

- `core-v1.0.0` - Stable CORE foundation, frozen for module development

