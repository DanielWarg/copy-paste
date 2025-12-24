# Privacy Shield v2 - Testinstruktioner

## Förberedelser

1. **Starta Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Verifiera att endpoints finns:**
```bash
curl http://localhost:8000/docs
# Öppna i webbläsare och kontrollera att /api/v1/privacy/scrub_v2 finns
```

## Kör Tester

### Snabbtest (4 tester)
```bash
python3 scripts/test_privacy_v2.py
```

### Omfattande A-Z tester (13 tester)
```bash
python3 scripts/test_full_privacy_v2.py
```

### Alla tester (inkl. audio)
```bash
./scripts/run_all_tests.sh
```

## Testscenarier

### A. Clean Input
- Text utan PII
- Förväntat: verification_passed=true, semantic_risk=false

### B. Email Patterns
- Många email-varianter
- Förväntat: Alla emails anonymiserade

### C. Phone Patterns
- Svenska + internationella telefonnummer
- Förväntat: Alla telefonnummer anonymiserade

### D. Personnummer/SSN
- Personnummer i olika format
- Förväntat: Personnummer anonymiserade

### E. Combined PII
- Email + phone + namn kombinerat
- Förväntat: All PII anonymiserad

### F. Semantic Leaks
- Identifierbar kontext (Nobelpris, unika roller)
- Förväntat: semantic_risk kan vara true, approval_required om risk

### G. Production Mode Hard Stop
- PII i Production Mode
- Förväntat: HTTP 400 hard stop

### H. Approval Token Flow
- Gated event med approval token
- Förväntat: Draft genereras med token

### I. Draft With/Without Token
- Testa draft generation med och utan token
- Förväntat: Blockerad utan token om gated, fungerar med token

### J. Receipt Verification
- Kontrollera receipt-struktur
- Förväntat: Korrekt receipt med steps, flags, hash

### K. Status Store Persistence
- Testa att status sparas mellan requests
- Förväntat: Draft gate kommer ihåg status

### L. Retry Logic
- Testa retry-mekanismen
- Förväntat: Retry-steps i receipt

### M. Fail-Closed Behavior
- Testa fail-closed vid max_retries=0
- Förväntat: Korrekt hantering av failures

## Debugging

Om tester misslyckas:

1. **Kontrollera backend logs:**
```bash
# I backend-terminalen
# Titta efter felmeddelanden
```

2. **Testa endpoint manuellt:**
```bash
# Skapa event först
EVENT_ID=$(curl -s -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"input_type":"text","value":"Test text"}' | jq -r .event_id)

# Testa scrub_v2
curl -X POST http://localhost:8000/api/v1/privacy/scrub_v2 \
  -H "Content-Type: application/json" \
  -d "{\"event_id\":\"$EVENT_ID\",\"production_mode\":false,\"max_retries\":2}" | jq
```

3. **Kontrollera Ollama:**
```bash
# Ollama måste köra för semantic audit
curl http://localhost:11434/api/tags
```

## Förväntade Resultat

Alla tester ska passera med:
- ✅ Clean input → verification_passed=true
- ✅ PII → anonymiserad korrekt
- ✅ Semantic risk → approval_required=true
- ✅ Production Mode → hard stop vid risk
- ✅ Approval token → draft fungerar
- ✅ Receipt → korrekt struktur
- ✅ Status store → persistence fungerar

