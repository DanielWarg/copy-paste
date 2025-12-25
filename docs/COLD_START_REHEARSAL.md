# Cold Start Rehearsal – Operational Realism Test

**Syfte:** Verifiera att systemet fungerar under stress, trötthet och skarpt läge  
**Duration:** 2-3 timmar  
**Deltagare:** Tech Lead, Security Lead, Operations

---

## Förberedelser

### 1. Environment Setup

**Krävs:**
- Clean environment (inga services körs)
- Certifikat genererade (`./scripts/generate_certs.sh`)
- Secrets skapade (`secrets/fernet_key.txt`)
- Dokumentation tillgänglig (`docs/security-brutal.md`, `docs/SECURITY_SUMMIT_PHASE_B.md`)

**Kontrollera:**
- ✅ Inga tidigare containers körs
- ✅ Inga certifikat finns (eller ta bort gamla)
- ✅ Inga secrets finns (eller ta bort gamla)
- ✅ Alla scripts är körbara (`chmod +x scripts/*.sh`)

---

## Rehearsal Scenarios

### Scenario 1: Normal Startup (Baseline)

**Mål:** Verifiera att normal startup fungerar korrekt.

**Steg:**
1. Generera certifikat: `./scripts/generate_certs.sh`
2. Skapa secrets: `echo "test-fernet-key-32-bytes-long!!" > secrets/fernet_key.txt`
3. Starta services: `docker-compose -f docker-compose.prod_brutal.yml up -d`
4. Vänta 30 sekunder för startup
5. Verifiera: `make verify-brutal`

**Förväntat resultat:**
- ✅ Alla services startar utan fel
- ✅ Health endpoints svarar
- ✅ Static validation passerar
- ✅ Runtime validation passerar
- ✅ mTLS fungerar (403 utan cert, 200 med cert)
- ✅ Zero egress verifierat

**Dokumentera:**
- Startup time: _____ minuter
- Eventuella varningar eller fel: _____
- Noteringar: _____

---

### Scenario 2: Felaktigt Certifikat (mTLS Failure)

**Mål:** Verifiera att systemet korrekt blockerar felaktiga certifikat.

**Steg:**
1. Generera ett felaktigt certifikat (inte signerat av CA)
2. Försök använda felaktigt cert för att nå API: `curl -k --cert wrong.crt --key wrong.key https://localhost/api/v1/events`
3. Verifiera att request blockeras (403)

**Förväntat resultat:**
- ✅ Request utan cert → 403
- ✅ Request med felaktigt cert → 403
- ✅ Request med korrekt cert → 200

**Dokumentera:**
- Response code utan cert: _____
- Response code med felaktigt cert: _____
- Response code med korrekt cert: _____
- Noteringar: _____

---

### Scenario 3: Revokerat Certifikat (CRL Test)

**Mål:** Verifiera att revokerade certifikat blockeras korrekt.

**Steg:**
1. Generera certifikat för "test-user"
2. Använd certifikat för att nå API (verifiera att det fungerar)
3. Revokera certifikat (lägg till i CRL)
4. Uppdatera proxy config med ny CRL
5. Restart proxy: `docker-compose -f docker-compose.prod_brutal.yml restart proxy`
6. Försök använda revokerat cert igen

**Förväntat resultat:**
- ✅ Certifikat fungerar innan revokering
- ✅ Certifikat blockeras efter revokering (403)
- ✅ Revokering är omedelbar (efter proxy restart)

**Dokumentera:**
- Time to revoke: _____ minuter
- Time to enforcement: _____ minuter
- Noteringar: _____

---

### Scenario 4: PII i Input (Privacy Gate Test)

**Mål:** Verifiera att Privacy Gate blockerar PII korrekt.

**Steg:**
1. Skicka request med PII till Privacy Shield: `curl -X POST https://localhost/api/v1/privacy/mask -H "Content-Type: application/json" -d '{"text":"test@example.com","mode":"strict"}'`
2. Skicka request med PII till Draft endpoint: `curl -X POST https://localhost/api/v1/events/1/draft -H "Content-Type: application/json" -d '{"raw_text":"test@example.com","mode":"strict"}'`
3. Verifiera att Privacy Shield maskerar PII korrekt
4. Verifiera att Draft endpoint blockerar eller maskerar PII

**Förväntat resultat:**
- ✅ Privacy Shield maskerar PII (`test@example.com` → `[EMAIL]`)
- ✅ Draft endpoint accepterar maskerad text eller blockerar
- ✅ Inga raw PII skickas till externa AI:er

**Dokumentera:**
- Privacy Shield response: _____
- Draft endpoint response: _____
- Noteringar: _____

---

### Scenario 5: Backend Crash (Failure Recovery)

**Mål:** Verifiera att systemet hanterar backend crash korrekt.

**Steg:**
1. Simulera backend crash: `docker-compose -f docker-compose.prod_brutal.yml stop backend`
2. Verifiera att proxy returnerar korrekt error (502/503)
3. Starta backend igen: `docker-compose -f docker-compose.prod_brutal.yml start backend`
4. Verifiera att backend recovery fungerar
5. Verifiera att API fungerar igen

**Förväntat resultat:**
- ✅ Proxy returnerar 502/503 när backend är nere
- ✅ Backend recovery fungerar
- ✅ API fungerar igen efter recovery
- ✅ Inga data förloras (om DB används)

**Dokumentera:**
- Time to detect failure: _____ sekunder
- Time to recovery: _____ minuter
- Noteringar: _____

---

