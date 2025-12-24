# MCP (Model Context Protocol) Compatibility

## Overview

Copy/Paste provides MCP-compatible endpoints for tool-oriented integration. This adapter layer demonstrates MCP principles (stable contracts, adapters, tool-oriented interface) without modifying core system behavior.

## Available Tools

### `ingest`

Ingests source data (URL, text, or PDF) and returns an event ID.

**Endpoint:** `POST /api/v1/mcp/ingest`

**Request:**
```json
{
  "tool": "ingest",
  "input_type": "url" | "text" | "pdf",
  "value": "https://example.com" | "raw text content" | "base64-encoded PDF",
  "metadata": {},
  "correlation_id": "optional-trace-id"
}
```

**Response (success):**
```json
{
  "ok": true,
  "event_id": "uuid-v4",
  "error": null
}
```

**Response (failure):**
```json
{
  "ok": false,
  "event_id": null,
  "error": "Error message"
}
```

## Why Scrub and Generate Draft Are Not MCP Tools (v1)

Scrub and generate_draft are intentionally not exposed as MCP tools in v1, as they require stronger guarantees around privacy state and execution context. These operations involve:

- Privacy state verification (is_anonymized checks)
- Production Mode enforcement
- External API security gates
- Multi-step workflows with state dependencies

Exposing these as simple MCP tools would require additional context management and state tracking that goes beyond the v1 scope of ingestion-only tools.

## MCP Compatibility Principles

**Stable contracts:** Pydantic models ensure type safety and validation at the API boundary.

**Tool-like endpoints:** `/api/v1/mcp/ingest` follows MCP tool pattern with explicit `tool` identifier and `ok/error` response structure.

**Adapter-based integration:** The MCP layer is a thin wrapper that reuses existing ingestion logic (`create_event`, `store_event`). No duplication, no parallel pipelines.

**No hidden state:** All state is explicit in requests/responses. No global backend state, no hidden context.

## Implementation Details

The MCP adapter (`backend/app/modules/ingestion/mcp_adapter.py`) is a thin wrapper that:

1. Validates `tool == "ingest"` (v1 limitation)
2. Calls `create_event()` - same function used by `/api/v1/ingest`
3. Calls `store_event()` - same function used by `/api/v1/ingest`
4. Returns `MCPToolResponse` with explicit success/failure structure

Both `/api/v1/ingest` and `/api/v1/mcp/ingest` use identical internal functions, ensuring consistent behavior and no code duplication.

## Security & GDPR

All existing security and GDPR guarantees apply to MCP endpoints:

- No new persistence of raw text or PII
- Same validation rules
- Same error handling
- Same privacy-safe logging
- Rate limiting applies automatically (via middleware)

## Versioning

MCP v1 supports only the `ingest` tool. Future versions may add additional tools (e.g., `scrub`, `generate_draft`) as the protocol evolves and security guarantees are strengthened.

