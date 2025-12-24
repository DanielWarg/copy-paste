# KRITISKA PROBLEM I PRIVACY SHIELD v2 IMPLEMENTATION

## Problem Identifierade Genom Kodanalys

### 1. ❌ KRITISKT: `is_anonymized=True` returneras även när verification_passed=False

**Fil:** `backend/app/modules/privacy_v2/privacy_v2_service.py:158`

**Problem:**
```python
return PrivacyScrubV2Response(
    ...
    is_anonymized=True,  # Always True if we got here  <-- FEL!
    verification_passed=verification_passed,  # Kan vara False!
    ...
)
```

**Konsekvens:** Om verification_passed=False men vi ändå returnerar is_anonymized=True, så kan draft generation tro att texten är anonymiserad när den inte är det.

**Fix:** `is_anonymized` ska vara `verification_passed and not semantic_risk`

---

### 2. ❌ KRITISKT: Layer 2 verification saknar svenska telefonnummer-format

**Fil:** `backend/app/modules/privacy_v2/layer2_verify.py:27`

**Problem:**
```python
# Check for phone patterns
if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', clean_text):  # Bara amerikanska format!
    failures.append("phone_pattern_detected")
```

**Konsekvens:** Svenska telefonnummer som `08-123 45 67` eller `070-1234567` kommer INTE att detekteras av Layer 2 verification, även om de inte är anonymiserade.

**Fix:** Lägg till svenska telefonnummer-patterns:
- `\b0\d{1,2}[-.\s]?\d{3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b` (svenska format)
- `\b\+46\s?\d{1,2}[-.\s]?\d{3}[-.\s]?\d{2,3}[-.\s]?\d{2,3}\b` (internationellt svenskt)

---

### 3. ❌ PROBLEM: Semantic audit körs även när verification_passed=False

**Fil:** `backend/app/modules/privacy_v2/privacy_v2_service.py:100-102`

**Problem:**
```python
# Layer 3: Semantic audit
receipt_manager.add_step(event_id, "L3", "ok", model_id="ollama/ministral-3b")
semantic_risk, risk_reason = await semantic_audit(clean_text, str(event_id))
```

**Konsekvens:** Om verification_passed=False efter alla retries, så har vi text som INTE är korrekt anonymiserad, men vi kör ändå semantic audit på den. Detta är slöseri med resurser och kan ge missvisande resultat.

**Fix:** Kör semantic audit ENDAST om verification_passed=True, eller sätt semantic_risk=True automatiskt om verification_passed=False.

---

### 4. ❌ PROBLEM: Tester kollar inte att PII faktiskt är borttaget

**Fil:** `scripts/test_full_privacy_v2.py:151`

**Problem:**
```python
assert "[EMAIL" in scrub_data['clean_text'] or "[EMAIL_PREFLIGHT" in scrub_data['clean_text'], \
    "Emails ska vara anonymiserade"
```

**Konsekvens:** Testet passarar även om originalet `john.doe@example.com` fortfarande finns kvar i clean_text, så länge det också finns en `[EMAIL_1]` token någonstans.

**Fix:** Testet ska kolla att originalet INTE finns:
```python
assert "john.doe@example.com" not in scrub_data['clean_text'], "Email ska vara borttaget"
assert "[EMAIL" in scrub_data['clean_text'], "Email ska vara anonymiserad"
```

---

### 5. ❌ PROBLEM: Exception handling kan lämna verification_passed=False utan clean_text

**Fil:** `backend/app/modules/privacy_v2/privacy_v2_service.py:89-98`

**Problem:**
```python
except Exception as e:
    receipt_manager.add_step(event_id, f"L1_attempt_{attempt}", "failed")
    log_privacy_safe(str(event_id), f"L1 anonymization error: {str(e)}")
    if attempt < max_retries:
        continue  # <-- clean_text kan vara från förra iterationen eller tom!
    else:
        raise HTTPException(...)
```

**Konsekvens:** Om anonymizer.anonymize() kraschar på första försöket, så är clean_text fortfarande preflight_text. Om det kraschar på alla försök, så har vi ingen clean_text att returnera.

**Fix:** Sätt clean_text till preflight_text innan loopen, eller hantera exception bättre.

---

### 6. ⚠️ PROBLEM: Layer 0 preflight kan krocka med Layer 1 anonymization

**Fil:** `backend/app/modules/privacy_v2/privacy_v2_service.py:47`

**Problem:**
```python
preflight_text, preflight_metrics = sanitize_preflight(raw_text)
# ...
clean_text = preflight_text  # <-- Skickar preflight_text till anonymizer
clean_text, mapping, is_anonymized = await anonymizer.anonymize(
    clean_text,  # <-- Innehåller redan [EMAIL_PREFLIGHT] tokens
    ...
)
```

**Konsekvens:** Om Layer 0 ersätter emails med `[EMAIL_PREFLIGHT]`, så kommer anonymizer.anonymize() att få text som redan har tokens, vilket kan förvirra den.

**Fix:** Antingen skippa Layer 0, eller se till att anonymizer hanterar preflight-tokens korrekt.

---

### 7. ⚠️ PROBLEM: Receipt steps kan ha felaktiga timestamps

**Fil:** `backend/app/modules/privacy_v2/receipts.py:545-550`

**Problem:**
```python
step = ReceiptStep(
    name=name,
    status=status,
    model_id=model_id,
    started_at=datetime.utcnow().isoformat(),  # <-- Samma som ended_at!
    ended_at=datetime.utcnow().isoformat(),   # <-- Ingen skillnad!
    ...
)
```

**Konsekvens:** Alla steps har samma start och end timestamp, vilket gör det omöjligt att se hur lång tid varje step tog.

**Fix:** Spara start_time när step börjar, end_time när den slutar.

---

## Sammanfattning

**KRITISKA (måste fixas):**
1. `is_anonymized=True` när verification_passed=False
2. Layer 2 saknar svenska telefonnummer-format
3. Semantic audit körs på overifierad text

**VIKTIGA (bör fixas):**
4. Tester kollar inte att PII är borttaget
5. Exception handling kan lämna clean_text i felaktigt tillstånd

**MINOR (nice to have):**
6. Layer 0/1 krock potential
7. Receipt timestamps

