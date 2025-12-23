#!/usr/bin/env python3
# scripts/test_suite_v2.py
"""
Copy/Paste - Full integration smoke suite (no pytest, no python -c).
Run against a running backend.

Usage:
  python3 scripts/test_suite_v2.py

Optional env:
  API_BASE=http://localhost:8000
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


API_BASE = os.getenv("API_BASE", "http://localhost:8000").rstrip("/")


@dataclass
class HttpResult:
    status: int
    body_text: str
    json: Optional[Dict[str, Any]] = None


def _http_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 20) -> HttpResult:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = Request(url=url, data=data, headers=headers, method=method.upper())
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            parsed = None
            try:
                parsed = json.loads(body) if body.strip() else None
            except Exception:
                parsed = None
            return HttpResult(status=getattr(resp, "status", 200), body_text=body, json=parsed)
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        parsed = None
        try:
            parsed = json.loads(body) if body.strip() else None
        except Exception:
            parsed = None
        return HttpResult(status=e.code, body_text=body, json=parsed)
    except URLError as e:
        raise RuntimeError(f"Network error calling {url}: {e}") from e


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def wait_for_health(max_seconds: int = 20) -> None:
    start = time.time()
    while True:
        r = _http_json("GET", f"{API_BASE}/health", payload=None, timeout=5)
        if r.status == 200:
            print("✅ health ok")
            return
        if time.time() - start > max_seconds:
            raise AssertionError(f"health not ready after {max_seconds}s. last_status={r.status} body={r.body_text[:200]}")
        time.sleep(1)


def ingest_text(value: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    payload = {
        "input_type": "text",
        "value": value,
        "metadata": metadata or {},
    }
    r = _http_json("POST", f"{API_BASE}/api/v1/ingest", payload=payload)
    _assert(r.status in (200, 201), f"ingest failed status={r.status} body={r.body_text[:500]}")
    _assert(isinstance(r.json, dict), f"ingest returned non-json: {r.body_text[:200]}")
    event_id = r.json.get("event_id")
    _assert(event_id, f"ingest missing event_id. json={_pretty(r.json)}")
    print(f"✅ ingest ok event_id={event_id}")
    return str(event_id)


def scrub_v2(event_id: str, production_mode: bool = False, max_retries: int = 2) -> Dict[str, Any]:
    payload = {
        "event_id": event_id,
        "production_mode": production_mode,
        "max_retries": max_retries,
    }
    r = _http_json("POST", f"{API_BASE}/api/v1/privacy/scrub_v2", payload=payload, timeout=60)
    _assert(r.status in (200, 400), f"scrub_v2 unexpected status={r.status} body={r.body_text[:500]}")
    _assert(isinstance(r.json, dict), f"scrub_v2 returned non-json: {r.body_text[:200]}")
    # In production_mode=True the endpoint may intentionally 400 on gated results.
    return r.json


def generate_draft(event_id: str, clean_text: str, production_mode: bool, approval_token: Optional[str]) -> HttpResult:
    payload: Dict[str, Any] = {
        "event_id": event_id,
        "clean_text": clean_text,
        "production_mode": production_mode,
    }
    if approval_token is not None:
        payload["approval_token"] = approval_token

    return _http_json("POST", f"{API_BASE}/api/v1/draft/generate", payload=payload, timeout=120)


def _find_l3_steps(scrub_data: Dict[str, Any]) -> Tuple[int, int]:
    receipt = scrub_data.get("receipt") or {}
    steps = receipt.get("steps") or []
    l3 = [s for s in steps if "L3" in str(s.get("name", ""))]
    return len(steps), len(l3)


def test_scrub_v2_receipt_has_l3() -> None:
    print("\n=== test_scrub_v2_receipt_has_l3 ===")
    eid = ingest_text("Det här är en neutral text utan personuppgifter.", {"test": "scrub_v2_receipt"})
    scrub = scrub_v2(eid, production_mode=False, max_retries=1)

    # Basic shape checks
    _assert("clean_text" in scrub, f"scrub_v2 missing clean_text: {_pretty(scrub)}")
    _assert("receipt" in scrub, f"scrub_v2 missing receipt: {_pretty(scrub)}")

    steps_count, l3_count = _find_l3_steps(scrub)
    _assert(steps_count > 0, f"receipt.steps empty: {_pretty(scrub.get('receipt'))}")
    _assert(l3_count > 0, f"❌ No L3 step found in receipt.steps. receipt={_pretty(scrub.get('receipt'))}")

    print(f"✅ receipt ok steps={steps_count}, l3_steps={l3_count}")


def test_semantic_risk_requires_approval() -> Tuple[str, Dict[str, Any]]:
    print("\n=== test_semantic_risk_requires_approval ===")
    # This text is intentionally "semantic leak"-y, even if tokens exist.
    # It should trigger semantic_risk (or at least approval_required).
    leak_text = "[PERSON_A] är VD för Acme Corporation, ett unikt företag. [PERSON_A] vann Nobelpriset i fysik 2023."
    eid = ingest_text(leak_text, {"test": "semantic_risk"})

    scrub = scrub_v2(eid, production_mode=False, max_retries=2)
    _assert("approval_required" in scrub, f"scrub_v2 missing approval_required: {_pretty(scrub)}")
    _assert("semantic_risk" in scrub, f"scrub_v2 missing semantic_risk: {_pretty(scrub)}")

    approval_required = bool(scrub.get("approval_required"))
    approval_token = scrub.get("approval_token")

    _assert(approval_required is True, f"Expected approval_required=true. got={approval_required}. scrub={_pretty(scrub)}")
    _assert(isinstance(approval_token, str) and len(approval_token) >= 16, f"Expected approval_token. got={approval_token}")

    steps_count, l3_count = _find_l3_steps(scrub)
    _assert(l3_count > 0, f"Expected L3 step for semantic audit. receipt={_pretty(scrub.get('receipt'))}")

    print(f"✅ semantic gate ok semantic_risk={scrub.get('semantic_risk')} approval_required={approval_required}")
    return eid, scrub


def test_draft_is_blocked_without_token(eid: str, scrub: Dict[str, Any]) -> None:
    print("\n=== test_draft_is_blocked_without_token ===")
    clean_text = scrub.get("clean_text") or ""
    _assert(clean_text.strip() != "", "clean_text is empty")

    # Attempt without approval token should be blocked (403/400 expected).
    r = generate_draft(eid, clean_text, production_mode=False, approval_token=None)
    _assert(r.status in (400, 403), f"Expected blocked draft without token. got status={r.status} body={r.body_text[:500]}")
    print(f"✅ draft blocked without token (status={r.status})")


def test_draft_gate_passes_with_token(eid: str, scrub: Dict[str, Any]) -> None:
    print("\n=== test_draft_gate_passes_with_token ===")
    clean_text = scrub.get("clean_text") or ""
    token = scrub.get("approval_token")
    _assert(token, "Missing approval_token in scrub result")

    r = generate_draft(eid, clean_text, production_mode=False, approval_token=token)

    # Two acceptable outcomes:
    # 1) Draft succeeds (200) if OpenAI key is configured.
    # 2) Gate passes, then it fails later due to provider/config (commonly 500/502/400 with provider error).
    #    In that case we still confirm it's NOT the "missing/invalid token" block.
    if r.status == 200:
        _assert(isinstance(r.json, dict), f"Expected json draft response. body={r.body_text[:200]}")
        # Check for draft response fields (our API returns 'text' and 'citations')
        draft_fields = r.json.get("text") or r.json.get("draft") or r.json.get("content")
        _assert(draft_fields, f"Draft response missing content fields: {_pretty(r.json)}")
        print("✅ draft generated successfully with token")
        return

    # If not 200, ensure it isn't blocked by token validation.
    blocked_markers = ["Invalid or expired approval_token", "approval_token", "403", "forbidden", "gated"]
    lower = (r.body_text or "").lower()
    _assert(
        not any(m.lower() in lower for m in blocked_markers),
        f"Still looks like token block even with token. status={r.status} body={r.body_text[:500]}",
    )
    print(f"✅ gate passed with token (status={r.status}). Non-200 likely due to external provider/config.")


def main() -> int:
    print(f"Running Copy/Paste suite against: {API_BASE}")
    try:
        wait_for_health()

        test_scrub_v2_receipt_has_l3()

        eid, scrub = test_semantic_risk_requires_approval()
        test_draft_is_blocked_without_token(eid, scrub)
        test_draft_gate_passes_with_token(eid, scrub)

        print("\n✅ ALL TESTS PASSED")
        return 0

    except AssertionError as e:
        print("\n❌ TEST FAILED")
        print(str(e))
        import traceback
        traceback.print_exc()
        return 2
    except Exception as e:
        print("\n❌ ERROR")
        print(str(e))
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

