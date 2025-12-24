# CORE Backend Foundation - Komplett Dokumentation

## Innehållsförteckning

1. [Arkitekturöversikt](#arkitekturöversikt)
2. [Startup Sequence](#startup-sequence)
3. [Request Flow](#request-flow)
4. [Core Modules](#core-modules)
5. [Error Handling](#error-handling)
6. [Database](#database)
7. [Logging](#logging)
8. [Security](#security)
9. [API Endpoints](#api-endpoints)
10. [Module Contract](#module-contract)

---

## Arkitekturöversikt

CORE är en minimal, stabil FastAPI-backend som fungerar som fundament för framtida moduler. Den är designad för att:

- **Alltid starta** - Inga kritiska dependencies, DB är optional
- **Vara privacy-safe** - Inga payloads, headers eller PII i logs
- **Vara modulär** - Alla features går i `/modules/*`, CORE ändras inte
- **Vara production-ready** - Security headers, error handling, observability

### Designprinciper

1. **Fail loud, fail early** - Konfigurationsfel stoppar boot omedelbart
2. **Privacy-by-default** - Inga payloads, headers eller PII loggas någonsin
3. **DB-optional** - App startar utan DB, `/ready` visar DB-status
4. **Modulär från dag 1** - CORE är frozen, all ny funktionalitet i moduler

### Filstruktur

```
backend/app/
├── main.py                    # FastAPI app, wire everything
├── core/
│   ├── config.py              # Pydantic Settings (fail-fast)
│   ├── logging.py              # Privacy-safe JSON logging
│   ├── middleware.py           # Request ID, timing, security headers
│   ├── database.py             # SQLAlchemy (optional DB)
│   ├── lifecycle.py            # Startup/shutdown hooks
│   └── errors.py                # Global exception handlers
├── routers/
│   ├── health.py               # GET /health (always 200)
│   ├── ready.py                # GET /ready (200/503 based on DB)
│   └── meta.py                 # GET /meta (optional, behind flag)
└── modules/
    └── example/                # Example module (Module Contract v1)
```

---

## Startup Sequence

Startup-ordningen är **kritisk** och följer denna sekvens:

### 1. Config Loading (`app.core.config`)

**När:** Vid Python import (innan app startar)

**Vad som händer:**
```python
# backend/app/core/config.py
settings = Settings()  # Validerar vid import
```

**Process:**
1. Läser `.env` från repo root (`Path(__file__).parent.parent.parent.parent / ".env"`)
2. Validerar alla fält med Pydantic (fail-fast om fel)
3. Kör `model_post_init()` som validerar CORS (fail-fast om `*` i production)
4. Om något fel → `ValueError` eller `ValidationError` → app startar inte

**Viktigt:**
- Config errors stoppar boot **innan** logging är initierad
- Detta säkerställer att vi inte försöker logga med trasig config
- CORS guard förhindrar `*` i production (security risk)

### 2. Logging Initialization (`app.core.logging`)

**När:** Vid Python import (efter config)

**Vad som händer:**
```python
# backend/app/core/logging.py
logger = setup_logging()  # Körs vid import
```

**Process:**
1. Skapar logger med namn "app"
2. Sätter log level från `settings.log_level`
3. Skapar `StreamHandler` (stdout)
4. Sätter `JSONFormatter` om `LOG_FORMAT=json`
5. Förhindrar propagation till root logger

**Viktigt:**
- Logger är redo **innan** DB init (så vi kan logga DB-init)
- JSON format gör logs parseable för log aggregation
- Privacy-safe från start (ingen PII kan loggas)

### 3. Database Initialization (`app.core.database`)

**När:** I `startup()` hook (om `DATABASE_URL` finns)

**Vad som händer:**
```python
# backend/app/core/lifecycle.py
if settings.database_url:
    init_db(settings.database_url)
```

**Process:**
1. Skapar SQLAlchemy engine med `pool_pre_ping=True`
2. Skapar `SessionLocal` sessionmaker
3. Kör `Base.metadata.create_all()` (backup, Alembic hanterar migrations)
4. **Om ingen DATABASE_URL:** Skippas helt, app startar ändå

**Viktigt:**
- DB är **optional** - app startar utan
- `pool_pre_ping` verifierar connections innan användning
- Engine är global (`engine` variabel) men kan vara `None`

### 4. Migrations (`alembic`)

**När:** I `startup()` hook (efter DB init, om DB finns)

**Vad som händer:**
```python
# backend/app/core/lifecycle.py
alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")
```

**Process:**
1. Läser `alembic.ini` config
2. Kör `alembic upgrade head` (kör alla pending migrations)
3. Om migration failar → loggar error men stoppar **inte** startup
4. Rationale: Migrations kan köras manuellt, app ska starta ändå

**Viktigt:**
- Migrations är **non-blocking** - app startar även om migrations failar
- Detta gör deployment mer robust (migrations kan köras separat)

### 5. Router Registration (`app.main`)

**När:** Vid FastAPI app creation (innan startup hook)

**Vad som händer:**
```python
# backend/app/main.py
app.include_router(health.router)
app.include_router(ready.router)
if settings.enable_meta:
    app.include_router(meta.router)
app.include_router(example_router.router, prefix="/api/v1")
```

**Process:**
1. Registrerar core routers (`/health`, `/ready`)
2. Conditionally registrerar `/meta` (om `ENABLE_META=true`)
3. Registrerar module routers (ex. `/api/v1/example`)

**Viktigt:**
- Routers registreras **innan** startup hook
- Detta säkerställer att endpoints är tillgängliga när app är "ready"

### 6. Middleware Registration (`app.main`)

**När:** Vid FastAPI app creation (innan routers)

**Vad som händer:**
```python
# backend/app/main.py
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(RequestIDMiddleware)
```

**Process:**
1. CORS middleware läggs till först (hanterar preflight requests)
2. RequestIDMiddleware läggs till (genererar ID, timing, security headers)

**Viktigt:**
- Middleware-ordning är viktig (CORS först, sedan custom)
- RequestIDMiddleware måste köras för att sätta `request.state.request_id`

### 7. Exception Handlers (`app.main`)

**När:** Vid FastAPI app creation (efter middleware)

**Vad som händer:**
```python
# backend/app/main.py
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

**Process:**
1. Registrerar handler för HTTPException (4xx, 5xx)
2. Registrerar handler för RequestValidationError (422)
3. Registrerar fallback handler för alla exceptions (500)

**Viktigt:**
- Handlers registreras i **specific → general** ordning
- Alla handlers returnerar konsekvent error-shape med `request_id`

### 8. App Ready

**När:** Efter startup hook körts

**Vad som händer:**
- FastAPI server startar (uvicorn)
- App lyssnar på `0.0.0.0:8000` (eller från `settings.port`)
- `/health` returnerar 200 omedelbart
- `/ready` returnerar 200 (om DB OK eller inte konfigurerad) eller 503 (om DB nere)

---

## Request Flow

När en HTTP-request kommer in går den genom följande pipeline:

### 1. CORS Middleware (FastAPI)

**Vad:** Hanterar CORS preflight requests (OPTIONS)

**Process:**
- Om OPTIONS request → returnerar CORS headers direkt
- Om annan request → lägger till CORS headers i response
- Använder `settings.cors_origins` (validerat att inte vara `*` i production)

**Headers som sätts:**
- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`

### 2. RequestIDMiddleware (Custom)

**Vad:** Genererar request ID, mäter timing, sätter security headers

**Process:**

```python
# backend/app/core/middleware.py
async def dispatch(request, call_next):
    # 1. Generera UUID request_id
    request_id = str(uuid.uuid4())
    
    # 2. Lägg i request.state (tillgänglig för handlers)
    request.state.request_id = request_id
    
    # 3. Starta timer
    start_time = time.time()
    
    # 4. Kör nästa middleware/handler
    try:
        response = await call_next(request)
    except Exception as e:
        # Logga error (privacy-safe)
        logger.error("request_error", extra={...})
        raise
    
    # 5. Beräkna latency
    latency_ms = (time.time() - start_time) * 1000
    
    # 6. Lägg till headers
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"
    
    # 7. Logga request (privacy-safe)
    log_request(logger, request_id, path, method, status_code, latency_ms)
    
    return response
```

**Viktigt:**
- Request ID genereras **tidigt** (innan handler körs)
- Security headers sätts **alltid** (även vid errors)
- Logging sker **efter** response (så vi har status_code)

### 3. Router Handler

**Vad:** Kör endpoint handler (ex. `/health`, `/ready`, `/api/v1/example`)

**Process:**
- FastAPI matchar URL till router
- Kör handler-funktion
- Returnerar response dict (konverteras till JSON av FastAPI)

**Exempel:**
```python
# backend/app/routers/health.py
@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}  # FastAPI konverterar till JSON
```

### 4. Exception Handling (om error)

**Vad:** Om exception kastas, hanteras av global handlers

**Process:**

**Scenario A: HTTPException (4xx, 5xx)**
```python
# backend/app/core/errors.py
async def http_exception_handler(request, exc):
    # Läser request_id från request.state
    request_id = get_request_id(request)
    
    # Skapar error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": "Request failed" if not DEBUG else exc.detail,
                "request_id": request_id
            }
        }
    )
```

**Scenario B: RequestValidationError (422)**
```python
async def validation_exception_handler(request, exc):
    # Samma process, men code="validation_error"
    # Message: "Invalid request" (production) eller detaljerad (debug)
```

**Scenario C: General Exception (500)**
```python
async def general_exception_handler(request, exc):
    # Loggar exception (privacy-safe)
    logger.error("unhandled_exception", extra={...})
    
    # Returnerar generisk error (production) eller detaljerad (debug)
    # ALDRIG stacktrace eller filvägar i production
```

**Viktigt:**
- Alla errors inkluderar `request_id` för traceability
- Production mode: generiska meddelanden, inga stacktraces
- Debug mode: mer detaljer (men fortfarande inga headers/bodies/PII)

### 5. Response Return

**Vad:** Response skickas tillbaka till klient

**Process:**
- FastAPI konverterar response dict till JSON
- Middleware har redan satt headers (X-Request-Id, security headers)
- Response skickas via HTTP

---

## Core Modules

### 1. Config (`app.core.config`)

**Syfte:** Centraliserad konfiguration med fail-fast validation

**Implementation:**

```python
class Settings(BaseSettings):
    # App metadata
    app_name: str = "Copy/Paste Core"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database (optional)
    database_url: Optional[str] = None
    db_health_timeout_seconds: float = 2.0
    
    # Security
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_sample_rate: float = 1.0
    
    # Features
    enable_meta: bool = False
    
    def model_post_init(self, __context: Any) -> None:
        # CORS sanity guard
        if not self.debug and "*" in self.cors_origins:
            raise ValueError("CORS cannot be '*' in production")
```

**Viktiga detaljer:**

1. **Fail-fast validation:**
   - Pydantic validerar vid import
   - Om fel → `ValidationError` → app startar inte
   - Detta säkerställer att trasig config upptäcks tidigt

2. **CORS sanity guard:**
   - `model_post_init()` körs efter Settings init
   - Kontrollerar att `cors_origins` inte innehåller `"*"` i production
   - Om `*` hittas → `ValueError` → app startar inte
   - Detta förhindrar oavsiktlig "wide-open" CORS i production

3. **Env file loading:**
   - Läser från `.env` i repo root
   - `env_ignore_empty=True` → tomma värden ignoreras
   - `case_sensitive=False` → `DATABASE_URL` och `database_url` fungerar båda

### 2. Logging (`app.core.logging`)

**Syfte:** Privacy-safe structured JSON logging

**Implementation:**

**JSONFormatter:**
```python
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": ...,
            "level": ...,
            "logger": ...,
            "message": ...
        }
        
        # Lägg till request fields om de finns
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        # ... path, method, status_code, latency_ms
        
        # Filtrera bort förbjudna nycklar från extra_data
        if hasattr(record, "extra_data"):
            safe_extra = {
                k: v for k, v in extra.items()
                if k.lower() not in _FORBIDDEN_LOG_KEYS
            }
            log_data.update(safe_extra)
        
        # Assert privacy-safe
        _assert_privacy_safe(log_data)
        
        return json.dumps(log_data)
```

**Privacy-safe enforcement:**

1. **Forbidden keys:**
   ```python
   _FORBIDDEN_LOG_KEYS = frozenset({
       "authorization", "cookie", "user-agent", "body",
       "payload", "headers", "query_params", "ip", ...
   })
   ```

2. **Assertion check:**
   ```python
   def _assert_privacy_safe(log_data):
       keys_lower = {k.lower() for k in log_data.keys()}
       forbidden_found = keys_lower & _FORBIDDEN_LOG_KEYS
       if forbidden_found:
           raise AssertionError(f"Privacy violation: {forbidden_found}")
   ```

3. **Sampling:**
   ```python
   def should_log() -> bool:
       return random.random() < settings.log_sample_rate
   ```

**Viktiga detaljer:**

- **Inga payloads:** Request/response bodies loggas aldrig
- **Inga headers:** Authorization, Cookie, User-Agent loggas aldrig
- **Inga PII:** IP-adresser, tokens, secrets loggas aldrig
- **Endast metadata:** request_id, path, method, status_code, latency_ms
- **Sampling:** `LOG_SAMPLE_RATE` styr hur många requests som loggas (1.0 = alla, 0.1 = 10%)

### 3. Middleware (`app.core.middleware`)

**Syfte:** Request ID generation, timing, security headers

**Implementation:**

```python
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 1. Generera UUID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 2. Timer
        start_time = time.time()
        
        # 3. Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Logga error (privacy-safe)
            logger.error("request_error", extra={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "error": str(e)  # Bara error message, inte stacktrace
            })
            raise
        
        # 4. Beräkna latency
        latency_ms = (time.time() - start_time) * 1000
        
        # 5. Headers
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"] = "no-store"
        
        # 6. Logga request
        log_request(logger, request_id, path, method, status_code, latency_ms)
        
        return response
```

**Viktiga detaljer:**

- **Request ID:** Genereras tidigt, tillgänglig i `request.state` för alla handlers
- **Timing:** Mäter total request time (inklusive DB queries, external calls)
- **Security headers:** Sätts **alltid**, även vid errors (middleware körs även vid exceptions)
- **Privacy-safe logging:** Loggar endast metadata, inga bodies/headers

### 4. Database (`app.core.database`)

**Syfte:** SQLAlchemy setup med optional DB support

**Implementation:**

**Initialization:**
```python
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None

def init_db(database_url: str):
    global engine, SessionLocal
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verifiera connections innan användning
        echo=False
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)  # Backup, Alembic hanterar migrations
```

**Health Check:**
```python
def _check_db_health_sync() -> bool:
    """Synchronous check (runs in thread)."""
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False

async def check_db_health() -> bool:
    """Async wrapper with timeout."""
    if not engine:
        return False
    try:
        # Run sync check in thread with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(_check_db_health_sync),
            timeout=settings.db_health_timeout_seconds  # Default 2.0s
        )
        return result
    except (asyncio.TimeoutError, Exception):
        return False
```

**Viktiga detaljer:**

- **Optional DB:** `engine` kan vara `None` → app startar ändå
- **Timeout:** Health check har hård timeout (2s default) → blockerar inte event loop
- **Thread safety:** Sync SQLAlchemy körs i `asyncio.to_thread()` → non-blocking
- **GDPR compliance:** `ServiceState` table har inga content fields

### 5. Lifecycle (`app.core.lifecycle`)

**Syfte:** Startup/shutdown hooks

**Implementation:**

**Startup:**
```python
async def startup():
    logger.info("app_startup", extra={"version": settings.app_version})
    
    # Initialize DB if configured
    if settings.database_url:
        logger.info("db_init_start")
        init_db(settings.database_url)
        
        # Run migrations
        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("db_migrations_complete")
        except Exception as e:
            logger.error("db_migration_failed", extra={"error": str(e)})
            # Don't fail startup - migrations might be run manually
    else:
        logger.info("db_not_configured")
    
    logger.info("app_startup_complete")
```

**Shutdown:**
```python
async def shutdown():
    logger.info("app_shutdown_start")
    
    # Close DB connections
    if engine:
        engine.dispose()
        logger.info("db_connections_closed")
    
    logger.info("app_shutdown_complete")
```

**Viktiga detaljer:**

- **Non-blocking migrations:** Migration failures stoppar inte startup
- **Graceful shutdown:** Stänger DB connections korrekt
- **Logging:** Alla steg loggas (privacy-safe)

### 6. Errors (`app.core.errors`)

**Syfte:** Global exception handlers för konsekvent error-shape

**Implementation:**

**Error Shape:**
```json
{
  "error": {
    "code": "validation_error" | "http_error" | "internal_error",
    "message": "Human-readable message",
    "request_id": "uuid-here",
    "debug": "..."  // Only if DEBUG=true
  }
}
```

**Handlers:**

1. **HTTPException Handler:**
   ```python
   async def http_exception_handler(request, exc):
       request_id = get_request_id(request)
       
       if settings.debug:
           message = exc.detail
       else:
           message = "Request failed"  # Generic
       
       return JSONResponse(
           status_code=exc.status_code,
           content={
               "error": {
                   "code": "http_error",
                   "message": message,
                   "request_id": request_id
               }
           }
       )
   ```

2. **Validation Error Handler:**
   ```python
   async def validation_exception_handler(request, exc):
       # Same structure, but code="validation_error"
       # Message: "Invalid request" (production) eller detaljerad (debug)
   ```

3. **General Exception Handler:**
   ```python
   async def general_exception_handler(request, exc):
       # Logga exception (privacy-safe)
       logger.error("unhandled_exception", extra={...})
       
       # Returnera generisk error (production)
       # ALDRIG stacktrace eller filvägar
   ```

**Viktiga detaljer:**

- **Request ID:** Alla errors inkluderar `request_id` från `request.state`
- **Production mode:** Generiska meddelanden, inga stacktraces
- **Debug mode:** Mer detaljer (men fortfarande inga headers/bodies/PII)
- **Privacy-safe:** Exception messages filtreras, inga interna detaljer läcker

---

## Error Handling

### Error Flow

```
Request → Handler → Exception
                    ↓
            Exception Handler (global)
                    ↓
            JSONResponse med error-shape
                    ↓
            Middleware (sätter headers)
                    ↓
            Response till klient
```

### Error Codes

- **`validation_error`** (422): Request validation failed (Pydantic)
- **`http_error`** (4xx, 5xx): HTTPException från FastAPI/Starlette
- **`internal_error`** (500): Unhandled exception (fallback)

### Production vs Debug

**Production (`DEBUG=false`):**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request",
    "request_id": "abc-123"
  }
}
```

**Debug (`DEBUG=true`):**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "request_id": "abc-123",
    "debug": "Validation failed: 1 error(s)"
  }
}
```

**Viktigt:** Även i debug mode läcker vi **aldrig** headers, bodies, eller PII.

---

## Database

### Optional DB Architecture

CORE är designad för att fungera **med eller utan** PostgreSQL:

**Utan DB (`DATABASE_URL` saknas):**
- App startar normalt
- `/ready` returnerar `200 {"status": "ready", "db": "not_configured"}`
- Inga DB-queries körs

**Med DB (`DATABASE_URL` satt):**
- App startar, initierar DB connection
- `/ready` returnerar `200 {"status": "ready"}` om DB OK
- `/ready` returnerar `503` om DB nere (med timeout)

### Health Check Timeout

**Problem:** SQLAlchemy `connect()` kan blockera länge om DB är nere

**Lösning:**
```python
async def check_db_health() -> bool:
    # Run sync SQLAlchemy in thread
    result = await asyncio.wait_for(
        asyncio.to_thread(_check_db_health_sync),
        timeout=settings.db_health_timeout_seconds  # 2.0s default
    )
    return result
```

**Viktigt:**
- Timeout är **hård** - `asyncio.wait_for()` kastar `TimeoutError` efter 2s
- Sync SQLAlchemy körs i thread → blockerar inte event loop
- Vid timeout → returnerar `False` → `/ready` returnerar 503

### ServiceState Table

**Minimal table för GDPR compliance:**
```python
class ServiceState(Base):
    __tablename__ = "service_state"
    id = Column(Integer, primary_key=True)
    service_name = Column(String, unique=True)
    last_heartbeat = Column(DateTime)
    # NO content fields - GDPR compliance
```

**Användning:**
- Framtida moduler kan använda denna för heartbeat/status
- Inga payloads, inga PII, inga content fields

---

## Logging

### Privacy-Safe Logging

**Vad som loggas:**
- `request_id` - UUID för traceability
- `path` - Request path (ex. `/api/v1/example`)
- `method` - HTTP method (GET, POST, etc.)
- `status_code` - HTTP status code (200, 404, 500, etc.)
- `latency_ms` - Request latency i millisekunder

**Vad som ALDRIG loggas:**
- Request/response bodies
- Headers (Authorization, Cookie, User-Agent, etc.)
- Query parameters
- IP addresses
- Tokens, secrets, passwords

### Log Format

**JSON Format (default):**
```json
{
  "timestamp": "2025-12-23 19:06:33,242",
  "level": "INFO",
  "logger": "app",
  "message": "http_request",
  "request_id": "abc-123-def-456",
  "path": "/api/v1/example",
  "method": "GET",
  "status_code": 200,
  "latency_ms": 12.34
}
```

**Text Format (om `LOG_FORMAT=text`):**
```
2025-12-23 19:06:33,242 - app - INFO - http_request
```

### Sampling

**Sampling rate:** `LOG_SAMPLE_RATE` (default 1.0 = log allt)

**Användning:**
```python
def should_log() -> bool:
    return random.random() < settings.log_sample_rate

def log_request(...):
    if not should_log():
        return  # Skip logging
    # ... log request
```

**Exempel:**
- `LOG_SAMPLE_RATE=1.0` → Loggar alla requests (100%)
- `LOG_SAMPLE_RATE=0.1` → Loggar 10% av requests
- `LOG_SAMPLE_RATE=0.01` → Loggar 1% av requests

**Användning:** För hög trafik kan sampling minska log-volym utan att förlora observability.

---

## Security

### Security Headers

Alla responses inkluderar dessa headers (sätts av middleware):

- **`X-Content-Type-Options: nosniff`** - Förhindrar MIME-sniffing
- **`X-Frame-Options: DENY`** - Förhindrar clickjacking
- **`X-XSS-Protection: 1; mode=block`** - XSS protection
- **`Referrer-Policy: no-referrer`** - Ingen referrer information
- **`Permissions-Policy: geolocation=(), microphone=(), camera=()`** - Inga permissions
- **`Cache-Control: no-store`** - Inga cached responses

### CORS Guard

**Problem:** Wide-open CORS (`*`) är säkerhetsrisk i production

**Lösning:**
```python
def model_post_init(self, __context: Any) -> None:
    if not self.debug and "*" in self.cors_origins:
        raise ValueError(
            "CORS origins cannot contain '*' in production (debug=False). "
            "This is a security risk."
        )
```

**Beteende:**
- Production (`DEBUG=false`): `*` i `CORS_ORIGINS` → `ValueError` → app startar inte
- Debug (`DEBUG=true`): `*` tillåtet (för lokal utveckling)

### Request ID

**Syfte:** Traceability för debugging och observability

**Implementation:**
- Genereras av middleware (UUID v4)
- Läggs i `request.state.request_id`
- Inkluderas i alla logs
- Inkluderas i alla error responses
- Returneras som `X-Request-Id` header

**Användning:**
- Debugging: Hitta alla logs för en specifik request
- Observability: Spåra request genom hela systemet
- Error tracking: Korrelera errors med requests

---

## API Endpoints

### `GET /health`

**Syfte:** Process alive check (Kubernetes liveness probe)

**Beteende:**
- Alltid returnerar `200 OK`
- Ingen DB-check
- Ingen business logic

**Response:**
```json
{
  "status": "ok"
}
```

**Användning:**
- Kubernetes liveness probe
- Load balancer health check
- Monitoring systems

### `GET /ready`

**Syfte:** Readiness check (Kubernetes readiness probe)

**Beteende:**

**Scenario A: No DB configured**
```json
{
  "status": "ready",
  "db": "not_configured"
}
```
Status: `200 OK`

**Scenario B: DB configured and healthy**
```json
{
  "status": "ready"
}
```
Status: `200 OK`

**Scenario C: DB configured but down**
```json
{
  "detail": {
    "status": "db_down",
    "message": "Database health check failed"
  }
}
```
Status: `503 Service Unavailable`

**Timeout:** Health check respekterar `DB_HEALTH_TIMEOUT_SECONDS` (default 2.0s)

**Användning:**
- Kubernetes readiness probe
- Deployment pipelines
- Service mesh health checks

### `GET /meta` (Optional)

**Syfte:** Version/build info (endast om `ENABLE_META=true`)

**Beteende:**
- Registreras endast om `settings.enable_meta == True`
- Default: `false` (endpoint finns inte)

**Response:**
```json
{
  "version": "2.0.0",
  "build": "local",
  "commit": "unknown"
}
```

**Användning:**
- Deployment verification
- Version tracking
- Debugging

**Viktigt:** Disabled by default för att minimera information leakage.

### `GET /api/v1/example`

**Syfte:** Example module endpoint (demonstrerar Module Contract v1)

**Beteende:**
- Kräver query parameter `q`
- Returnerar status + module identifier

**Request:**
```
GET /api/v1/example?q=test
```

**Response:**
```json
{
  "status": "ok",
  "module": "example",
  "query": "test"
}
```

**Error (om `q` saknas):**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request",
    "request_id": "abc-123"
  }
}
```
Status: `422 Unprocessable Entity`

---

## Module Contract

### Module Structure

```
backend/app/modules/{module_name}/
├── __init__.py
├── router.py          # FastAPI router
├── service.py         # Business logic (optional)
├── models.py          # SQLAlchemy models (optional)
└── README.md          # Module documentation
```

### Module Requirements

1. **No Core Dependencies:**
   - Moduler får **inte** importera från `app.core` utom `config` och `logging`
   - Rationale: CORE är frozen, moduler ska inte bero på interna CORE-detaljer

2. **Router Registration:**
   ```python
   # In app/main.py
   from app.modules.example import router as example_router
   app.include_router(example_router.router, prefix="/api/v1", tags=["modules"])
   ```

3. **Privacy-Safe Logging:**
   ```python
   from app.core.logging import logger
   
   logger.info("module_action", extra={
       "module": "example",
       "action": "process"
   })
   ```

4. **Error Handling:**
   - Moduler använder FastAPI exceptions (`HTTPException`, `RequestValidationError`)
   - Global exception handlers hanterar dem automatiskt

5. **Database Models:**
   - Moduler definierar sina egna models
   - Migrations i `alembic/versions/`
   - Använder `Base` från `app.core.database`

### Example Module

**Implementation:**
```python
# backend/app/modules/example/router.py
from fastapi import APIRouter, Query
from app.core.logging import logger

router = APIRouter()

@router.get("/example")
async def example(q: str = Query(...)) -> dict:
    logger.info("example_module_called", extra={
        "module": "example",
        "endpoint": "/api/v1/example"
    })
    
    return {
        "status": "ok",
        "module": "example",
        "query": q
    }
```

**Registration:**
```python
# backend/app/main.py
from app.modules.example import router as example_router
app.include_router(example_router.router, prefix="/api/v1", tags=["modules"])
```

---

## Data Flow Diagrams

### Startup Flow

```
Python Import
    ↓
Config Loading (fail-fast)
    ↓
Logging Initialization
    ↓
FastAPI App Creation
    ↓
Middleware Registration
    ↓
Router Registration
    ↓
Exception Handler Registration
    ↓
Startup Hook
    ↓
  ├─→ DB Init? (if DATABASE_URL)
  │     ↓
  │   Migrations (non-blocking)
  │     ↓
  └─→ App Ready
```

### Request Flow

```
HTTP Request
    ↓
CORS Middleware
    ↓
RequestIDMiddleware
    ├─→ Generate UUID
    ├─→ Start Timer
    └─→ call_next()
        ↓
    Router Handler
        ├─→ Success → Response
        └─→ Exception → Exception Handler
            ↓
        Error Response
    ↓
RequestIDMiddleware (cont.)
    ├─→ Calculate Latency
    ├─→ Set Headers
    └─→ Log Request
    ↓
HTTP Response
```

### Error Flow

```
Exception in Handler
    ↓
Exception Handler (global)
    ├─→ Get request_id
    ├─→ Log error (privacy-safe)
    └─→ Create error response
        ↓
    JSONResponse
        ↓
Middleware (sätter headers)
        ↓
HTTP Response (med error-shape)
```

---

## Testing

### Smoke Tests (`make test`)

**Scenario A: No DB configured**
1. Startar backend utan `DATABASE_URL`
2. Verifierar `/health` → 200
3. Verifierar `/ready` → 200 med `{"status": "ready", "db": "not_configured"}`

**Scenario B: DB up**
1. Startar full stack (PostgreSQL + Backend)
2. Verifierar `/health` → 200
3. Verifierar `/ready` → 200 med `{"status": "ready"}`
4. Verifierar `/api/v1/example?q=test` → 200
5. Verifierar `/api/v1/example` (utan query) → 422 med error-shape

**Scenario C: DB down**
1. Stoppar PostgreSQL men behåller backend
2. Verifierar `/ready` → 503 inom timeout (< 4 sekunder)
3. Verifierar response innehåller `{"detail": {"status": "db_down"}}`

### Manual Smoke Tests (`make smoke`)

Kör curl mot alla endpoints och visar responses:
- `GET /health`
- `GET /ready`
- `GET /api/v1/example?q=test`
- `GET /api/v1/example` (validation error)

### Log Privacy Check (`scripts/check_logs.py`)

Verifierar att logs inte innehåller förbjudna nycklar:
- Läser Docker logs
- Kontrollerar varje log-rad för forbidden keys
- Assertar att inga violations hittas

---

## Verifiering

### Lokal Verifiering (utan Docker)

```bash
# Test config loading
cd backend
python3 -c "from app.core.config import settings; print('✅ Config OK')"

# Test logging
python3 -c "from app.core.logging import logger; logger.info('test'); print('✅ Logging OK')"

# Test app loading
python3 -c "from app.main import app; print(f'✅ App OK: {app.title}')"
```

### Docker Verifiering

```bash
# Start services
make up

# Check health
make health

# Run smoke tests
make test

# Check logs
make logs

# Manual smoke
make smoke
```

---

## CORE v1 Freeze

**CORE v1.0.0** är frozen och ska inte ändras utan ADR (Architecture Decision Record) eller PR review.

**Policy:**
- All ny funktionalitet måste gå i `/modules/*`
- CORE-ändringar kräver explicit godkännande
- CORE anses stabil och production-ready

**Release Tag:**
```bash
git tag -a core-v1.0.0 -m "CORE v1.0.0 - Stable foundation"
git push origin core-v1.0.0
```

---

## Sammanfattning

CORE är en minimal, stabil backend som:

1. **Startar alltid** - Inga kritiska dependencies, DB är optional
2. **Är privacy-safe** - Inga payloads, headers eller PII i logs
3. **Har konsekvent error handling** - Alla errors har samma shape med request_id
4. **Har security headers** - Alltid satta, även vid errors
5. **Har quality gates** - Ruff, mypy, pre-commit, CI
6. **Är modulär** - CORE är frozen, all ny funktionalitet i moduler
7. **Är production-ready** - Docker, health checks, observability

CORE är redo för modulutveckling. Alla framtida features ska byggas som moduler enligt Module Contract v1.