### Scenario 6: Proxy Restart (High Availability)

**Mål:** Verifiera att proxy restart inte påverkar backend.

**Steg:**
1. Verifiera att systemet fungerar (health check)
2. Restart proxy: `docker-compose -f docker-compose.prod_brutal.yml restart proxy`
3. Vänta 10 sekunder
4. Verifiera att systemet fortfarande fungerar

**Förväntat resultat:**
- ✅ Proxy restart påverkar inte backend
- ✅ Systemet fungerar igen efter proxy restart
- ✅ Inga förluster av pågående requests (om några)

**Dokumentera:**
- Proxy restart time: _____ sekunder
- Service disruption: _____ sekunder
- Noteringar: _____

---

### Scenario 7: Secret Missing (Boot Fail Test)

**Mål:** Verifiera att systemet startar inte utan secrets (fail-closed).

**Steg:**
1. Stoppa alla services
2. Ta bort secret: `rm secrets/fernet_key.txt`
3. Försök starta backend: `docker-compose -f docker-compose.prod_brutal.yml up -d backend`
4. Verifiera att backend crashar med error om saknad secret
5. Återskapa secret: `echo "test-fernet-key-32-bytes-long!!" > secrets/fernet_key.txt`
6. Starta backend igen
7. Verifiera att backend startar korrekt

**Förväntat resultat:**
- ✅ Backend crashar om secret saknas
- ✅ Error message är tydlig (beskriver vad som saknas)
- ✅ Backend startar korrekt när secret finns

**Dokumentera:**
- Error message: _____
- Time to detect failure: _____ sekunder
- Noteringar: _____

---

### Scenario 8: Cloud API Key Detection (Boot Fail Test)

**Mål:** Verifiera att systemet startar inte om cloud API keys finns i env (fail-closed).

**Steg:**
1. Stoppa alla services
2. Sätt cloud API key: `export OPENAI_API_KEY=test-key`
3. Försök starta backend: `docker-compose -f docker-compose.prod_brutal.yml up -d backend`
4. Verifiera att backend crashar med error om cloud API key finns
5. Ta bort cloud API key: `unset OPENAI_API_KEY`
6. Starta backend igen
7. Verifiera att backend startar korrekt

**Förväntat resultat:**
- ✅ Backend crashar om cloud API key finns i env
- ✅ Error message är tydlig (beskriver vad som är fel)
- ✅ Backend startar korrekt när cloud API key saknas

**Dokumentera:**
- Error message: _____
- Time to detect failure: _____ sekunder
- Noteringar: _____

---

### Scenario 9: Zero Egress Verification (Infrastructure Test)

**Mål:** Verifiera att backend verkligen inte kan nå internet.

**Steg:**
1. Verifiera att backend körs: `docker ps | grep backend`
2. Försök nå internet från backend: `docker exec copy-paste-backend-brutal curl -s https://www.google.com`
3. Verifiera att request failar (connection error)
4. Kör automated test: `docker exec copy-paste-backend-brutal bash scripts/verify_no_internet.sh`

**Förväntat resultat:**
- ✅ Backend kan inte nå internet (connection error)
- ✅ Automated test passerar (zero egress verified)

**Dokumentera:**
- Connection error type: _____
- Automated test result: _____
- Noteringar: _____

---

### Scenario 10: Incident Response (Break-Glass)

**Mål:** Verifiera att incident playbook fungerar i praktiken.

**Steg:**
1. Simulera kritiskt incident (backend crash, data breach, certifikatstöld)
2. Följ incident playbook exakt som dokumenterat
3. Verifiera att alla steg kan följas
4. Verifiera att break-glass-procedure fungerar (om applicerbart)

**Förväntat resultat:**
- ✅ Incident playbook kan följas steg-för-steg
- ✅ Alla steg är genomförbara
- ✅ Break-glass-procedure fungerar (om applicerbart)
- ✅ Incident dokumenteras korrekt

**Dokumentera:**
- Incident type: _____
- Time to resolution: _____ minuter
- Steg som var svåra att följa: _____
- Förbättringsförslag: _____
- Noteringar: _____

---

## Post-Rehearsal Review

### Success Criteria

**Alla scenarios måste:**
- ✅ Kunna genomföras enligt dokumentation
- ✅ Ge förväntade resultat
- ✅ Vara genomförbara under stress (timme 2-3 av rehearsal)

**Dokumentation måste:**
- ✅ Vara begriplig under stress
- ✅ Innehålla alla nödvändiga steg
- ✅ Ge tydliga förväntade resultat

**Process måste:**
- ✅ Vara genomförbar av operations team
- ✅ Inte kräva teknisk expertis bortom dokumentation
- ✅ Vara robust mot mänskligt fel

---

### Identified Issues

**Dokumentera:**
- Issues hittade under rehearsal: _____
- Steg som var otydliga: _____
- Förbättringsförslag: _____
- Missing documentation: _____

---

### Sign-off

**Tech Lead:**
- ✅ Alla scenarios testade
- ✅ Alla issues dokumenterade
- ✅ Systemet är operativt redo

**Security Lead:**
- ✅ Security guarantees verifierade
- ✅ Incident response fungerar
- ✅ Systemet är säkert för produktion

**Operations:**
- ✅ Procedures är genomförbara
- ✅ Documentation är begriplig
- ✅ Systemet kan hanteras operativt

---

## Lessons Learned

**Vad fungerade bra:**
- _____

**Vad behöver förbättras:**
- _____

**Vad saknas:**
- _____

---

**Status:** Cold Start Rehearsal Complete

