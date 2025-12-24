# Example Module

Reference implementation demonstrating **Module Contract v1**.

## Purpose

This module serves as a template and proof-of-concept for how future modules should be structured according to the Module Contract v1 specification.

## Structure

```
backend/app/modules/example/
├── __init__.py
├── router.py          # FastAPI router
└── README.md          # Module documentation
```

## Endpoint

### `GET /api/v1/example`

Returns a simple status response.

**Response:**
```json
{
  "status": "ok",
  "module": "example"
}
```

## Module Contract Compliance

- ✅ **No Core Dependencies**: Only imports from `app.core.logging` and `app.core.config` (via logging)
- ✅ **Router Registration**: Registered in `app/main.py` with prefix `/api/v1`
- ✅ **Privacy-Safe Logging**: Uses structured logging from `app.core.logging` with no PII
- ✅ **No DB Requirements**: No database models or migrations
- ✅ **Simple Error Handling**: Uses FastAPI's standard exception handling

## Logging

The module logs events using the core logging system:

```python
logger.info(
    "example_module_called",
    extra={
        "module": "example",
        "endpoint": "/api/v1/example",
    },
)
```

All logging is privacy-safe (no headers, no body, no PII).

## Testing

The module is tested as part of the core test suite via `make test`.

